"""
Terminal chat with Microsoft 365 Copilot through the copilot-web browser bridge.
No Claude Code (and no Claude credit) needed: you type, Copilot answers here.

  .venv/Scripts/python.exe chat.py [conversation-url]

Commands: /open <url>  /new  /read  /url  /attach <file>...  /detach  /collect
          /inspect  /reload  /quit
Uses the same profile, selectors.json and environment variables as server.py.
"""
from __future__ import annotations

import asyncio
import os
import shlex
import sys
import time

import transfer
from server import GIVE_UP_SECONDS, HOME_URL, bridge, check_url

# How often to print a progress line while waiting (a finished reply is shown as soon as it
# settles, regardless of this). The give-up time (COPILOT_GIVE_UP_SECONDS, 0 = never) is
# shared with the MCP server.
STATUS_SECONDS = max(1.0, float(os.environ.get("COPILOT_STATUS_SECONDS", "20")))

HELP = ("Commands: /open <url>  /new  /read  /url  /attach <file>...  /detach  /collect  /inspect  "
        "/reload  /quit   (anything else is sent to Copilot)")

staged: list = []  # files to attach to the next message


async def ask(prompt: str) -> None:
    page = await bridge.ensure()
    composer = await bridge.composer(page)
    if composer is None:
        print("! No chat box found. Sign in in the Edge window, or fix 'composer' in selectors.json.")
        return
    if staged:
        print(f"… attaching {len(staged)} file(s)", flush=True)
        info = await bridge.attach(page, list(staged))
        print(f"… attached via {info['method']}" + ("" if info["confirmed"] else " (upload not confirmed by the page)"))
        staged.clear()
    await bridge.begin_pending(page)
    await bridge.type_prompt(page, composer, prompt)
    await bridge.click_send(page, composer)
    print("… waiting for Copilot (Ctrl+C to give up)", flush=True)
    try:
        started = time.monotonic()
        while True:
            result = await bridge.wait_for_reply(page, STATUS_SECONDS)
            if result["complete"]:
                print(f"\nCopilot:\n{result['response']}\n", flush=True)
                found = await bridge.reply_artifacts(page)
                extras = {k: v for k, v in found.items() if v}
                if extras:
                    print(f"(this reply contains {extras}; /collect saves them)\n")
                return
            matched = len(await bridge.signatures(page))
            stop = await bridge.stop_visible(page)
            if result["response"] is None:
                print(f"… no new reply detected: 'assistant_message' matches {matched} element(s) "
                      f"(was {bridge.pending['before_count']}).", flush=True)
                if GIVE_UP_SECONDS and time.monotonic() - started >= GIVE_UP_SECONDS and not stop:
                    bridge.pending = None
                    print(f"\nGave up after {GIVE_UP_SECONDS:g}s. If Copilot has answered in the Edge window, the "
                          "'assistant_message' selector doesn't match your Copilot page. "
                          "Run /inspect to find the right one.\n", flush=True)
                    return
            elif stop:
                print("… reply is arriving but the 'stop_button' selector still matches a visible "
                      "button. If Copilot has finished, that selector is wrong (see /inspect).", flush=True)
            else:
                print("… reply still changing, waiting for it to settle", flush=True)
    except (KeyboardInterrupt, asyncio.CancelledError):
        task = asyncio.current_task()
        if task is not None and hasattr(task, "uncancel"):
            task.uncancel()  # Ctrl+C cancels the main task; resume the chat loop instead
        bridge.pending = None
        print("\n(stopped waiting; /read shows whatever the selector currently finds)")


async def collect(page) -> None:
    manifest, _ = await bridge.collect(page, -1, images=True, files=True, code_blocks=True, inline_images=False)
    saved = [*manifest["images"], *manifest["files"], *manifest["code_blocks"]]
    if saved:
        print(f"\nSaved to {manifest['saved_to']}:")
        for item in saved:
            print(f"  {item['path']}  ({item.get('bytes', item.get('chars'))} bytes/chars, {item.get('method', 'code')})")
    for link in manifest["links"]:
        print(f"  link: {link['text'][:50]!r} -> {link['href']}")
    for problem in manifest["problems"]:
        print(f"  ! {problem['item']}: {problem['error']}")
    if not (saved or manifest["links"] or manifest["problems"]):
        print("Nothing to collect in the latest reply.")
    print()


async def inspect(page) -> None:
    """Print what selectors.json matches and the page's likely message containers."""
    from server import INSPECT_JS

    root = bridge.root(page)
    print("\nCurrent selector matches:")
    for name, sel in bridge.sel.items():
        if name == "frame" or not sel:
            continue
        for k, s in enumerate(sel if isinstance(sel, list) else [sel]):
            label = f"{name}[{k}]" if isinstance(sel, list) else name
            print(f"  {label:18} {await root.locator(s).count():3}  {s}")
    print(f"  latest reply contains: {await bridge.reply_artifacts(page)}")
    keywords = ("stop", "send", "attach", "upload", "add", "download", "file", "plus", "menuitem")
    for frame in page.frames:
        try:
            info = await frame.evaluate(INSPECT_JS)
        except Exception:
            continue
        cands = info.get("message_candidates") or []
        inputs = [i for i in info.get("inputs", []) if i.get("visible")]
        if frame != page.main_frame and not (cands or inputs or info.get("file_inputs")):
            continue
        where = "  (main page)" if frame == page.main_frame else '  (IFRAME: set "frame" in selectors.json)'
        print(f"\nFrame: {frame.url[:100]}{where}")
        for i in inputs[:5]:
            print("  input  ", {k: v for k, v in i.items() if v not in (None, True)})
        for f in info.get("file_inputs", [])[:5]:
            print("  file   ", {k: v for k, v in f.items() if v not in (None, False)})
        buttons = [b for b in info.get("buttons", []) if any(w in str(b).lower() for w in keywords)]
        for b in buttons[:12]:
            print("  button ", {k: v for k, v in b.items() if v not in (None, False)})
        print("  likely reply/attachment containers (selector, count, start of text):")
        for c in cands[:25]:
            sample = c["sample"].replace("\n", " ")[:70]
            print(f"    {c['count']:3}  {c['selector']:55} {sample}")
    print("\nPick the selector whose count equals the number of Copilot answers on screen and whose text "
          "is Copilot's answer (not your question). Put it first under \"assistant_message\" in "
          "selectors.json, then run /reload.\n")


async def main() -> None:
    page = await bridge.ensure()
    if len(sys.argv) > 1:
        check_url(sys.argv[1])
        await page.goto(sys.argv[1], wait_until="domcontentloaded")
    print(f"Connected: {page.url}\nSign in in the Edge window if asked.\n{HELP}\n")
    while True:
        try:
            line = (await asyncio.to_thread(input, "You> ")).strip()
        except EOFError:
            break
        if not line:
            continue
        try:
            if line in ("/quit", "/exit"):
                break
            elif line == "/new":
                await page.goto(HOME_URL, wait_until="domcontentloaded")
                bridge.pending = None
            elif line.startswith("/open "):
                url = line.split(maxsplit=1)[1]
                check_url(url)
                await page.goto(url, wait_until="domcontentloaded")
                bridge.pending = None
            elif line == "/read":
                msgs = await bridge.assistant_texts(page)
                print(f"\nCopilot:\n{msgs[-1] if msgs else '(no replies found)'}\n")
            elif line == "/url":
                print(page.url)
            elif line == "/attach" or line.startswith("/attach "):
                args = [a.strip('"').strip("'") for a in shlex.split(line[len("/attach"):], posix=False)]
                if args:
                    # You chose these files yourself, so any folder is allowed (secrets still refused).
                    staged.extend(transfer.validate_uploads(args, enforce_roots=False))
                print("Attached to your next message:", [p.name for p in staged] or "nothing")
            elif line == "/detach":
                staged.clear()
                print("Attachments cleared.")
            elif line == "/collect":
                await collect(page)
            elif line == "/inspect":
                await inspect(page)
            elif line == "/reload":
                from server import load_selectors
                bridge.sel = load_selectors()
                print("selectors.json reloaded")
            elif line.startswith("/"):
                print(HELP)
            else:
                await ask(line)
            page = await bridge.ensure()
        except Exception as exc:  # keep the session alive on page/selector errors
            bridge.pending = None
            print(f"! {exc}")
    if bridge.ctx is not None:
        if bridge.page is not None and not bridge.page.is_closed():
            bridge.remember_url(bridge.page)
        await bridge.ctx.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
