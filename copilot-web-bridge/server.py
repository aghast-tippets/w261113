"""
copilot-web: an MCP server that lets Claude Code drive the Microsoft 365 Copilot
web UI through a persistent, dedicated browser profile (Playwright).

This is UI automation, not a supported Microsoft API. Selectors live in
selectors.json and will almost certainly need calibrating for your tenant
(use the copilot_inspect tool).

Everything diagnostic goes to stderr: stdout is the MCP stdio channel.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from mcp.server.fastmcp import FastMCP
from playwright.async_api import BrowserContext, Page, async_playwright
from playwright.async_api import Error as PlaywrightError


def log(*args: object) -> None:
    print("[copilot-web]", *args, file=sys.stderr, flush=True)


def env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# --------------------------------------------------------------------------
# Configuration (all overridable with environment variables)
# --------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
STATE_DIR = Path(os.environ.get("COPILOT_BRIDGE_DIR") or Path.home() / ".copilot-web-bridge")
PROFILE_DIR = STATE_DIR / "profile"
STATE_FILE = STATE_DIR / "state.json"
SELECTORS_FILE = Path(os.environ.get("COPILOT_SELECTORS") or HERE / "selectors.json")

HOME_URL = os.environ.get("COPILOT_HOME_URL", "https://m365.cloud.microsoft/chat")
# "msedge" (default: always present on Windows, plays best with Entra/Conditional
# Access), "chrome", or "chromium" (Playwright's bundled build; needs
# `python -m playwright install chromium`).
BROWSER_CHANNEL = os.environ.get("COPILOT_BROWSER_CHANNEL", "msedge").strip()
BROWSER_EXECUTABLE = os.environ.get("COPILOT_BROWSER_EXECUTABLE", "").strip()
HEADLESS = env_bool("COPILOT_HEADLESS", False)
ALLOWED_HOSTS = {
    h.strip().lower()
    for h in os.environ.get(
        "COPILOT_ALLOWED_HOSTS",
        "m365.cloud.microsoft,copilot.cloud.microsoft,www.microsoft365.com,microsoft365.com",
    ).split(",")
    if h.strip()
}
# Hard cap on prompts sent per server process (0 = unlimited). Guards against
# runaway Claude <-> Copilot loops. Restart the server (/mcp) to reset.
MAX_SENDS = int(os.environ.get("COPILOT_MAX_SENDS", "25"))
# Seconds the reply text must stay unchanged (with no stop button) to count as done.
STABLE_SECONDS = float(os.environ.get("COPILOT_STABLE_SECONDS", "4"))

DEFAULT_SELECTORS: dict[str, list[str]] = {
    "frame": [],
    "composer": ['[contenteditable="true"][role="textbox"]', "textarea"],
    "send_button": ['button[aria-label="Send"]'],
    "stop_button": ['button[aria-label*="Stop"]'],
    "assistant_message": ['[data-message-author-role="assistant"]'],
}


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def load_selectors() -> dict[str, str]:
    merged = {k: list(v) for k, v in DEFAULT_SELECTORS.items()}
    if SELECTORS_FILE.exists():
        data = json.loads(SELECTORS_FILE.read_text(encoding="utf-8"))
        for key, value in data.items():
            if key.startswith("_"):
                continue
            merged[key] = [value] if isinstance(value, str) else list(value)
    return {k: ", ".join(v) for k, v in merged.items()}


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.replace(tmp, STATE_FILE)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def check_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() not in ALLOWED_HOSTS:
        raise ValueError(
            f"Refusing to open {url!r}: only https URLs on {sorted(ALLOWED_HOSTS)} are allowed "
            "(set COPILOT_ALLOWED_HOSTS to change this)."
        )


INSPECT_JS = r"""
() => {
  const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const cls = e => typeof e.className === 'string' ? e.className.trim().split(/\s+/).slice(0, 4).join(' ') : undefined;
  const attr = (e, n) => e.getAttribute(n) || undefined;
  const inputs = [...document.querySelectorAll('textarea, input[type=text], [contenteditable="true"], [role="textbox"]')]
    .map(e => ({ tag: e.tagName.toLowerCase(), id: e.id || undefined, testid: attr(e, 'data-testid'),
                 role: attr(e, 'role'), aria: attr(e, 'aria-label'),
                 placeholder: attr(e, 'placeholder') || attr(e, 'data-placeholder'),
                 contenteditable: attr(e, 'contenteditable'), cls: cls(e), visible: vis(e) }));
  const buttons = [...document.querySelectorAll('button, [role=button]')].filter(vis)
    .map(e => ({ aria: attr(e, 'aria-label'), title: attr(e, 'title'), testid: attr(e, 'data-testid'),
                 text: (e.innerText || '').trim().slice(0, 40) || undefined,
                 disabled: e.disabled || e.getAttribute('aria-disabled') === 'true' }))
    .filter(b => b.aria || b.title || b.testid || b.text);
  const testids = {};
  for (const e of document.querySelectorAll('[data-testid]')) {
    const t = e.getAttribute('data-testid'); testids[t] = (testids[t] || 0) + 1; }
  const msg = {};
  const re = /message|reply|response|turn|author|bot|assistant|copilot|chat|answer/i;
  for (const e of document.querySelectorAll('*')) {
    for (const a of e.attributes) {
      if (!(a.name.startsWith('data-') || a.name === 'role' || a.name === 'aria-roledescription')) continue;
      if (a.value.length > 60 || !re.test(a.name + '=' + a.value)) continue;
      const key = `[${a.name}="${a.value}"]`;
      const slot = (msg[key] ||= { count: 0, sample: '' });
      slot.count++;
      const t = (e.innerText || '').trim();
      if (t.length > slot.sample.length) slot.sample = t.slice(0, 160);
    }
  }
  const message_candidates = Object.entries(msg)
    .filter(([, v]) => v.sample.length > 0)
    .sort((a, b) => b[1].sample.length - a[1].sample.length).slice(0, 60)
    .map(([selector, v]) => ({ selector, ...v }));
  return { inputs: inputs.slice(0, 30), buttons: buttons.slice(0, 80), testids, message_candidates };
}
"""


# --------------------------------------------------------------------------
# Browser bridge
# --------------------------------------------------------------------------
class Bridge:
    def __init__(self) -> None:
        self.pw = None
        self.ctx: BrowserContext | None = None
        self.page: Page | None = None
        self.lock = asyncio.Lock()
        self.sel = load_selectors()
        self.state = load_state()
        self.sends = 0
        # Baseline captured at send time, so copilot_wait can resume without resending.
        self.pending: dict | None = None

    # -- lifecycle ---------------------------------------------------------
    def _on_close(self, *_: object) -> None:
        log("browser context closed")
        self.ctx = None
        self.page = None

    async def ensure(self) -> Page:
        if self.page is not None and not self.page.is_closed() and self.ctx is not None:
            return self.page
        if self.ctx is None:
            if self.pw is None:
                self.pw = await async_playwright().start()
            PROFILE_DIR.mkdir(parents=True, exist_ok=True)
            kwargs: dict = {
                "user_data_dir": str(PROFILE_DIR),
                "headless": HEADLESS,
                "viewport": {"width": 1400, "height": 950},
            }
            if BROWSER_EXECUTABLE:
                kwargs["executable_path"] = BROWSER_EXECUTABLE
            elif BROWSER_CHANNEL and BROWSER_CHANNEL != "chromium":
                kwargs["channel"] = BROWSER_CHANNEL
            log("launching browser", {k: v for k, v in kwargs.items() if k != "viewport"})
            try:
                self.ctx = await self.pw.chromium.launch_persistent_context(**kwargs)
            except PlaywrightError as exc:
                raise RuntimeError(
                    f"Could not launch the browser ({exc.message.splitlines()[0]}). "
                    "Is another copilot-web server (another Claude Code session) already using "
                    f"the profile at {PROFILE_DIR}? Close it, or set COPILOT_BRIDGE_DIR to a "
                    "different directory for this session."
                ) from exc
            self.ctx.on("close", self._on_close)
        pages = [p for p in self.ctx.pages if not p.is_closed()]
        self.page = pages[0] if pages else await self.ctx.new_page()
        if self.page.url in ("", "about:blank"):
            await self.page.goto(self.state.get("last_url") or HOME_URL, wait_until="domcontentloaded")
        return self.page

    def root(self, page: Page):
        """Locator root: the page itself, or an iframe if selectors.json sets 'frame'."""
        frame = self.sel.get("frame")
        return page.frame_locator(frame) if frame else page

    def remember_url(self, page: Page) -> None:
        self.state["last_url"] = page.url
        save_state(self.state)

    # -- DOM access --------------------------------------------------------
    async def assistant_texts(self, page: Page) -> list[str]:
        texts = await self.root(page).locator(self.sel["assistant_message"]).all_inner_texts()
        return [t.strip() for t in texts if t.strip()]

    async def stop_visible(self, page: Page) -> bool:
        if not self.sel.get("stop_button"):
            return False
        loc = self.root(page).locator(self.sel["stop_button"])
        for i in range(await loc.count()):
            if await loc.nth(i).is_visible():
                return True
        return False

    async def composer(self, page: Page):
        loc = self.root(page).locator(self.sel["composer"])
        for i in range(await loc.count()):
            cand = loc.nth(i)
            if await cand.is_visible() and await cand.is_editable():
                return cand
        return None

    async def type_prompt(self, page: Page, composer, prompt: str) -> None:
        tag = await composer.evaluate("e => e.tagName")
        if tag in ("TEXTAREA", "INPUT"):
            await composer.fill(prompt)
            return
        # Rich editors (Lexical/Fluent) often ignore fill(); emulate a user instead.
        await composer.click()
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Delete")
        await page.keyboard.insert_text(prompt)
        typed = (await composer.inner_text()).strip()
        probe = prompt.strip()[:20]
        if probe and probe not in typed:
            await composer.fill(prompt)

    async def click_send(self, composer) -> str:
        page = self.page
        assert page is not None
        loc = self.root(page).locator(self.sel["send_button"]) if self.sel.get("send_button") else None
        if loc is not None:
            for i in range(await loc.count()):
                btn = loc.nth(i)
                if await btn.is_visible() and await btn.is_enabled():
                    await btn.click()
                    return "send_button"
        await composer.press("Enter")
        return "enter_key"

    async def wait_for_reply(self, page: Page, timeout_seconds: float) -> dict:
        assert self.pending is not None
        before_count = self.pending["before_count"]
        before_last = self.pending["before_last"]
        deadline = time.monotonic() + timeout_seconds
        last_text: str | None = None
        stable_since: float | None = None
        while time.monotonic() < deadline:
            await asyncio.sleep(1)
            if page.is_closed():
                raise RuntimeError("The Copilot browser window was closed while waiting for a reply.")
            msgs = await self.assistant_texts(page)
            is_new = len(msgs) > before_count or (bool(msgs) and msgs[-1] != before_last)
            if not is_new:
                continue
            latest = msgs[-1]
            if latest != last_text:
                last_text, stable_since = latest, time.monotonic()
                continue
            if (
                stable_since is not None
                and time.monotonic() - stable_since >= STABLE_SECONDS
                and not await self.stop_visible(page)
            ):
                self.pending = None
                self.state.setdefault("seen", {})[page.url] = digest(latest)
                self.remember_url(page)
                return {"url": page.url, "response": latest, "complete": True}
        return {
            "url": page.url,
            "response": last_text,
            "complete": False,
            "error": (
                "Timed out before the reply looked finished. Do NOT resend the prompt; "
                "call copilot_wait to keep waiting, or copilot_read to see what is there."
            ),
        }


bridge = Bridge()
mcp = FastMCP("copilot-web")


# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------
@mcp.tool()
async def copilot_status() -> dict:
    """Open the browser if needed and report the current Copilot page, sign-in state hints,
    and how many elements each configured selector matches. Call this first; if the page is a
    Microsoft sign-in page, ask the user to finish signing in in the browser window."""
    async with bridge.lock:
        page = await bridge.ensure()
        root = bridge.root(page)
        counts = {}
        for name, selector in bridge.sel.items():
            if name == "frame" or not selector:
                continue
            try:
                counts[name] = await root.locator(selector).count()
            except PlaywrightError as exc:
                counts[name] = f"error: {exc.message.splitlines()[0]}"
        host = (urlparse(page.url).hostname or "").lower()
        return {
            "url": page.url,
            "title": await page.title(),
            "on_copilot_host": host in ALLOWED_HOSTS,
            "looks_like_sign_in": "login." in host or "microsoftonline" in host,
            "selector_matches": counts,
            "sends_this_session": bridge.sends,
            "max_sends": MAX_SENDS or "unlimited",
            "reply_pending": bridge.pending is not None,
        }


@mcp.tool()
async def copilot_open(url: str) -> dict:
    """Open an existing Microsoft 365 Copilot conversation by its URL (copied from the
    browser address bar). Only Microsoft Copilot hosts are allowed."""
    check_url(url)
    async with bridge.lock:
        page = await bridge.ensure()
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        bridge.pending = None
        bridge.remember_url(page)
        return {"url": page.url, "title": await page.title(),
                "message": "Opened. If a sign-in page appears, the user must complete it in the browser."}


@mcp.tool()
async def copilot_new_chat() -> dict:
    """Navigate to the Copilot home page to start a fresh conversation."""
    async with bridge.lock:
        page = await bridge.ensure()
        await page.goto(HOME_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        bridge.pending = None
        return {"url": page.url}


@mcp.tool()
async def copilot_send(prompt: str, timeout_seconds: int = 180) -> dict:
    """Type a prompt into the open Copilot conversation, submit it, and wait for the reply.
    Returns {response, complete}. If complete is false, do NOT resend: call copilot_wait."""
    if not prompt.strip():
        raise ValueError("Prompt must not be empty.")
    timeout_seconds = max(15, min(timeout_seconds, 600))
    async with bridge.lock:
        if MAX_SENDS and bridge.sends >= MAX_SENDS:
            raise RuntimeError(
                f"Send limit reached ({MAX_SENDS} prompts this session). Ask the user before "
                "continuing; they can raise COPILOT_MAX_SENDS or restart the server."
            )
        if bridge.pending is not None:
            raise RuntimeError("A previous reply is still pending. Call copilot_wait first.")
        page = await bridge.ensure()
        composer = await bridge.composer(page)
        if composer is None:
            raise RuntimeError(
                "No visible, editable composer found. The user may need to sign in, or the "
                "'composer' selector in selectors.json needs updating (see copilot_inspect)."
            )
        before = await bridge.assistant_texts(page)
        bridge.pending = {"before_count": len(before), "before_last": before[-1] if before else None}
        await bridge.type_prompt(page, composer, prompt)
        method = await bridge.click_send(composer)
        bridge.sends += 1
        result = await bridge.wait_for_reply(page, timeout_seconds)
        return {"prompt": prompt, "submitted_via": method, **result}


@mcp.tool()
async def copilot_wait(timeout_seconds: int = 120) -> dict:
    """Keep waiting for the reply to the last prompt after copilot_send timed out.
    Never resends anything."""
    timeout_seconds = max(5, min(timeout_seconds, 600))
    async with bridge.lock:
        if bridge.pending is None:
            return {"complete": True, "message": "Nothing pending. Use copilot_read."}
        page = await bridge.ensure()
        return await bridge.wait_for_reply(page, timeout_seconds)


@mcp.tool()
async def copilot_read(count: int = 1) -> dict:
    """Return the last `count` visible Copilot replies in the open conversation (oldest first)."""
    count = max(1, min(count, 20))
    async with bridge.lock:
        page = await bridge.ensure()
        msgs = await bridge.assistant_texts(page)
        return {"url": page.url, "total_replies": len(msgs), "replies": msgs[-count:],
                "still_generating": await bridge.stop_visible(page)}


@mcp.tool()
async def copilot_poll() -> dict:
    """Report whether a new, finished Copilot reply has appeared since the last check, e.g. one
    the user triggered by typing directly in the browser. The first poll on a conversation only
    records a baseline."""
    async with bridge.lock:
        page = await bridge.ensure()
        if await bridge.stop_visible(page):
            return {"changed": False, "still_generating": True, "url": page.url}
        msgs = await bridge.assistant_texts(page)
        if not msgs:
            return {"changed": False, "url": page.url}
        seen = bridge.state.setdefault("seen", {})
        latest_digest = digest(msgs[-1])
        previous = seen.get(page.url)
        seen[page.url] = latest_digest
        bridge.remember_url(page)
        if previous is None:
            return {"changed": False, "baseline_set": True, "url": page.url}
        if previous == latest_digest:
            return {"changed": False, "url": page.url}
        return {"changed": True, "url": page.url, "response": msgs[-1]}


@mcp.tool()
async def copilot_inspect() -> dict:
    """Diagnostics for calibrating selectors.json: lists input boxes, labelled buttons, data-testid
    counts and likely message containers in every frame of the current page. Contains page text
    samples, so treat the output as potentially sensitive."""
    async with bridge.lock:
        page = await bridge.ensure()
        frames = []
        for frame in page.frames:
            try:
                info = await frame.evaluate(INSPECT_JS)
            except PlaywrightError as exc:
                info = {"error": exc.message.splitlines()[0]}
            if frame != page.main_frame and not any(info.get(k) for k in ("inputs", "message_candidates")):
                continue
            frames.append({"frame_url": frame.url, "is_main": frame == page.main_frame, **info})
        return {"url": page.url, "selectors_in_use": bridge.sel, "frames": frames}


@mcp.tool()
async def copilot_reload_selectors() -> dict:
    """Re-read selectors.json after editing it, without restarting the server."""
    async with bridge.lock:
        bridge.sel = load_selectors()
        return {"selectors_file": str(SELECTORS_FILE), "selectors": bridge.sel}


if __name__ == "__main__":
    log(f"starting; state dir {STATE_DIR}, selectors {SELECTORS_FILE}")
    mcp.run(transport="stdio")
