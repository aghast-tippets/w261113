"""
Live proof: can files move between Claude's side and YOUR Microsoft 365 Copilot, both ways?

This script plays Claude's role exactly as Claude Code does (it starts server.py as an MCP server
over stdio and calls its tools), so it needs no Claude credit. Every step uses random values that
Copilot cannot guess, so a PASS means the content really travelled.

  .venv/Scripts/python.exe live_proof.py              # real Copilot: an Edge window opens
  .venv/Scripts/python.exe live_proof.py --rehearse   # dry run against the local fake Copilot

It only uploads small synthetic files it generates itself (no organisational data), in a new
Copilot chat. Don't run it while Claude Code or copilot.sh is using the bridge (shared profile).
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import io
import json
import os
import random
import re
import secrets
import string
import sys
import tempfile
import zipfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import transfer

HERE = Path(__file__).resolve().parent

# Prompts are single-line on purpose: a newline typed into Copilot's box can send early.
PROMPT_TEXT_FILE = "I have attached a text file. Reply with only the code word written in it, nothing else."
PROMPT_IMAGE = "I have attached an image. What number is shown in it? Reply with only the digits."
PROMPT_CODE = ("Reply with exactly one fenced code block (language text) that contains exactly three lines: "
               "the first line is `{a}`, the second line is `{b}`, the third line is `{c}`. "
               "Write nothing outside the code block.")
PROMPT_CSV = ("I have attached a CSV file with columns a and b. Reply with one fenced code block (language csv) "
              "containing the same rows with a third column sum = a + b, keeping the header row (a,b,sum) and "
              "the original row order. Write nothing outside the code block.")
PROMPT_MAKE_IMAGE = "Create an image: a simple red circle on a white background."
PROMPT_MAKE_FILE = ("Create a downloadable text file named {name} whose entire content is the single line: {secret}. "
                    "Give me the file to download.")


@dataclass
class Step:
    id: str
    title: str
    direction: str
    optional: bool = False
    status: str = "NOT RUN"  # PASS / PARTIAL / FAIL / ERROR / SKIPPED
    detail: str = ""
    evidence: dict = field(default_factory=dict)


# ---------------------------------------------------------------- verification (pure)
def word_present(response: str, word: str) -> bool:
    return word.lower() in (response or "").lower()


def digits_present(response: str, code: str) -> bool:
    return code in re.sub(r"\D", "", response or "")


def compare_lines(text: str, expected: list[str]) -> str:
    """'exact', 'partial' (all values present, extra/odd formatting) or 'missing'."""
    lines = [ln.rstrip() for ln in text.strip("\r\n").splitlines()]
    if lines == expected:
        return "exact"
    return "partial" if all(e in text for e in expected) else "missing"


def check_csv_sum(text: str, rows: list[tuple[int, int]]) -> tuple[bool, str]:
    parsed = [r for r in csv.reader(io.StringIO(text.strip())) if r]
    if not parsed or [h.strip().lower() for h in parsed[0]] != ["a", "b", "sum"]:
        return False, f"header was {parsed[0] if parsed else None}"
    body = parsed[1:]
    if len(body) != len(rows):
        return False, f"{len(body)} data rows, expected {len(rows)}"
    for got, (a, b) in zip(body, rows):
        try:
            values = [int(float(v)) for v in got]
        except ValueError:
            return False, f"non-numeric row {got}"
        if values != [a, b, a + b]:
            return False, f"row {got} should be {[a, b, a + b]}"
    return True, "all sums correct"


def file_contains(path: Path, needle: str) -> bool:
    data = path.read_bytes()
    if data[:4] == b"PK\x03\x04":  # docx/xlsx/pptx: search the XML inside
        try:
            with zipfile.ZipFile(path) as z:
                return any(needle.encode() in z.read(n) for n in z.namelist() if n.endswith(".xml"))
        except zipfile.BadZipFile:
            return False
    return needle.encode() in data


# ---------------------------------------------------------------- MCP client
class Bridge:
    def __init__(self, session: ClientSession):
        self.session = session

    async def call(self, tool: str, **args):
        res = await self.session.call_tool(tool, args)
        texts = [c.text for c in res.content if c.type == "text"]
        raw = texts[0] if texts else ""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = raw
        if res.isError:
            raise RuntimeError(str(data))
        return data

    async def send(self, prompt: str, files: list[Path] | None = None, timeout: int = 180) -> dict:
        r = await self.call("copilot_send", prompt=prompt, timeout_seconds=timeout,
                            **({"files": [str(f) for f in files]} if files else {}))
        if not r.get("complete"):
            r = {**r, **await self.call("copilot_wait", timeout_seconds=timeout)}
        if not r.get("complete"):
            raise RuntimeError(f"No complete reply ({r.get('reason')}): {r.get('error')}")
        return r

    async def collect_until(self, predicate, attempts: int, delay: float) -> dict:
        manifest = await self.call("copilot_collect", inline_images=False)
        for _ in range(attempts - 1):
            if predicate(manifest):
                break
            await asyncio.sleep(delay)
            manifest = await self.call("copilot_collect", inline_images=False)
        return manifest


# ---------------------------------------------------------------- the proof
def nonce_word() -> str:
    return random.choice(["KESTREL", "MARMOT", "OSPREY", "BADGER", "HERON"]) + "-" + "".join(
        secrets.choice(string.digits) for _ in range(5))


async def run(bridge: Bridge, outbox: Path, steps: list[Step], args) -> None:
    by_id = {s.id: s for s in steps}

    async def attempt(step: Step, coro):
        if step.status == "SKIPPED":
            return
        print(f"\n[{step.id}] {step.title} ...", flush=True)
        try:
            await coro
        except Exception as exc:  # report and keep going: each step stands alone
            step.status, step.detail = "ERROR", str(exc)[:500]
        print(f"[{step.id}] {step.status}: {step.detail}", flush=True)

    # P1: Claude -> Copilot, text file
    async def p1():
        s = by_id["P1"]
        word = nonce_word()
        f = outbox / "transfer-test.txt"
        f.write_text(f"Transfer test file.\nCODE WORD: {word}\nNothing else in this file matters.\n", encoding="utf-8")
        r = await bridge.send(PROMPT_TEXT_FILE, [f])
        s.evidence = {"file": str(f), "sha256": transfer.sha256(f.read_bytes()), "expected": word,
                      "reply": r["response"][:300], "attached": r.get("attached")}
        ok = word_present(r["response"], word)
        s.status, s.detail = ("PASS", f"Copilot read the code word {word} from the file") if ok else \
            ("FAIL", "Copilot's reply does not contain the code word")

    # P2: Claude -> Copilot, image
    async def p2():
        s = by_id["P2"]
        code = "".join(secrets.choice("23456789") for _ in range(6))
        f = outbox / "transfer-test.png"
        f.write_bytes(transfer.digits_png(code))
        r = await bridge.send(PROMPT_IMAGE, [f])
        s.evidence = {"file": str(f), "expected": code, "reply": r["response"][:300]}
        ok = digits_present(r["response"], code)
        s.status, s.detail = ("PASS", f"Copilot read {code} from the image") if ok else \
            ("FAIL", "Copilot's reply does not contain the number in the image")

    # P3: Copilot -> Claude, code block saved as a file
    async def p3():
        s = by_id["P3"]
        expected = [f"alpha {nonce_word()}", f"bravo {nonce_word()}", f"charlie {nonce_word()}"]
        await bridge.send(PROMPT_CODE.format(a=expected[0], b=expected[1], c=expected[2]))
        manifest = await bridge.call("copilot_collect", images=False, files=False, inline_images=False)
        blocks = manifest.get("code_blocks", [])
        s.evidence = {"expected": expected, "code_blocks": blocks}
        if not blocks:
            s.status, s.detail = "FAIL", "no code block found in the reply (check the reply in the browser)"
            return
        text = Path(blocks[0]["path"]).read_text(encoding="utf-8")
        verdict = compare_lines(text, expected)
        s.status, s.detail = {
            "exact": ("PASS", f"saved {blocks[0]['path']} with exactly the requested content"),
            "partial": ("PARTIAL", "file received with the right values but extra or different formatting"),
            "missing": ("FAIL", "the saved code block does not contain the requested values"),
        }[verdict]

    # P4: round trip: CSV to Copilot, computed CSV back
    async def p4():
        s = by_id["P4"]
        rows = [(random.randint(-50, 200), random.randint(-50, 200)) for _ in range(5)]
        f = outbox / "transfer-test.csv"
        f.write_text("a,b\n" + "".join(f"{a},{b}\n" for a, b in rows), encoding="utf-8")
        await bridge.send(PROMPT_CSV, [f])
        manifest = await bridge.call("copilot_collect", images=False, files=False, inline_images=False)
        blocks = manifest.get("code_blocks", [])
        s.evidence = {"sent": str(f), "rows": rows, "code_blocks": blocks}
        if not blocks:
            s.status, s.detail = "FAIL", "no CSV code block in the reply"
            return
        ok, why = check_csv_sum(Path(blocks[0]["path"]).read_text(encoding="utf-8"), rows)
        s.status, s.detail = ("PASS", f"Copilot read the CSV and returned correct sums ({blocks[0]['path']})") if ok \
            else ("FAIL", why)

    # P5: Copilot -> Claude, generated image (optional: needs image generation in your tenant)
    async def p5():
        s = by_id["P5"]
        r = await bridge.send(PROMPT_MAKE_IMAGE, timeout=args.generation_timeout)
        manifest = await bridge.collect_until(lambda m: m.get("images"), attempts=4, delay=15)
        images = [i for i in manifest.get("images", []) if i["width"] >= 64 and i["height"] >= 64]
        s.evidence = {"reply": r["response"][:300], "images": images, "problems": manifest.get("problems")}
        if images:
            s.status, s.detail = "PASS", f"saved {images[0]['path']} ({images[0]['width']}x{images[0]['height']}, via {images[0]['method']})"
        else:
            s.status, s.detail = "FAIL", "no image in the reply (image generation may be unavailable in your tenant)"

    # P6: Copilot -> Claude, generated downloadable file (optional)
    async def p6():
        s = by_id["P6"]
        secret, name = nonce_word(), f"proof-{secrets.token_hex(3)}.txt"
        r = await bridge.send(PROMPT_MAKE_FILE.format(name=name, secret=secret), timeout=args.generation_timeout)
        manifest = await bridge.collect_until(lambda m: m.get("files"), attempts=3, delay=15)
        hits = [f for f in manifest.get("files", []) if file_contains(Path(f["path"]), secret)]
        s.evidence = {"expected": secret, "reply": r["response"][:300], "files": manifest.get("files"),
                      "links": manifest.get("links"), "problems": manifest.get("problems")}
        if hits:
            s.status, s.detail = "PASS", f"downloaded {hits[0]['path']} containing {secret} (via {hits[0]['method']})"
        elif manifest.get("files"):
            s.status, s.detail = "PARTIAL", "a file arrived but does not contain the requested line"
        elif manifest.get("links") or manifest.get("problems"):
            s.status, s.detail = "PARTIAL", "Copilot offered a link or viewer, not a downloadable file (see evidence)"
        elif word_present(r["response"], secret):
            s.status, s.detail = "PARTIAL", "Copilot wrote the content as text but offered no file"
        else:
            s.status, s.detail = "FAIL", "no file, link or content came back"

    for step, fn in (("P1", p1), ("P2", p2), ("P3", p3), ("P4", p4), ("P5", p5), ("P6", p6)):
        await attempt(by_id[step], fn())


async def wait_for_sign_in(bridge: Bridge, rehearse: bool) -> dict:
    for attempt_no in range(4):
        status = await bridge.call("copilot_status")
        ready = (status["selector_matches"].get("composer", 0) and not status["looks_like_sign_in"])
        if ready or rehearse:
            return status
        print(f"\nCopilot isn't ready (page: {status['url']}). Sign in in the Edge window and open Copilot Chat.")
        await asyncio.to_thread(input, "Press Enter when Copilot Chat is showing... ")
    raise RuntimeError("Copilot chat box not found. Check the 'composer' selector with copilot.sh /inspect.")


def print_report(steps: list[Step], report_path: Path) -> None:
    print("\n" + "=" * 78)
    print(f"{'Step':5} {'Direction':22} {'Result':8} Detail")
    print("-" * 78)
    for s in steps:
        print(f"{s.id:5} {s.direction:22} {s.status:8} {s.title}" + (" (optional)" if s.optional else ""))
        if s.detail:
            print(f"{'':37}{s.detail[:120]}")
    print("=" * 78)
    print(f"Full report with evidence: {report_path}")


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rehearse", action="store_true", help="run against the local fake Copilot (headless)")
    ap.add_argument("--skip-image-generation", action="store_true", help="skip P5")
    ap.add_argument("--skip-file-generation", action="store_true", help="skip P6")
    ap.add_argument("--generation-timeout", type=int, default=300, help="seconds to wait in P5/P6")
    args = ap.parse_args()

    env = dict(os.environ)
    site = None
    if args.rehearse:
        sys.path.insert(0, str(HERE / "tests"))
        import fake_site
        site, base = fake_site.start()
        state = Path(tempfile.mkdtemp(prefix="copilot-proof-"))
        env.update(COPILOT_HOME_URL=base + "/", COPILOT_HEADLESS="1", COPILOT_BRIDGE_DIR=str(state),
                   COPILOT_SELECTORS=str(HERE / "tests" / "fake_copilot" / "selectors.json"),
                   COPILOT_STABLE_SECONDS="1", COPILOT_UPLOAD_TIMEOUT="15")
        env.pop("COPILOT_INBOX_DIR", None)
        exchange = state / "exchange"
    else:
        exchange = transfer.EXCHANGE_DIR
    run_dir = exchange / "outbox" / f"proof-{datetime.now():%Y%m%d-%H%M%S}"
    run_dir.mkdir(parents=True, exist_ok=True)

    steps = [
        Step("P1", "Text file uploaded and read by Copilot", "Claude -> Copilot"),
        Step("P2", "Image uploaded and read by Copilot", "Claude -> Copilot"),
        Step("P3", "Code block returned and saved as a file", "Copilot -> Claude"),
        Step("P4", "CSV sent, computed CSV returned", "round trip"),
        Step("P5", "Generated image downloaded", "Copilot -> Claude", optional=True),
        Step("P6", "Generated file downloaded", "Copilot -> Claude", optional=True),
    ]
    if args.skip_image_generation:
        steps[4].status = "SKIPPED"
    if args.skip_file_generation:
        steps[5].status = "SKIPPED"

    params = StdioServerParameters(command=sys.executable, args=[str(HERE / "server.py")], env=env, cwd=str(HERE))
    started = datetime.now()
    with open(run_dir / "server.log", "w", encoding="utf-8") as errlog:
        async with stdio_client(params, errlog=errlog) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            bridge = Bridge(session)
            status = await wait_for_sign_in(bridge, args.rehearse)
            await bridge.call("copilot_new_chat")
            await run(bridge, run_dir, steps, args)
    if site is not None:
        site.shutdown()

    report = {"mode": "rehearsal (fake Copilot)" if args.rehearse else "live Microsoft 365 Copilot",
              "started": started.isoformat(timespec="seconds"), "finished": datetime.now().isoformat(timespec="seconds"),
              "copilot_url": status.get("url"), "steps": [asdict(s) for s in steps]}
    report_path = run_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print_report(steps, report_path)
    core_ok = all(s.status == "PASS" for s in steps if not s.optional)
    print("\nCore transfer (P1-P4): " + ("PROVEN" if core_ok else "NOT PROVEN - see details above"))
    return 0 if core_ok else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
