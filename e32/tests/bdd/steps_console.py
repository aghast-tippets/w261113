"""
Console steps: booting QEMU (flash or ROM download mode), driving a board,
typing at mimmo and checking what the console shows.
"""
import os
import re
import time

import pytest
from pytest_bdd import parsers, step

import qemu_console as qc
from support import ENV, World

R = parsers.re


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def manual(what):
    pytest.fail(f"MANUAL: '{what}' needs a person or an instrument at the board; "
                "it is not automated", pytrace=False)


def qemu_env(world):
    env = os.environ.copy()
    env.update(world.make_env())
    return env


def get_console(world: World):
    if world.console is None and world.data.get("tcp_pending"):
        connect_tcp(world)
    if world.console is None and not world.data.get("auto_started"):
        # Scenarios that open with "the operator enters ..." or "the monitor
        # prompt is shown" presume running firmware: boot it the way the
        # scenario's environment tag says.
        world.data["auto_started"] = True
        if "qemu" in world.tags and (ENV.qemu and ENV.cross_gcc or not ENV.port):
            boot_qemu_flash(world)
        elif "hardware" in world.tags:
            board_ready(world)
    assert world.console is not None, "no console: no step booted the firmware or opened a board"
    return world.console


def since(world):
    return world.data.get("mark", 0)


def set_mark(world):
    world.data["mark"] = get_console(world).mark()
    return world.data["mark"]


def _fresh(world, console):
    if world.console is not None:
        world.console.close()
    world.console = console
    world.data.update(mark=0, prompt_since=0, boot_time=time.monotonic(), first_cmd=True)


def boot_qemu_flash(world):
    ENV.need_cross()
    ENV.need_qemu()
    _fresh(world, qc.boot_flash(world.tree, ENV.qemu or "qemu-system-xtensa", qemu_env(world)))


def start_download_qemu(world, args=None):
    ENV.need_cross()
    ENV.need_qemu()
    world.build("e32.bin")
    if world.qemu is not None:
        world.qemu.close()
    world.qemu = qc.start_download_mode(world.tree, ENV.qemu or "qemu-system-xtensa",
                                        qemu_env(world), args=args)
    world.data["tcp_pending"] = True
    time.sleep(1.0)                      # let QEMU open its TCP listener


LOAD_RAM = ("esptool --chip esp32 -p socket://localhost:5556 --no-stub "
            "--before no-reset --after no-reset load-ram e32.bin")


def esptool_load_ram(world):
    ENV.need_esptool()
    res = world.shell(LOAD_RAM, timeout=120)
    assert res.rc == 0, f"esptool load-ram failed:\n{res.out}"
    return res


def connect_tcp(world):
    world.data["tcp_pending"] = False
    _fresh(world, qc.TcpConsole(qc.DOWNLOAD_PORT))
    # The banner went out before we connected: ask for a fresh prompt.
    world.console.send(b"\r")


def open_board(world, reset=True):
    ENV.need_board()
    try:
        import serial  # noqa: F401
    except ImportError:
        if not ENV.force:
            pytest.skip("pyserial not installed (pip install pyserial)")
        raise
    if not isinstance(world.console, qc.SerialConsole):
        _fresh(world, qc.SerialConsole(ENV.port))
    if reset:
        world.data["mark"] = world.console.mark()
        world.data["prompt_since"] = world.data["mark"]
        world.console.reset()


def board_ready(world):
    """Board reset, prompt seen; later checks start after the prompt."""
    open_board(world)
    c = get_console(world)
    c.prompt(timeout=qc.BOOT_TIMEOUT, since=since(world))
    set_mark(world)
    world.data["prompt_since"] = since(world)


def wait_prompt_soft(world):
    """Before typing, let the previous command finish (no failure)."""
    c = get_console(world)
    timeout = qc.BOOT_TIMEOUT if world.data.get("first_cmd") else qc.TIMEOUT
    try:
        c.prompt(timeout=timeout, since=world.data.get("prompt_since", 0))
    except qc.ConsoleTimeout:
        pass
    world.data["first_cmd"] = False


def enter(world, line, wait=True):
    c = get_console(world)
    if wait:
        wait_prompt_soft(world)
    m = set_mark(world)
    world.data["prompt_since"] = m
    world.data["last_cmd"] = line
    c.enter(line)
    return m


def enter_and_wait(world, line):
    m = enter(world, line)
    get_console(world).prompt(since=m)
    return m


def settle(world):
    """Wait for the current command's prompt (or silence) before a
    negative or counting check."""
    c = get_console(world)
    try:
        c.prompt(since=since(world), timeout=qc.TIMEOUT)
    except qc.ConsoleTimeout:
        pass
    c.quiet(0.5)


def shows(world, text, timeout=None):
    return get_console(world).wait_for(world.expand(text), timeout, since=since(world))


def shows_line(world, rx, timeout=None):
    line = get_console(world).wait_for_line(world.expand(rx), timeout, since=since(world))
    world.data["last_line"] = line
    return line


def parse_bytes(spec):
    """'"r 3ffb0001" 08 "0" 0d' -> b'r 3ffb0001\\x080\\r'"""
    out = bytearray()
    for m in re.finditer(r'"([^"]*)"|\b([0-9a-fA-F]{2})\b', spec):
        out += m.group(1).encode("latin-1") if m.group(1) is not None else bytes([int(m.group(2), 16)])
    return bytes(out)


def irq_count(world, line_no):
    m = enter(world, "i")
    c = get_console(world)
    c.prompt(since=m)
    found = re.search(rf"^irq {line_no:2d}: (\d+)", c.text(m).replace("\r", ""), re.M)
    return int(found.group(1)) if found else 0


def ticks(world):
    m = enter(world, "i")
    line = get_console(world).wait_for_line(r"^uptime .*\((\d+) ticks\)$", since=m)
    return int(re.search(r"\((\d+) ticks\)", line).group(1)), line


def last_value(world):
    """The word printed by the last "r <addr>" command."""
    txt = get_console(world).text(since(world)).replace("\r", "")
    m = re.search(r"read [0-9a-f]{8}\n([0-9a-f]{8})", txt)
    if not m:
        get_console(world).wait_for(re.compile(r"read [0-9a-f]{8}\r?\n[0-9a-f]{8}"), since=since(world))
        txt = get_console(world).text(since(world)).replace("\r", "")
        m = re.search(r"read [0-9a-f]{8}\n([0-9a-f]{8})", txt)
    return int(m.group(1), 16)


# --------------------------------------------------------------------------
# Starting the firmware
# --------------------------------------------------------------------------

@step("the firmware is booted in QEMU from flash")
def booted_from_flash(world):
    boot_qemu_flash(world)


@step("the firmware is loaded into RAM in QEMU download mode")
def loaded_into_ram(world):
    start_download_qemu(world)
    esptool_load_ram(world)
    connect_tcp(world)


@step("QEMU is started in download mode with the console on TCP port 5556")
def qemu_download_mode(world):
    start_download_qemu(world)


@step(R(r'QEMU is started with "(?P<options>[^"]+)"'))
def qemu_started_with(world, options):
    ENV.need_cross()
    ENV.need_qemu()
    args = ["-display", "none"] + options.split()
    if "flash.img" in options:
        world.build("flash.img")
    if "tcp::" in options:
        start_download_qemu(world, args=args)
    else:
        _fresh(world, qc.ProcessConsole([ENV.qemu or "qemu-system-xtensa"] + args, world.tree,
                                        env=qemu_env(world), ctrl_a_escape=False))


@step(R(r'the firmware reaches the monitor through "(?P<path>[^"]+)"'))
def reaches_monitor(world, path):
    if path == "esptool load-ram":
        esptool_load_ram(world)
        connect_tcp(world)
    elif path != "flash boot":
        raise AssertionError(f"unknown path {path!r}")
    get_console(world).prompt(timeout=qc.BOOT_TIMEOUT)


@step(R(r'I run "make qemu QEMU=(?P<qemu>[^"]+)" and enter "(?P<line>[^"]*)"'))
def make_qemu_and_enter(world, qemu, line):
    ENV.need_cross()
    ENV.need_qemu()
    world.build("e32.bin")
    cmd = ["make", "qemu", "QEMU=" + world.expand(qemu)]
    _fresh(world, qc.ProcessConsole(cmd, world.tree, env=qemu_env(world), name="make qemu"))
    enter(world, line)
    world.data["mark"] = 0          # the Then steps look at the boot output too


# --------------------------------------------------------------------------
# A physical board
# --------------------------------------------------------------------------

@step("the firmware is running on a board")
@step("the firmware is running on a board after a flash boot")
def running_on_board(world):
    board_ready(world)


@step("a board in download mode on PORT")
def board_in_download_mode(world):
    ENV.need_board()
    assert ENV.force or os.path.exists(ENV.port), f"E32_PORT={ENV.port} does not exist"


@step("a terminal on PORT at 115200 baud, 8 data bits, no parity, 1 stop bit")
def terminal_on_port(world):
    open_board(world, reset=False)


@step("I reset the board")
def reset_board(world):
    if ENV.port or ENV.force:
        open_board(world, reset=True)
    else:
        boot_qemu_flash(world)


@step("the banner is readable")
def banner_readable(world):
    shows(world, "e32: bare-metal ESP32", timeout=qc.BOOT_TIMEOUT)


@step(R(r'I paste (?P<n>\d+) characters of commands while "(?P<cmd>[^"]*)" runs'))
def paste_commands(world, n, cmd):
    enter(world, cmd)
    one = b"r 3ffb1000\r"
    count = int(n) // len(one)
    world.data["pasted"] = count
    get_console(world).send(one * count)


@step("every pasted command is answered")
def pasted_answered(world):
    n = world.data["pasted"]
    got = get_console(world).wait_count("read 3ffb1000", n, since=since(world))
    settle(world)
    assert get_console(world).text(since(world)).count("read 3ffb1000") == n, f"{got} of {n} answered"


@step(R(r"GPIO (?P<gpio>\d+) is tied to (?P<tie>\S+)"))
def gpio_tied(world, gpio, tie):
    manual(f"GPIO {gpio} is tied to {tie}")


@step(R(r"pin (?P<gpio>\d+) measures (?P<volts>.+)"))
def pin_measures(world, gpio, volts):
    manual(f"pin {gpio} measures {volts}")


@step(R(r'I enter "i" and start a stopwatch'))
def stopwatch_start(world):
    world.data["t0"] = time.monotonic()
    world.data["up0"] = ticks(world)[0]


@step(R(r'I enter "i" again after (?P<s>\d+) stopwatch seconds'))
def stopwatch_again(world, s):
    time.sleep(max(0.0, world.data["t0"] + int(s) - time.monotonic()))
    world.data["up1"] = ticks(world)[0]


@step(R(r"the uptime difference is between (?P<lo>[\d.]+) and (?P<hi>[\d.]+) seconds"))
def uptime_difference(world, lo, hi):
    hz = 100                                # HZ in include/io.h
    diff = (world.data["up1"] - world.data["up0"]) / hz
    assert float(lo) <= diff <= float(hi), f"uptime advanced {diff:.2f} s"


@step("the board idles at the prompt for 10 minutes")
def idle_ten_minutes(world):
    board_ready(world)
    time.sleep(600)


@step("it has not reset")
def has_not_reset(world):
    assert "rst:" not in get_console(world).text(since(world))


@step(R(r"the LED (?P<what>on GPIO2 follows|blinks at about 1 Hz|changes state \d+ to \d+ times)"))
def led_observed(world, what):
    manual(f"the LED {what}")


# --------------------------------------------------------------------------
# Typing
# --------------------------------------------------------------------------

@step(R(r'I enter "(?P<line>[^"]*)"'))
def i_enter(world, line):
    enter(world, world.expand(line))


@step(R(r'I immediately enter "(?P<line>[^"]*)" (?P<n>\d+) times'))
@step(R(r'I enter "(?P<line>[^"]*)" (?P<n>\d+) times in quick succession'))
def enter_many(world, line, n):
    c = get_console(world)
    if world.data.get("first_cmd"):
        wait_prompt_soft(world)
    set_mark(world)
    c.send((line + "\r").encode("latin-1") * int(n))


@step(R(r"I send the bytes (?P<spec>.+)"))
def send_bytes(world, spec):
    wait_prompt_soft(world)
    set_mark(world)
    get_console(world).send(parse_bytes(spec))


@step(R(r'I send "(?P<text>[^"]*)" followed by (?P<n>\d+) spaces and 0d'))
def send_spaces(world, text, n):
    wait_prompt_soft(world)
    set_mark(world)
    get_console(world).send(text.encode() + b" " * int(n) + b"\r")


@step(R(r'I send (?P<n>\d+) characters while "(?P<cmd>[^"]*)" runs'))
def send_while(world, n, cmd):
    enter(world, cmd)
    # Spaces: whatever survives the overrun is a harmless blank line.
    get_console(world).send(b" " * int(n))
    get_console(world).wait_for(re.compile(r"all ok|FAILED"), timeout=qc.TIMEOUT, since=since(world))
    get_console(world).send(b"\r")


@step(R(r"I press any key|the developer presses a key"))
def press_key(world):
    c = get_console(world)
    try:
        c.wait_for("Press any key to reboot", since=since(world))
    except qc.ConsoleTimeout:
        pass
    set_mark(world)
    world.data["prompt_since"] = since(world)
    c.send(b" ")


@step(R(r"I (?:wait|watch for) (?P<s>\d+) seconds"))
def wait_seconds(world, s):
    time.sleep(int(s))


@step(R(r'I enter "i" at (?P<t1>\d+) s and again at (?P<t2>\d+) s'))
def enter_i_twice(world, t1, t2):
    t0 = world.data.get("boot_time", time.monotonic())
    time.sleep(max(0.0, t0 + int(t1) - time.monotonic()))
    world.data["ticks1"] = ticks(world)[0]
    time.sleep(max(0.0, t0 + int(t2) - time.monotonic()))
    world.data["ticks2"] = ticks(world)[0]


@step("the routine runs")
def routine_runs(world):
    pytest.fail("PENDING automation: the call12 routine variant is not automated", pytrace=False)


# --------------------------------------------------------------------------
# Checking the console
# --------------------------------------------------------------------------

@step(R(r"the monitor prompt (?:is shown|appears)"))
def prompt_shown(world):
    timeout = qc.BOOT_TIMEOUT if world.data.get("first_cmd") else None
    get_console(world).prompt(timeout=timeout, since=since(world))


@step(R(r'the console shows "(?P<text>.*)"'))
def console_shows(world, text):
    shows(world, text, timeout=qc.BOOT_TIMEOUT if since(world) == 0 else None)


@step(R(r'the console shows "(?P<text>.*)" (?P<n>\d+) times'))
def console_shows_n(world, text, n):
    c = get_console(world)
    c.wait_count(text, int(n), since=since(world))
    settle(world)
    got = c.text(since(world)).count(text)
    assert got == int(n), f"{text!r} shown {got} times, expected {n}"


@step(R(r"the console shows a line matching /(?P<rx>.*)/"))
def console_line(world, rx):
    shows_line(world, rx, timeout=qc.BOOT_TIMEOUT if since(world) == 0 else None)


@step(R(r"the console shows (?P<n>\d+) lines matching /(?P<rx>.*)/"))
def console_n_lines(world, n, rx):
    settle(world)
    lines = [l for l in get_console(world).lines(since(world)) if re.search(rx, l)]
    assert len(lines) == int(n), f"{len(lines)} lines match /{rx}/: {lines}"


@step("the console shows each of:")
def console_each(world, datatable):
    for row in datatable[1:]:
        shows(world, row[0].replace("\\|", "|"))


@step(R(r'the console does not show "(?P<text>.*)"'))
def console_not_shows(world, text):
    settle(world)
    txt = get_console(world).text(since(world))
    assert world.expand(text) not in txt, f"console shows {text!r}"


@step(R(r'the next non-empty line starts with "(?P<text>.*)"'))
def next_line_starts(world, text):
    c = get_console(world)
    prev = world.data["last_line"]
    deadline = time.monotonic() + qc.TIMEOUT
    while True:
        lines = c.lines(since(world), complete_only=True)
        rest = lines[lines.index(prev) + 1:] if prev in lines else []
        nxt = next((l for l in rest if l.strip()), None)
        if nxt is not None or time.monotonic() > deadline:
            break
        time.sleep(0.1)
    assert nxt is not None, f"no line after {prev!r}"
    assert nxt.startswith(text), f"line after {prev!r} is {nxt!r}"


@step(R(r"the console shows nothing more within (?P<s>\d+) seconds"))
def nothing_more(world, s):
    c = get_console(world)
    m = c.wait_for(re.compile(r"\*\*\*[^\n]*\n"), since=since(world))
    end = since(world) + m.end()
    time.sleep(int(s))
    rest = c.text(end)
    assert not rest.strip(), f"more output after the first report line: {rest[:300]!r}"


@step("every line the firmware prints ends with the bytes 0d 0a")
def crlf_everywhere(world):
    c = get_console(world)
    c.prompt(timeout=qc.BOOT_TIMEOUT)
    raw = bytes(c.raw)
    start = raw.find(b"e32: bare-metal")
    assert start >= 0, "banner not found"
    start = max(0, start - 2)               # the "\n" main() prints first
    body = raw[start:raw.rfind(b"\n") + 1]
    bad = [i for i in range(len(body)) if body[i] == 0x0a and (i == 0 or body[i - 1] != 0x0d)]
    assert not bad, f"{len(bad)} line(s) end in a bare LF, e.g. {body[max(0, bad[0]-40):bad[0]+1]!r}"


@step(R(r"the console echoes (?P<n>\d+) characters before the newline"))
def echo_count(world, n):
    c = get_console(world)
    c.wait_for("\n", since=since(world))
    echo = c.text(since(world)).split("\n", 1)[0].rstrip("\r")
    assert len(echo) == int(n), f"echoed {len(echo)} characters"


@step(R(r'the console shows at least (?P<n>\d+) lines alternating "(?P<a>[^"]*)" and "(?P<b>[^"]*)"'))
def alternating(world, n, a, b):
    lines = [l for l in get_console(world).lines(since(world)) if l in (a, b)]
    assert len(lines) >= int(n), f"only {len(lines)} lines of {a!r}/{b!r}"
    assert all(x != y for x, y in zip(lines, lines[1:])), f"not alternating: {lines}"


@step(R(r"the chip resets (?P<n>\d+) times within (?P<s>\d+) seconds"))
def chip_resets(world, n, s):
    # Counted as ROM reset banners ("rst:") in the transcript since boot,
    # the power-on one included.
    got = get_console(world).text(0).count("rst:")
    assert got == int(n), f"{got} reset banners within {s} s, expected {n}"


@step(R(r"the second tick count exceeds the first by at least (?P<n>\d+)"))
def tick_delta(world, n):
    d = world.data["ticks2"] - world.data["ticks1"]
    assert d >= int(n), f"ticks advanced by {d}"


@step(R(r'"irq 6" counts more than (?P<n>\d+) interrupts in total'))
def irq6_total(world, n):
    shows(world, "stress:", timeout=600)
    get_console(world).prompt(since=since(world), timeout=600)
    got = irq_count(world, 6)
    assert got > int(n), f"irq 6 count is {got}"


@step(R(r'"(?P<sym>\w+)" read with "r" is greater than (?P<n>\d+)'))
def symbol_greater(world, sym, n):
    addr = world.symbol(sym)
    enter_and_wait(world, f"r {addr}")
    assert last_value(world) > int(n)


@step(R(r"bits (?P<hi>\d+)\.\.(?P<lo>\d+) of the value are (?P<v>\d+) and bit (?P<b>\d+) is (?P<bv>[01])"))
def bits_field(world, hi, lo, v, b, bv):
    val = last_value(world)
    hi, lo = int(hi), int(lo)
    field = (val >> lo) & ((1 << (hi - lo + 1)) - 1)
    assert field == int(v) and (val >> int(b)) & 1 == int(bv), f"value {val:08x}"


@step(R(r"the value is (?P<hexval>[0-9a-f]{8})"))
def value_is(world, hexval):
    assert last_value(world) == int(hexval, 16), f"value {last_value(world):08x}"


@step(R(r"bit (?P<b>\d+) of the value is (?P<bv>[01])"))
def bit_is(world, b, bv):
    val = last_value(world)
    assert (val >> int(b)) & 1 == int(bv), f"value {val:08x}"


@step(R(r'the address of "(?P<sym>\w+)" from "xtensa-esp32-elf-nm e32\.elf"'))
def address_from_nm(world, sym):
    world.vars["that address"] = world.symbol(sym)


@step(R(r"every word except the one at (?P<addr>[0-9a-f]{8}) \((?P<what>[^,]+), (?P<val>[0-9a-f]{8})\) "
        r"is (?P<other>[0-9a-f]{8})"))
def dump_words(world, addr, what, val, other):
    c = get_console(world)
    c.prompt(since=since(world))
    words = {}
    for line in c.lines(since(world)):
        m = re.match(r"^([0-9a-f]{8}):((?: [0-9a-f]{8})+)$", line)
        if m:
            base = int(m.group(1), 16)
            for i, w in enumerate(m.group(2).split()):
                words[base + 4 * i] = w
    assert words, "no dump output"
    assert words.get(int(addr, 16)) == val, f"{addr} ({what}) is {words.get(int(addr, 16))}"
    bad = {f"{a:08x}": w for a, w in words.items() if a != int(addr, 16) and w != other}
    assert not bad, f"words not {other}: {bad}"
