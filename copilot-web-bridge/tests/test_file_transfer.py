"""
End-to-end proof, over MCP stdio, that files move both ways between Claude (the MCP client,
the master) and Copilot (the fake web UI, the slave) byte for byte.
"""
from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

import pytest

import fake_site
import transfer
from conftest import reply_hashes

pytestmark = pytest.mark.anyio


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def reply_value(response: str, key: str) -> str:
    m = re.search(rf"{re.escape(key)}:\s*([0-9a-f]{{64}})", response)
    assert m, f"{key!r} not in reply: {response!r}"
    return m.group(1)


# ---------------------------------------------------------------- Claude -> Copilot
async def test_upload_text_and_binary_arrive_intact_via_attach_menu(bridge, files_dir):
    text = files_dir / "notes ü.txt"
    text.write_text("Grüße from Claude\nline 2\n", encoding="utf-8")
    binary = files_dir / "blob.bin"
    binary.write_bytes(os.urandom(200_000))
    async with bridge() as c:
        r = await c.ok("copilot_send", prompt="Please confirm receipt", files=[str(text), str(binary)])
    assert r["complete"] and r["attached"]["method"] == "file_chooser" and r["attached"]["confirmed"]
    received = reply_hashes(r["response"])
    for path in (text, binary):
        data = path.read_bytes()
        assert received[path.name] == (len(data), sha(data)), "Copilot did not receive identical bytes"


async def test_upload_via_static_file_input(bridge, files_dir):
    f = files_dir / "data.csv"
    f.write_text("a,b\n1,2\n")
    async with bridge(query="?static_input") as c:
        r = await c.ok("copilot_send", prompt="Receipt?", files=[str(f)])
    assert r["attached"]["method"] == "file_input"
    assert reply_hashes(r["response"])["data.csv"] == (f.stat().st_size, sha(f.read_bytes()))


async def test_image_upload_is_readable_by_copilot(bridge, files_dir):
    png = files_dir / "proof.png"
    png.write_bytes(transfer.digits_png("482796"))
    async with bridge() as c:
        r = await c.ok("copilot_send", prompt="I have attached an image. What number is shown in it?", files=[str(png)])
    assert r["response"].splitlines()[0].strip() == "482796"


async def test_refused_uploads_send_nothing(bridge, files_dir, tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("not allowed")
    secret = files_dir / ".env"
    secret.write_text("API_KEY=x")
    async with bridge() as c:
        for path, why in ((outside, "outside the allowed folders"), (secret, "secret")):
            r = await c.call("copilot_send", prompt="hi", files=[str(path)])
            assert r.is_error and why in str(r.data)
        status = await c.ok("copilot_status")
    assert status["sends_this_session"] == 0


async def test_unconfirmed_upload_does_not_send_prompt(bridge, files_dir):
    f = files_dir / "a.txt"
    f.write_text("x")
    async with bridge(query="?upload_fail", COPILOT_UPLOAD_TIMEOUT="3") as c:
        r = await c.call("copilot_send", prompt="should never be sent", files=[str(f)])
        assert r.is_error and "Upload not confirmed" in str(r.data)
        read = await c.ok("copilot_read")
        status = await c.ok("copilot_status")
    assert read["total_replies"] == 0 and status["sends_this_session"] == 0


# ---------------------------------------------------------------- Copilot -> Claude
async def test_blob_image_collected_byte_exact_and_shown_inline(bridge):
    async with bridge() as c:
        r = await c.ok("copilot_send", prompt="MAKE-IMAGE n0nce1")
        assert r["reply_artifacts"]["images"] == 1  # the 16px icon is ignored
        res = await c.call("copilot_collect")
    assert not res.is_error
    (image,) = res.data["images"]
    assert image["method"] == "blob_fetch" and image["inline"]
    assert image["sha256"] == reply_value(r["response"], "image-sha256")
    assert sha(Path(image["path"]).read_bytes()) == image["sha256"]
    assert res.image_types == ["image/png"] and sha(res.images[0]) == image["sha256"]


async def test_data_url_image(bridge):
    async with bridge() as c:
        r = await c.ok("copilot_send", prompt="MAKE-DATA-IMAGE n0nce2")
        res = await c.call("copilot_collect")
    (image,) = res.data["images"]
    assert image["method"] == "data_url" and image["sha256"] == reply_value(r["response"], "image-sha256")


async def test_protected_image_fetched_with_browser_session(bridge):
    async with bridge() as c:
        await c.ok("copilot_send", prompt="MAKE-PROTECTED-IMAGE pic")
        res = await c.call("copilot_collect")
    (image,) = res.data["images"]
    assert image["method"] == "http_request"
    assert image["sha256"] == sha(fake_site.PROTECTED_PNG) and (image["width"], image["height"]) == (80, 60)


async def test_svg_chart_falls_back_to_screenshot(bridge):
    async with bridge() as c:
        await c.ok("copilot_send", prompt="MAKE-CHART")
        res = await c.call("copilot_collect")
    (image,) = res.data["images"]
    data = Path(image["path"]).read_bytes()
    assert image["method"] == "screenshot" and transfer.png_size(data) == (200, 120)


async def test_download_button_file_byte_exact(bridge):
    async with bridge() as c:
        r = await c.ok("copilot_send", prompt="MAKE-FILE report.txt n0nce3")
        assert r["reply_artifacts"]["download_buttons"] == 1
        res = await c.call("copilot_collect", images=False, code_blocks=False)
    (f,) = res.data["files"]
    assert f["method"] == "download" and f["name"] == "report.txt"
    assert f["sha256"] == reply_value(r["response"], "file-sha256")
    assert Path(f["path"]).read_text(encoding="utf-8") == "n0nce3\nsecond line ✓\n"


async def test_blob_link_with_download_attribute(bridge):
    async with bridge() as c:
        r = await c.ok("copilot_send", prompt="MAKE-BLOB-LINK out.txt n0nce4")
        res = await c.call("copilot_collect")
    (f,) = res.data["files"]
    assert f["method"] == "blob_fetch" and f["sha256"] == reply_value(r["response"], "file-sha256")


async def test_http_file_link_and_viewer_link(bridge):
    async with bridge() as c:
        await c.ok("copilot_send", prompt="MAKE-LINK-FILE budget.xlsx")
        direct = await c.call("copilot_collect")
        await c.ok("copilot_send", prompt="MAKE-VIEWER-LINK plan.docx")
        viewer = await c.call("copilot_collect")
        await c.ok("copilot_send", prompt="MAKE-PAGE-LINK")
        page = await c.call("copilot_collect")
    (f1,) = direct.data["files"]
    assert f1["method"] == "http_request" and f1["sha256"] == sha(fake_site.FILE_BYTES)
    (f2,) = viewer.data["files"]
    assert f2["method"] == "http_request_download_param" and f2["sha256"] == sha(fake_site.FILE_BYTES)
    assert page.data["files"] == [] and page.data["links"][0]["text"] == "documentation"  # plain link: listed only


async def test_code_block_saved_verbatim(bridge):
    async with bridge() as c:
        await c.ok("copilot_send", prompt="MAKE-CODE n0nce5")
        res = await c.call("copilot_collect")
    (block,) = res.data["code_blocks"]
    expected = 'def proof():\n    value = "n0nce5"\n    if value:\n        return value  # indented\n\treturn None\n'
    assert block["language"] == "python" and block["path"].endswith(".py")
    assert Path(block["path"]).read_text(encoding="utf-8") == expected


# ---------------------------------------------------------------- round trips
async def test_round_trip_file_out_transformed_file_back(bridge, files_dir):
    original = "Claude sends this.\nCopilot returns it uppercased.\n"
    f = files_dir / "roundtrip.txt"
    f.write_text(original, encoding="utf-8")
    async with bridge() as c:
        await c.ok("copilot_send", prompt="ECHO-UPPER", files=[str(f)])
        res = await c.call("copilot_collect")
    (back,) = res.data["files"]
    assert back["name"] == "UPPER-roundtrip.txt"
    assert Path(back["path"]).read_text(encoding="utf-8") == original.upper()


async def test_round_trip_csv_computation(bridge, files_dir):
    f = files_dir / "numbers.csv"
    f.write_text("a,b\n3,4\n10,25\n-2,7\n")
    async with bridge() as c:
        await c.ok("copilot_send", prompt="CSV-SUM", files=[str(f)])
        res = await c.call("copilot_collect")
    (block,) = res.data["code_blocks"]
    assert Path(block["path"]).read_text() == "a,b,sum\n3,4,7\n10,25,35\n-2,7,5\n"


async def test_collected_files_can_be_sent_back(bridge, files_dir):
    """Files land in the exchange inbox, which is an allowed upload root: Claude can forward them."""
    async with bridge() as c:
        await c.ok("copilot_send", prompt="MAKE-FILE fwd.txt n0nce6")
        res = await c.call("copilot_collect")
        path = res.data["files"][0]["path"]
        r = await c.ok("copilot_send", prompt="Receipt?", files=[path])
    assert reply_hashes(r["response"])["fwd.txt"][1] == res.data["files"][0]["sha256"]
