"""
Terminal chat with Microsoft 365 Copilot through the copilot-web browser bridge.
No Claude Code (and no Claude credit) needed: you type, Copilot answers here.

  .venv/Scripts/python.exe chat.py [conversation-url]

Commands: /open <url>  /new  /read  /url  /quit
Uses the same profile, selectors.json and environment variables as server.py.
"""
from __future__ import annotations

import asyncio
import sys

from server import HOME_URL, bridge, check_url

HELP = "Commands: /open <url>  /new  /read  /url  /quit   (anything else is sent to Copilot)"


async def ask(prompt: str) -> None:
    page = await bridge.ensure()
    composer = await bridge.composer(page)
    if composer is None:
        print("! No chat box found. Sign in in the Edge window, or fix 'composer' in selectors.json.")
        return
    before = await bridge.assistant_texts(page)
    bridge.pending = {"before_count": len(before), "before_last": before[-1] if before else None}
    await bridge.type_prompt(page, composer, prompt)
    await bridge.click_send(composer)
    print("… waiting for Copilot", flush=True)
    result = await bridge.wait_for_reply(page, 300)
    while not result["complete"]:
        print("… still waiting (Ctrl+C to stop)", flush=True)
        result = await bridge.wait_for_reply(page, 120)
    print(f"\nCopilot:\n{result['response']}\n", flush=True)


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
