"""
Test harness: each test starts the real server.py over MCP stdio (exactly how Claude Code runs
it) and talks to it as Claude would, against the fake Copilot page served by fake_site.py.

Browser: by default Playwright's channel from COPILOT_BROWSER_CHANNEL (msedge on Windows), or
COPILOT_BROWSER_EXECUTABLE. Tests always run headless.
"""
from __future__ import annotations

import base64
import json
import os
import sys
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import fake_site

BRIDGE_DIR = Path(__file__).resolve().parent.parent
SERVER = BRIDGE_DIR / "server.py"
SELECTORS = Path(__file__).resolve().parent / "fake_copilot" / "selectors.json"


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def site():
    server, base = fake_site.start()
    yield base
    server.shutdown()


@dataclass
class Result:
    is_error: bool
    data: dict | str
    images: list[bytes] = field(default_factory=list)
    image_types: list[str] = field(default_factory=list)


class Client:
    def __init__(self, session: ClientSession):
        self.session = session

    async def call(self, tool: str, **args) -> Result:
        res = await self.session.call_tool(tool, args)
        texts = [c.text for c in res.content if c.type == "text"]
        images = [c for c in res.content if c.type == "image"]
        raw = texts[0] if texts else ""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = raw
        return Result(res.isError, data, [base64.b64decode(i.data) for i in images], [i.mimeType for i in images])

    async def ok(self, tool: str, **args) -> dict:
        result = await self.call(tool, **args)
        assert not result.is_error, f"{tool} failed: {result.data}"
        return result.data


@pytest.fixture
def files_dir(tmp_path: Path) -> Path:
    d = tmp_path / "files"
    d.mkdir()
    return d


@pytest.fixture
def bridge(site, tmp_path, files_dir):
    """Usage: async with bridge(query="?static_input", COPILOT_X="1") as client: ..."""

    @asynccontextmanager
    async def open_bridge(query: str = "", **env):
        e = dict(os.environ)
        e.update(
            COPILOT_HOME_URL=f"{site}/{query}",
            COPILOT_HEADLESS="1",
            COPILOT_BRIDGE_DIR=str(tmp_path / "state"),
            COPILOT_SELECTORS=str(SELECTORS),
            COPILOT_STABLE_SECONDS="1",
            COPILOT_GIVE_UP_SECONDS="15",
            COPILOT_SEND_TIMEOUT="60",
            COPILOT_UPLOAD_TIMEOUT="10",
            COPILOT_UPLOAD_ROOTS=str(files_dir),
        )
        e.pop("COPILOT_INBOX_DIR", None)
        e.update({k: str(v) for k, v in env.items()})
        params = StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=e, cwd=str(BRIDGE_DIR))
        with open(tmp_path / "server.log", "a", encoding="utf-8") as errlog:
            async with stdio_client(params, errlog=errlog) as (read, write), ClientSession(read, write) as session:
                await session.initialize()
                yield Client(session)

    return open_bridge


def reply_hashes(response: str) -> dict[str, tuple[int, str]]:
    """Parse the fake Copilot's 'FILE name | size | sha256' receipt lines."""
    out = {}
    for line in response.splitlines():
        if line.startswith("FILE "):
            name, size, digest = (p.strip() for p in line[5:].split("|"))
            out[name] = (int(size), digest)
    return out
