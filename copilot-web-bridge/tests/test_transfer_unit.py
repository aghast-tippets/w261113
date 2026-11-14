"""Unit tests for the browser-free helpers in transfer.py."""
from __future__ import annotations

import importlib
import os

import pytest

import transfer


def test_msys_paths_convert_to_windows():
    assert transfer.msys_to_windows("/c/Users/me/report.docx") == "C:\\Users\\me\\report.docx"
    assert transfer.msys_to_windows("/cygdrive/d/data/x.csv") == "D:\\data\\x.csv"
    assert transfer.msys_to_windows("/c") == "C:\\"
    assert transfer.msys_to_windows("/home/me/x.txt") == "/home/me/x.txt"  # needs cygpath, left alone
    assert transfer.msys_to_windows("C:\\already\\windows") == "C:\\already\\windows"


@pytest.mark.parametrize("name,expected", [
    ("report.docx", "report.docx"),
    ("../../etc/passwd", "passwd"),
    ("C:\\Users\\me\\a.txt", "a.txt"),
    ('bad<>:"|?*name.txt', "bad_______name.txt"),
    ("CON.txt", "_CON.txt"),
    ("   ", "file"),
    ("what?.txt", "what_.txt"),
])
def test_safe_filename(name, expected):
    assert transfer.safe_filename(name) == expected


def test_unique_path_never_overwrites(tmp_path):
    first = transfer.unique_path(tmp_path, "a.txt")
    first.write_text("1")
    second = transfer.unique_path(tmp_path, "a.txt")
    assert second.name == "a-1.txt" and not second.exists()


def test_sniff_magic_bytes():
    assert transfer.sniff(transfer.solid_png(2, 2, (0, 0, 0)))[0] == "image/png"
    assert transfer.sniff(b"\xff\xd8\xff\xe0rest")[0] == "image/jpeg"
    assert transfer.sniff(b"%PDF-1.7")[0] == "application/pdf"
    assert transfer.sniff(b"PK\x03\x04docx")[0] == "application/zip"
    assert transfer.sniff("héllo".encode())[0] == "text/plain"
    assert transfer.sniff(bytes([0xff, 0xfe, 0x00, 0x81]))[0] == "application/octet-stream"


def test_png_writer_and_digits_image():
    png = transfer.digits_png("4827")
    w, h = transfer.png_size(png)
    assert (w, h) == ((4 * 6 - 1 + 4) * 16, (7 + 4) * 16)
    assert transfer.sniff(png)[0] == "image/png"


def test_language_extensions():
    assert transfer.ext_for_language("python") == "py"
    assert transfer.ext_for_language("CSV") == "csv"
    assert transfer.ext_for_language("") == "txt"


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    """Reload transfer with its state dir and upload roots inside tmp_path."""
    monkeypatch.setenv("COPILOT_BRIDGE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("COPILOT_UPLOAD_ROOTS", str(tmp_path / "allowed"))
    monkeypatch.setenv("COPILOT_MAX_UPLOAD_MB", "0.01")
    (tmp_path / "allowed").mkdir()
    mod = importlib.reload(transfer)
    yield mod, tmp_path
    monkeypatch.undo()
    importlib.reload(transfer)


def test_upload_validation(isolated):
    t, tmp = isolated
    ok = tmp / "allowed" / "notes.txt"
    ok.write_text("fine")
    assert t.validate_uploads([str(ok)]) == [ok.resolve()]

    outside = tmp / "elsewhere.txt"
    outside.write_text("x")
    with pytest.raises(ValueError, match="outside the allowed folders"):
        t.validate_uploads([str(outside)])
    assert t.validate_uploads([str(outside)], enforce_roots=False)  # the human chose it in the chat

    for secret in (".env", "id_rsa", "server.pem", "credentials.json"):
        p = tmp / "allowed" / secret
        p.write_text("s")
        with pytest.raises(ValueError, match="secret"):
            t.validate_uploads([str(p)], enforce_roots=False)

    cookie = tmp / "state" / "profile" / "Cookies"
    cookie.parent.mkdir(parents=True)
    cookie.write_text("c")
    with pytest.raises(ValueError, match="bridge's own state"):
        t.validate_uploads([str(cookie)], enforce_roots=False)

    outbox_file = t.OUTBOX_DIR / "proof.txt"
    outbox_file.parent.mkdir(parents=True)
    outbox_file.write_text("ok")
    assert t.validate_uploads([str(outbox_file)])  # the exchange folder is always allowed

    big = tmp / "allowed" / "big.bin"
    big.write_bytes(os.urandom(20_000))
    with pytest.raises(ValueError, match="limit"):
        t.validate_uploads([str(big)])

    with pytest.raises(ValueError, match="Not a file"):
        t.validate_uploads([str(tmp / "allowed" / "missing.txt")])
