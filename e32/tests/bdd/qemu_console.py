"""
qemu_console.py -- talk to the e32 console in Espressif's QEMU (or on a board).

UNTESTED: neither qemu-system-xtensa nor the cross compiler was available
when this was written, so this module has never driven a real QEMU.  It is
kept small and defensive on purpose.

    con = boot_flash(tree)                 # make flash.img, start QEMU
    con.prompt()                           # wait for "> " at a line start
    m = con.mark(); con.enter("s")         # sends "s\\r"
    con.wait_for("all ok", since=m)
    con.raw                                # every byte received (transcript)
    con.close()

A Console collects every byte its transport receives in a background
thread.  Positions ("marks") are byte offsets into that transcript; text is
decoded as Latin-1 so a character offset equals a byte offset.
"""
import os
import re
import signal
import socket
import subprocess
import threading
import time
from pathlib import Path

TIMEOUT = float(os.environ.get("E32_TIMEOUT", "15"))
BOOT_TIMEOUT = float(os.environ.get("E32_BOOT_TIMEOUT", "30"))
DOWNLOAD_PORT = 5556

PROMPT_RE = re.compile(r"(?:^|\n)> ")

QEMU_FLASH_ARGS = ["-nographic", "-machine", "esp32",
                   "-drive", "file=flash.img,if=mtd,format=raw"]
QEMU_DOWNLOAD_ARGS = ["-nographic", "-machine", "esp32",
                      "-drive", "file=empty.img,if=mtd,format=raw",
                      "-global", "driver=esp32.gpio,property=strap_mode,value=0x0f",
                      "-serial", f"tcp::{DOWNLOAD_PORT},server,nowait"]


class ConsoleTimeout(AssertionError):
    pass


class Console:
    """Transcript, waiting and sending; subclasses provide the transport."""

    name = "console"

    def __init__(self):
        self.raw = bytearray()
        self._cond = threading.Condition()
        self._eof = False
        self._last_rx = time.monotonic()
        self._thread = None

    # Transport hooks -------------------------------------------------------
    def _read(self):            # -> bytes; b"" at end of stream
        raise NotImplementedError

    def _write(self, data):
        raise NotImplementedError

    def _shutdown(self):
        pass

    # Reader thread ---------------------------------------------------------
    def _start_reader(self):
        self._thread = threading.Thread(target=self._pump, daemon=True)
        self._thread.start()

    def _pump(self):
        while True:
            try:
                data = self._read()
            except (OSError, ValueError):
                data = b""
            with self._cond:
                if not data:
                    self._eof = True
                    self._cond.notify_all()
                    return
                self.raw.extend(data)
                self._last_rx = time.monotonic()
                self._cond.notify_all()

    # Sending ----------------------------------------------------------------
    def send(self, data):
        if isinstance(data, str):
            data = data.encode("latin-1")
        self._write(bytes(data))

    def enter(self, line):
        """Type a line the way a terminal does: the text, then CR."""
        self.send(line.encode("latin-1") + b"\r")

    # Reading ----------------------------------------------------------------
    def mark(self):
        with self._cond:
            return len(self.raw)

    def text(self, since=0):
        with self._cond:
            return bytes(self.raw[since:]).decode("latin-1")

    def lines(self, since=0, complete_only=False):
        """Lines received since a mark, without CR/LF."""
        txt = self.text(since)
        parts = txt.split("\n")
        if complete_only:
            parts = parts[:-1]
        return [p.rstrip("\r") for p in parts]

    def _wait(self, check, timeout, what):
        deadline = time.monotonic() + (TIMEOUT if timeout is None else timeout)
        with self._cond:
            while True:
                found = check(bytes(self.raw).decode("latin-1"))
                if found is not None:
                    return found
                left = deadline - time.monotonic()
                if left <= 0 or self._eof:
                    tail = bytes(self.raw[-1500:]).decode("latin-1")
                    why = "stream closed" if self._eof else f"timeout"
                    raise ConsoleTimeout(f"{self.name}: {why} waiting for {what}\n"
                                         f"--- last output ---\n{tail}")
                self._cond.wait(min(left, 0.2))

    def wait_for(self, pattern, timeout=None, since=0):
        """Wait for a literal string or a compiled regex; return the match.
        The match is against the text from `since` on, so its offsets are
        relative to `since`."""
        rx = pattern if isinstance(pattern, re.Pattern) else re.compile(re.escape(pattern))

        def check(txt):
            return rx.search(txt[since:])
        return self._wait(check, timeout, repr(getattr(rx, "pattern", rx)))

    def wait_for_line(self, regex, timeout=None, since=0):
        """Wait for a complete line matching regex (re.search); return it."""
        rx = re.compile(regex)

        def check(txt):
            for line in txt[since:].split("\n")[:-1]:
                line = line.rstrip("\r")
                if rx.search(line):
                    return line
            return None
        return self._wait(check, timeout, f"a line matching /{regex}/")

    def wait_count(self, text, count, timeout=None, since=0):
        def check(txt):
            return True if txt.count(text, since) >= count else None
        self._wait(check, timeout, f"{count} x {text!r}")
        return self.text(since).count(text)

    def prompt(self, timeout=None, since=0):
        """Wait for the monitor prompt "> " at the start of a line."""
        return self.wait_for(PROMPT_RE, timeout, since)

    def quiet(self, period=0.5, timeout=None):
        """Wait until nothing has arrived for `period` seconds."""
        deadline = time.monotonic() + (TIMEOUT if timeout is None else timeout)
        while time.monotonic() < deadline:
            with self._cond:
                idle = time.monotonic() - self._last_rx
                if idle >= period or self._eof:
                    return
            time.sleep(min(0.1, period))

    def close(self):
        try:
            self._shutdown()
        finally:
            if self._thread:
                self._thread.join(timeout=2)


class ProcessConsole(Console):
    """A child process whose stdout/stdin are the console (QEMU -nographic,
    or "make qemu").  QEMU's -nographic multiplexer treats Ctrl-A as its
    escape key, so a literal 0x01 is sent doubled."""

    def __init__(self, argv, cwd, env=None, ctrl_a_escape=True, name="qemu"):
        super().__init__()
        self.name = name
        self.argv = argv
        self.ctrl_a_escape = ctrl_a_escape
        self.proc = subprocess.Popen(argv, cwd=str(cwd), env=env,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, start_new_session=True)
        self._start_reader()

    def _read(self):
        return os.read(self.proc.stdout.fileno(), 4096)

    def _write(self, data):
        if self.ctrl_a_escape:
            data = data.replace(b"\x01", b"\x01\x01")
        self.proc.stdin.write(data)
        self.proc.stdin.flush()

    def _shutdown(self):
        if self.proc.poll() is None:
            try:
                os.killpg(self.proc.pid, signal.SIGTERM)
                self.proc.wait(timeout=5)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(self.proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        for f in (self.proc.stdin, self.proc.stdout):
            try:
                f.close()
            except OSError:
                pass


class TcpConsole(Console):
    """QEMU's UART0 exported with -serial tcp::PORT,server,nowait."""

    def __init__(self, port=DOWNLOAD_PORT, host="localhost", timeout=10):
        super().__init__()
        self.name = f"tcp:{port}"
        deadline = time.monotonic() + timeout
        while True:
            try:
                self.sock = socket.create_connection((host, port), timeout=2)
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.2)
        self.sock.settimeout(None)
        self._start_reader()

    def _read(self):
        return self.sock.recv(4096)

    def _write(self, data):
        self.sock.sendall(data)

    def _shutdown(self):
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()


class SerialConsole(Console):
    """A physical board on a serial port (needs pyserial)."""

    def __init__(self, port, baud=115200):
        super().__init__()
        import serial                      # optional dependency
        self.name = port
        self.ser = serial.Serial(port, baud, timeout=0.2)
        self._stop = False
        self._start_reader()

    def _read(self):
        while not self._stop:
            data = self.ser.read(4096)
            if data:
                return data
        return b""

    def _write(self, data):
        self.ser.write(data)
        self.ser.flush()

    def reset(self):
        """Pulse EN through RTS, as esptool does on DevKit boards."""
        self.ser.dtr = False
        self.ser.rts = True
        time.sleep(0.1)
        self.ser.rts = False

    def _shutdown(self):
        self._stop = True
        time.sleep(0.3)
        self.ser.close()


# --------------------------------------------------------------------------
# Starting QEMU
# --------------------------------------------------------------------------

def _make(tree, target, env):
    p = subprocess.run(["make", target], cwd=str(tree), env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", "replace")
    assert p.returncode == 0, f"make {target} failed (rc={p.returncode}):\n{out[-3000:]}"
    return out


def boot_flash(tree, qemu, env=None):
    """Build flash.img and boot it; the console is QEMU's stdio."""
    _make(tree, "flash.img", env)
    return ProcessConsole([qemu] + QEMU_FLASH_ARGS, tree, env=env)


def make_empty_img(tree):
    path = Path(tree) / "empty.img"
    if not path.exists():
        path.write_bytes(b"\xff" * (4 * 1024 * 1024))
    return path


def start_download_mode(tree, qemu, env=None, args=None):
    """Start QEMU with GPIO0 strapped low (ROM download mode) and UART0 on
    TCP port 5556.  Returns the process console (QEMU's monitor/stdout);
    connect to the UART with TcpConsole() once esptool is done with it."""
    make_empty_img(tree)
    return ProcessConsole([qemu] + (args or QEMU_DOWNLOAD_ARGS), tree, env=env,
                          name="qemu-monitor")
