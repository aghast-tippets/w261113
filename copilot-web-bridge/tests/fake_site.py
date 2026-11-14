"""
Local web server for the fake Copilot page. Besides the page it serves cookie-protected
resources, to prove the bridge fetches content as the signed-in browser user:

  /protected/<name>.png   image, only with the session cookie
  /files/<name>           file download (Content-Disposition), only with the cookie
  /viewer/<name>          an HTML "viewer" page, or the file itself with ?download=1
"""
from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from transfer import solid_png

PAGE = (Path(__file__).parent / "fake_copilot" / "index.html").read_bytes()
PROTECTED_PNG = solid_png(80, 60, (10, 120, 200))
FILE_BYTES = "protected file content ✓\nline 2\n".encode("utf-8")
COOKIE = "fakeauth=ok"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:  # keep test output quiet
        pass

    def _send(self, status: int, body: bytes, ctype: str, extra: dict | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        url = urlparse(self.path)
        query = parse_qs(url.query)
        authed = COOKIE in (self.headers.get("Cookie") or "")
        if url.path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8", {"Set-Cookie": COOKIE + "; Path=/; SameSite=Lax"})
        elif not authed and url.path.split("/")[1] in ("protected", "files", "viewer"):
            self._send(401, b"sign in required", "text/plain")
        elif url.path.startswith("/protected/"):
            self._send(200, PROTECTED_PNG, "image/png")
        elif url.path.startswith("/files/"):
            name = url.path.rsplit("/", 1)[-1]
            self._send(200, FILE_BYTES, "text/plain; charset=utf-8",
                       {"Content-Disposition": f'attachment; filename="{name}"'})
        elif url.path.startswith("/viewer/"):
            if query.get("download") == ["1"]:
                self._send(200, FILE_BYTES, "application/octet-stream")
            else:
                self._send(200, b"<html><body>Document viewer</body></html>", "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")


def start(port: int = 0) -> tuple[ThreadingHTTPServer, str]:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


if __name__ == "__main__":
    srv, base = start(8765)
    print(f"Fake Copilot at {base}/  (Ctrl+C to stop)")
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        srv.shutdown()
