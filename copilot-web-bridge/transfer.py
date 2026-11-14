"""
Pure helpers for moving files between Claude and Copilot: path handling, upload safety checks,
file naming, content sniffing and a tiny PNG writer. No browser code lives here, so it can be
unit-tested and imported by the live proof script cheaply.
"""
from __future__ import annotations

import hashlib
import os
import re
import struct
import subprocess
import zlib
from pathlib import Path


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except ValueError:
        return default


# --------------------------------------------------------------------------
# Locations
# --------------------------------------------------------------------------
STATE_DIR = Path(os.environ.get("COPILOT_BRIDGE_DIR") or Path.home() / ".copilot-web-bridge")
PROFILE_DIR = STATE_DIR / "profile"
EXCHANGE_DIR = STATE_DIR / "exchange"
OUTBOX_DIR = EXCHANGE_DIR / "outbox"   # always an allowed upload root
INBOX_DIR = Path(os.environ.get("COPILOT_INBOX_DIR") or EXCHANGE_DIR / "inbox")

MAX_UPLOAD_MB = _env_float("COPILOT_MAX_UPLOAD_MB", 50)
MAX_UPLOAD_FILES = int(_env_float("COPILOT_MAX_UPLOAD_FILES", 10))
MAX_DOWNLOAD_MB = _env_float("COPILOT_MAX_DOWNLOAD_MB", 100)


# --------------------------------------------------------------------------
# Paths (MSYS2-aware)
# --------------------------------------------------------------------------
def msys_to_windows(path: str) -> str:
    """'/c/Users/x/f.txt' or '/cygdrive/c/...' -> 'C:\\Users\\x\\f.txt'. Other paths unchanged."""
    m = re.match(r"^/(?:cygdrive/)?([a-zA-Z])(?:/(.*))?$", path)
    if not m:
        return path
    rest = (m.group(2) or "").replace("/", "\\")
    return f"{m.group(1).upper()}:\\{rest}"


def _cygpath(path: str) -> str | None:
    try:
        out = subprocess.run(["cygpath", "-w", path], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None if out.returncode == 0 else None


def normalize_path(raw: str | os.PathLike) -> Path:
    """Resolve a user/Claude-supplied path. On Windows, MSYS-style paths are converted."""
    s = str(raw).strip().strip('"').strip("'")
    if os.name == "nt" and s.startswith("/"):
        converted = msys_to_windows(s)
        if converted == s:  # e.g. /home/me/x: only MSYS's cygpath knows where that is
            converted = _cygpath(s) or s
        s = converted
    return Path(os.path.expanduser(s)).resolve()


def is_under(child: Path, parent: Path) -> bool:
    c = os.path.normcase(str(child))
    p = os.path.normcase(str(parent)).rstrip("\\/")
    return c == p or c.startswith(p + os.sep)


def upload_roots() -> list[Path]:
    """Folders Claude may upload from: COPILOT_UPLOAD_ROOTS (os.pathsep-separated, ';' on
    Windows) or the server's working directory, plus the bridge's exchange folder."""
    raw = os.environ.get("COPILOT_UPLOAD_ROOTS", "")
    roots = [normalize_path(p) for p in raw.split(os.pathsep) if p.strip()]
    if not roots:
        roots = [Path.cwd().resolve()]
    roots.append(EXCHANGE_DIR.resolve())
    return roots


_SECRET_NAMES = [
    r"\.env(\..*)?", r".*\.(pem|key|pfx|p12|kdbx|ppk|jks|keystore|asc)", r"id_(rsa|dsa|ecdsa|ed25519)(\.pub)?",
    r"(credentials|secrets?)(\..*)?", r"token_cache\.json", r"\.netrc", r"\.git-credentials", r"\.npmrc",
    r"\.pypirc", r"\.claude\.json",
]
_SECRET_DIRS = {".ssh", ".aws", ".azure", ".gnupg", ".kube", ".docker", ".git", ".claude"}


def validate_uploads(paths: list[str], *, enforce_roots: bool = True) -> list[Path]:
    """Check every path before anything is sent. Raises ValueError explaining the first problem."""
    if not paths:
        raise ValueError("No files given.")
    if len(paths) > MAX_UPLOAD_FILES:
        raise ValueError(f"Too many files ({len(paths)}); the limit is {MAX_UPLOAD_FILES} (COPILOT_MAX_UPLOAD_FILES).")
    roots = upload_roots() if enforce_roots else []
    state, exchange = STATE_DIR.resolve(), EXCHANGE_DIR.resolve()
    result: list[Path] = []
    for raw in paths:
        p = normalize_path(raw)
        if not p.is_file():
            raise ValueError(f"Not a file: {raw!r} (resolved to {p}).")
        if is_under(p, state) and not is_under(p, exchange):
            raise ValueError(f"Refusing to upload {p}: it is part of the bridge's own state (browser profile, cookies).")
        name = p.name.lower()
        if any(re.fullmatch(pat, name) for pat in _SECRET_NAMES) or _SECRET_DIRS & {part.lower() for part in p.parts}:
            raise ValueError(f"Refusing to upload {p}: it looks like a secret or credential file.")
        size_mb = p.stat().st_size / 1_048_576
        if size_mb > MAX_UPLOAD_MB:
            raise ValueError(f"{p.name} is {size_mb:.1f} MB; the limit is {MAX_UPLOAD_MB:g} MB (COPILOT_MAX_UPLOAD_MB).")
        if enforce_roots and not any(is_under(p, r) for r in roots):
            raise ValueError(
                f"Refusing to upload {p}: it is outside the allowed folders {[str(r) for r in roots]}. "
                "Ask the user, who can set COPILOT_UPLOAD_ROOTS or copy the file into the exchange outbox."
            )
        result.append(p)
    return result


# --------------------------------------------------------------------------
# Naming and content
# --------------------------------------------------------------------------
_WIN_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def safe_filename(name: str, default: str = "file") -> str:
    name = name.replace("\\", "/").split("/")[-1]
    name = re.sub(r'[<>:"|?*\x00-\x1f]', "_", name).strip(" .")
    if not name:
        name = default
    if name.split(".")[0].upper() in _WIN_RESERVED:
        name = "_" + name
    if len(name) > 120:
        stem, dot, ext = name.rpartition(".")
        name = (stem[: 110] + dot + ext[:9]) if dot and len(ext) <= 9 else name[:120]
    return name


def unique_path(directory: Path, name: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    candidate = directory / name
    stem, dot, ext = name.rpartition(".")
    if not dot:
        stem, ext = name, ""
    n = 1
    while candidate.exists():
        candidate = directory / (f"{stem}-{n}.{ext}" if ext else f"{stem}-{n}")
        n += 1
    return candidate


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sniff(data: bytes) -> tuple[str, str]:
    """(mime, extension) from magic bytes; falls back to text/plain or octet-stream."""
    head = data[:16]
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "png"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", "jpg"
    if head[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif", "gif"
    if head[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp", "webp"
    if head.startswith(b"%PDF"):
        return "application/pdf", "pdf"
    if head.startswith(b"PK\x03\x04"):
        return "application/zip", "zip"
    if data.lstrip()[:5].lower() == b"<svg " or b"<svg" in data[:256].lower():
        return "image/svg+xml", "svg"
    try:
        data[:4096].decode("utf-8")
        return "text/plain", "txt"
    except UnicodeDecodeError:
        return "application/octet-stream", "bin"


_LANG_EXT = {
    "python": "py", "py": "py", "javascript": "js", "js": "js", "typescript": "ts", "ts": "ts",
    "json": "json", "csv": "csv", "bash": "sh", "sh": "sh", "shell": "sh", "powershell": "ps1",
    "ps1": "ps1", "html": "html", "css": "css", "sql": "sql", "yaml": "yaml", "yml": "yaml",
    "markdown": "md", "md": "md", "xml": "xml", "c": "c", "cpp": "cpp", "c++": "cpp", "csharp": "cs",
    "cs": "cs", "c#": "cs", "java": "java", "go": "go", "rust": "rs", "ruby": "rb", "vba": "bas",
}


def ext_for_language(language: str) -> str:
    return _LANG_EXT.get((language or "").lower(), "txt")


def png_size(data: bytes) -> tuple[int, int] | None:
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return struct.unpack(">II", data[16:24])


# --------------------------------------------------------------------------
# Minimal PNG writer (used for proof images and test fixtures)
# --------------------------------------------------------------------------
def png_bytes(width: int, height: int, rows: list[bytes]) -> bytes:
    """rows: `height` byte strings of width*3 RGB bytes each."""
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)

    raw = b"".join(b"\x00" + r for r in rows)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def solid_png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    return png_bytes(width, height, [bytes(rgb) * width] * height)


# 5x7 glyphs for the digits 2-9 (0/1 are left out: easily confused with O/I/l).
DIGIT_GLYPHS = {
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
}
GLYPH_SCALE, GLYPH_MARGIN = 16, 2  # in glyph cells; the fake Copilot decodes with the same values


def digits_png(code: str, scale: int = GLYPH_SCALE, margin: int = GLYPH_MARGIN) -> bytes:
    """Black digits on white, big enough for any vision model to read."""
    cols = len(code) * 6 - 1 + 2 * margin
    rows = 7 + 2 * margin
    grid = [[0] * cols for _ in range(rows)]
    for k, ch in enumerate(code):
        glyph = DIGIT_GLYPHS[ch]
        for y in range(7):
            for x in range(5):
                if glyph[y][x] == "1":
                    grid[margin + y][margin + k * 6 + x] = 1
    white, black = b"\xff\xff\xff", b"\x00\x00\x00"
    out_rows = []
    for row in grid:
        line = b"".join((black if v else white) * scale for v in row)
        out_rows.extend([line] * scale)
    return png_bytes(cols * scale, rows * scale, out_rows)
