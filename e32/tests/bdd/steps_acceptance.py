"""
Stakeholder acceptance steps (acceptance.feature): actor-phrased steps,
mostly composed from the console and build helpers.
"""
import re
import shutil
import time

import pytest
from pytest_bdd import parsers, step

import qemu_console as qc
import variants
from steps_build import link_line, rom_targets, run_step_command
from steps_console import (board_ready, boot_qemu_flash, connect_tcp, enter, enter_and_wait,
                           esptool_load_ram, get_console, irq_count, manual, set_mark, shows,
                           shows_line, since, start_download_qemu)

from support import ENV, World, run

R = parsers.re
FREESTANDING = {"stddef.h", "stdarg.h", "stdint.h", "stdbool.h", "limits.h", "float.h",
                "iso646.h", "stdalign.h", "stdnoreturn.h"}


def use_qemu():
    """@qemu @hardware scenarios run in QEMU when it is there, else on the board."""
    return bool(ENV.qemu and ENV.cross_gcc) or (ENV.force and not ENV.port)


def flash_board(world: World):
    ENV.need_board()
    res = world.shell("make flash PORT=/dev/ttyUSB0", timeout=300)
    assert res.rc == 0, res.out[-3000:]
    board_ready(world)


@step("a host with xtensa-esp32-elf-gcc, make and cc only")
def bare_host(world):
    ENV.need_cross()
    assert shutil.which("make") and ENV.hostcc, "make and cc are required"


@step("e32.elf and e32.bin are produced without warnings")
def produced_without_warnings(world):
    res = world.result
    assert res.rc == 0, res.out[-3000:]
    assert (world.tree / "e32.elf").exists() and (world.tree / "e32.bin").exists()
    assert "warning" not in res.out.lower(), "warnings in the build output"


@step("the inspection shows no SDK, no libc and no ROM routine in use")
def inspection(world):
    words = link_line(world).split()
    assert "-nostdlib" in words
    libs = [w for w in words if w.endswith(".a") or w.startswith("-l")]
    assert all(w.endswith("libgcc.a") or w == "-lgcc" for w in libs), libs
    includes = set()
    for pat in ("*.c", "*.S", "include/*.h"):
        for p in world.tree.glob(pat):
            includes |= set(re.findall(r"#include\s*<([^>]+)>", p.read_text()))
    assert includes <= FREESTANDING, f"non-freestanding headers: {includes - FREESTANDING}"
    rom = rom_targets(world, 0x40000000, 0x4006FFFF)
    assert not rom, f"calls into ROM: {rom}"


@step(R(r'the maintainer runs "tools/build-toolchain\.sh" in an empty directory'))
def maintainer_builds_toolchain(world):
    (world.tmp / "w").mkdir(exist_ok=True)
    res = run_step_command(world, "PREFIX=/tmp/tc WORK=/tmp/w tools/build-toolchain.sh")
    assert res.rc == 0, res.out[-3000:]


@step("the resulting compiler builds e32 without warnings")
def resulting_compiler_builds(world):
    res = run_step_command(world, "make clean all CROSS_COMPILE=/tmp/tc/bin/xtensa-esp32-elf-")
    assert res.rc == 0 and "warning" not in res.out, res.out[-3000:]


@step(R(r'the developer runs "make ram" with the board in download mode'))
def developer_make_ram(world):
    if use_qemu():
        start_download_qemu(world)
        esptool = world.make_env().get("ESPTOOL", "esptool")
        res = world.shell(f'make ram PORT=socket://localhost:5556 '
                          f'ESPTOOL="{esptool} --before no-reset --after no-reset"', timeout=120)
        assert res.rc == 0, res.out[-3000:]
        connect_tcp(world)
    else:
        ENV.need_board()
        res = world.shell("make ram PORT=/dev/ttyUSB0", timeout=120)
        assert res.rc == 0, res.out[-3000:]
        from steps_console import open_board
        open_board(world, reset=False)
        world.data["mark"] = 0


@step(R(r'the developer runs "make flash" and resets the board'))
def developer_make_flash(world):
    if use_qemu():
        boot_qemu_flash(world)
    else:
        flash_board(world)


@step("the monitor prompt appears after every reset")
def prompt_after_every_reset(world):
    for _ in range(2):
        get_console(world).prompt(timeout=qc.BOOT_TIMEOUT, since=since(world))
        if use_qemu():
            boot_qemu_flash(world)          # a reset in QEMU: power the machine up again
        else:
            board_ready(world)
    get_console(world).prompt(timeout=qc.BOOT_TIMEOUT, since=since(world))


@step("the operator opens a terminal at 115200 8N1 and resets the board")
def operator_terminal(world):
    boot_qemu_flash(world)                  # QEMU ignores the line settings


@step(R(r'the banner and "> " are shown'))
def banner_and_prompt(world):
    shows(world, "e32: bare-metal ESP32", timeout=qc.BOOT_TIMEOUT)
    get_console(world).prompt(timeout=qc.BOOT_TIMEOUT)


@step(R(r"the operator pastes (?P<n>\d+) commands while the self test runs"))
def paste_during_self_test(world, n):
    enter(world, "s")
    world.data["pasted"] = int(n)
    get_console(world).send(b"r 3ffb1000\r" * int(n))


@step(R(r"all (?P<n>\d+) are answered"))
def all_answered(world, n):
    c = get_console(world)
    c.wait_count("read 3ffb1000", int(n), since=since(world))
    c.quiet(0.5)
    assert c.text(since(world)).count("read 3ffb1000") == int(n)


@step(R(r'the operator enters (?P<cmds>"[^"]*"(?:, "[^"]*")* and "[^"]*")'))
def operator_enters_many(world, cmds):
    answers = {}
    for cmd in re.findall(r'"([^"]*)"', cmds):
        cmd = world.expand(cmd)
        m = enter_and_wait(world, cmd)
        answers[cmd] = get_console(world).text(m).replace("\r", "")
    world.data["answers"] = answers


@step(R(r'the operator enters "(?P<cmd>[^"]*)"'))
@step(R(r'the developer enters "(?P<cmd>[^"]*)"'))
def actor_enters(world, cmd):
    enter(world, world.expand(cmd))


@step(R(r'the operator enters "s" and then "i"'))
def enters_s_then_i(world):
    enter_and_wait(world, "s")
    enter_and_wait(world, "i")              # later checks look at the "i" output


@step("each command answers in its documented format")
def documented_format(world):
    checks = {
        "h": [r"r <addr>", r"w <addr> <value>"],
        "w": [r"write [0-9a-f]{8} = [0-9a-f]{8}"],
        "r": [r"read [0-9a-f]{8}\n[0-9a-f]{8}"],
        "d": [r"(?m)^[0-9a-f]{8}:( [0-9a-f]{8}){4}$"],
        "g": [r"go [0-9a-f]{8}"],
    }
    for cmd, out in world.data["answers"].items():
        for rx in checks.get(cmd[0], []):
            assert re.search(rx, out), f"{cmd!r}: /{rx}/ not in {out!r}"
    d = next(out for cmd, out in world.data["answers"].items() if cmd.startswith("d "))
    assert len(re.findall(r"(?m)^[0-9a-f]{8}:( [0-9a-f]{8}){4}$", d)) == 4


@step("the command is refused")
def command_refused(world):
    shows(world, "invalid gpio")


@step("the blink build is flashed")
@step("the blink build is flashed to a board with an LED on GPIO2")
def blink_flashed(world):
    variants.blink(world.tree)
    flash_board(world)


@step("the software interrupt handler ran once")
def soft_irq_once(world):
    txt = get_console(world).text(0)
    assert "software irq:      1 hit (ok)" in txt
    assert re.search(r"(?m)^irq  7: 1\r?$", txt), "irq 7 count is not 1"


@step(R(r"lines (?P<a>\d+) and (?P<b>\d+) are counting"))
def lines_counting(world, a, b):
    for n in (int(a), int(b)):
        shows_line(world, rf"^irq {n:2d}: [1-9]\d*$")


@step(R(r'the report names "(?P<name>\w+)" and the PC maps to (?P<fn>\w+)\(\) in (?P<src>\S+)'))
def report_and_pc(world, name, fn, src):
    shows(world, name)
    res = run_step_command(world, "xtensa-esp32-elf-addr2line -f -e e32.elf <pc>")
    assert fn in res.out and src in res.out, res.out


@step(R(r'the board reboots with "(?P<text>[^"]+)"'))
def reboots_with(world, text):
    shows(world, text, timeout=qc.BOOT_TIMEOUT)


@step(R(r'deep recursion and the variable-length array both report "(?P<word>\w+)"'))
def recursion_and_vla(world, word):
    shows_line(world, rf"^recursion 200 deep: \d+ \({word}\)$")
    shows_line(world, rf"^VLA after spill: +\d+ \({word}\)$")


@step(R(r'the tester runs "make qemu" and enters "s" and "f 0" to "f 5"'))
def make_qemu_self_test_and_faults(world):
    ENV.need_cross()
    ENV.need_qemu()
    world.build("e32.bin")
    from steps_console import _fresh, qemu_env
    _fresh(world, qc.ProcessConsole(["make", "qemu"], world.tree, env=qemu_env(world), name="make qemu"))
    m = enter_and_wait(world, "s")
    world.data["self_test"] = get_console(world).text(m)
    failures = []
    for n in range(6):
        c = get_console(world)
        m = enter(world, f"f {n}")
        try:
            c.wait_for("Press any key to reboot", since=m)
            k = c.mark()
            c.send(b" ")
            c.wait_for("rst:0x3 (SW_RESET)", since=k, timeout=qc.BOOT_TIMEOUT)
            c.prompt(since=k, timeout=qc.BOOT_TIMEOUT)
            world.data["prompt_since"] = c.mark()
            report = c.text(m)
            if "***" not in report:
                failures.append(f"f {n}: no report heading")
        except qc.ConsoleTimeout as exc:
            failures.append(f"f {n}: {str(exc).splitlines()[0]}")
    world.data["fault_failures"] = failures
    world.data["mark"] = 0


@step(R(r'the self test reports "(?P<text>[^"]+)"'))
def self_test_reports(world, text):
    if "self_test" in world.data:
        assert text in world.data["self_test"], world.data["self_test"]
    else:
        shows(world, text)


@step("every fault is reported and followed by a reboot")
def faults_reboot(world):
    assert not world.data["fault_failures"], world.data["fault_failures"]


@step("an ESP32-WROOM-32 DevKit without PSRAM")
def devkit(world):
    ENV.need_board()            # the board model itself is the operator's word


@step(R(r'the developer flashes e32 and enters "(?P<cmd>[^"]*)"'))
def flashes_and_enters(world, cmd):
    flash_board(world)
    enter(world, cmd)


@step("the firmware is flashed to an ESP32-WROOM-32 DevKit without PSRAM")
def flashed_to_devkit(world):
    flash_board(world)
