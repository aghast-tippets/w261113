"""
Host-side steps: commands, the build, build variants, image and ELF
inspection, mkimage, documentation and the toolchain script.
All builds and commands run in the scenario's private copy of the tree.
"""
import filecmp
import os
import re
import shutil
import struct
import time
from pathlib import Path

import pytest
from pytest_bdd import parsers, step

import variants
from support import E32, ENV, World, needs_for_command, run

R = parsers.re
HEX = r"0x[0-9a-fA-F]+"


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def run_step_command(world: World, cmd, timeout=600):
    cmd = world.expand(cmd)
    needs_for_command(cmd)
    first = cmd.split()[0] if cmd.split() else ""
    if first == "./tools/mkimage":
        world.build_mkimage()
    # Inspection commands name build outputs the scenario assumes exist.
    if first.startswith("xtensa-esp32-elf-") and "e32.elf" in cmd \
            and not (world.tree / "e32.elf").exists():
        world.build("e32.elf")
    if first.startswith("esptool") and "image-info" in cmd and not (world.tree / "e32.bin").exists():
        world.build("e32.bin")
    if "build-toolchain.sh" in cmd:
        timeout = 4 * 3600
    return world.shell(cmd, timeout=timeout)


def last(world):
    assert world.result is not None, "no command has run in this scenario"
    return world.result


def objdump(world):
    if "objdump" not in world.data:
        ENV.need_cross()
        if not (world.tree / "e32.elf").exists():
            world.build("e32.elf")
        res = run(f"{ENV.cross_prefix}objdump -d e32.elf", world.tree)
        assert res.rc == 0, res.out
        world.data["objdump"] = res.out
    return world.data["objdump"]


INSN_RE = re.compile(r"^\s*([0-9a-f]+):\s+([0-9a-f]+)\s+(\S+)\s*(.*)$")
FUNC_RE = re.compile(r"^([0-9a-f]+) <([^>]+)>:$")


def instructions(dump, func=None):
    """[(addr, size, mnemonic, operands)] for the whole dump or one function."""
    out, cur = [], None
    for line in dump.splitlines():
        f = FUNC_RE.match(line)
        if f:
            cur = f.group(2)
            continue
        m = INSN_RE.match(line)
        if m and (func is None or cur == func):
            out.append((int(m.group(1), 16), len(m.group(2)) // 2, m.group(3), m.group(4)))
    return out


def nm_symbols(world):
    if "nm" not in world.data:
        ENV.need_cross()
        if not (world.tree / "e32.elf").exists():
            world.build("e32.elf")
        res = run(f"{ENV.cross_prefix}nm e32.elf", world.tree)
        assert res.rc == 0, res.out
        world.data["nm"] = {m.group(3): int(m.group(1), 16) for m in
                            re.finditer(r"^([0-9a-f]{8}) (\w) (\S+)$", res.out, re.M)}
    return world.data["nm"]


def link_line(world):
    for res in reversed(world.runs):
        for line in res.out.splitlines():
            if "-o e32.elf" in line:
                return line
    pytest.fail("no link command (\"-o e32.elf\") in this scenario's make output")


def image_segments(data):
    """Parse an ESP32 image: [(load_addr, bytes)], and the checksum offset."""
    assert data[0] == 0xE9, "bad magic"
    n, pos, segs = data[1], 24, []
    for _ in range(n):
        addr, length = struct.unpack_from("<II", data, pos)
        segs.append((addr, data[pos + 8:pos + 8 + length]))
        pos += 8 + length
    return segs, pos


def map_sections(world, prefix):
    """(name, addr, size) of input sections starting with prefix in e32.map,
    handling ld's wrapped lines."""
    text = (world.tree / "e32.map").read_text().splitlines()
    out = []
    for i, line in enumerate(text):
        m = re.match(rf"^\s*({re.escape(prefix)}\S*)(?:\s+0x([0-9a-f]+)\s+0x([0-9a-f]+))?", line)
        if not m:
            continue
        if m.group(2) is None and i + 1 < len(text):
            n = re.match(r"^\s+0x([0-9a-f]+)\s+0x([0-9a-f]+)", text[i + 1])
            if not n:
                continue
            addr, size = n.group(1), n.group(2)
        elif m.group(2) is None:
            continue
        else:
            addr, size = m.group(2), m.group(3)
        out.append((m.group(1), int(addr, 16), int(size, 16)))
    return out


def readme_has_topic(text, topic):
    """A heading, a table row, or a bold/colon lead-in naming the topic."""
    t = re.escape(topic)
    patterns = [rf"^#{{1,6}}\s.*{t}", rf"^\|.*{t}.*\|", rf"^\*\*{t}\b", rf"^{t}:"]
    return any(re.search(p, text, re.M | re.I) for p in patterns)


# --------------------------------------------------------------------------
# Preconditions and build
# --------------------------------------------------------------------------

@step("a clean checkout of e32")
def clean_checkout(world):
    assert not (world.tree / "e32.elf").exists()


@step("xtensa-esp32-elf-gcc is on the PATH")
def cross_on_path(world):
    ENV.need_cross()


@step("the firmware is built")
def firmware_built(world):
    world.build("all")


@step(R(r'"flash\.img" holds e32\.bin at offset 0x1000'))
def flash_img_holds(world):
    world.build("flash.img")
    img = (world.tree / "flash.img").read_bytes()
    binary = (world.tree / "e32.bin").read_bytes()
    assert img[0x1000:0x1000 + len(binary)] == binary


@step(R(r'"(?P<name>[^"]+)" exists'))
def file_made_to_exist(world, name):
    world.build(name)
    assert world.path(name).exists()


# --------------------------------------------------------------------------
# Build variants
# --------------------------------------------------------------------------

@step(R(r'a build variant with "(?P<old>[^"]+)" changed to "(?P<new>[^"]+)" in (?P<rel>\S+)'))
def variant_changed(world, old, new, rel):
    variants.replace_text(world.tree, rel, old, new)


@step(R(r'a build variant with "(?P<text>[^"]+)" added to (?P<rel>\S+)'))
def variant_added(world, text, rel):
    variants.add_text(world.tree, rel, text)


@step(R(r"a build variant with timer_init\((?P<hz>\d+)\)"))
@step(R(r"timer_init\((?P<hz>\d+)\) in main\.c"))
def variant_timer(world, hz):
    variants.timer_hz(world.tree, hz)


@step(R(r'a build variant with timer_init\((?P<hz>\d+)\) and the stress command "S"'))
def variant_timer_stress(world, hz):
    variants.timer_hz(world.tree, hz)
    variants.stress_command(world.tree)


@step(R(r'a build variant that counts entries to _alloca_handler and adds a command "S" running '
        r"2000 rounds of recurse\(200\) and vla_after_spill\(100 \+ i % 16\)"))
def variant_alloca_stress(world):
    variants.stress_command(world.tree, count_alloca=True)


@step(R(r"a build variant with RXBUF_SIZE set to (?P<n>\d+)"))
def variant_rxbuf(world, n):
    variants.rxbuf_size(world.tree, n)


@step(R(r'a build variant that arms the TG0 watchdog \(stage 0 = reset, 26,000,000 APB cycles\) '
        r'before "wdt_disable"'))
def variant_wdt_armed(world):
    variants.wdt_armed(world.tree, call_disable=True)


@step(R(r'a build variant that arms the TG0 watchdog and does not call "wdt_disable"'))
def variant_wdt_no_disable(world):
    variants.wdt_armed(world.tree, call_disable=False)


@step(R(r"a build variant (?P<what>that enables CPU line \d+ without a handler and raises it"
        r"|that prints the result of irq_request\(-?\d+, handler, 0\)"
        r"|whose panic_handler reads address 0 after its first line"
        r"|with an assembly routine that calls .+)"))
def variant_not_automated(world, what):
    pytest.fail(f"PENDING automation: build variant '{what}' is not implemented", pytrace=False)


# --------------------------------------------------------------------------
# Commands and their results
# --------------------------------------------------------------------------

@step(R(r'I run "(?P<cmd>[^"]*)"'))
@step(R(r'the (?:developer|maintainer) runs "(?P<cmd>[^"]*)"'))
def i_run(world, cmd):
    run_step_command(world, cmd)


@step(R(r'I touch "(?P<rel>[^"]+)" and run "(?P<cmd>[^"]*)"'))
def touch_and_run(world, rel, cmd):
    time.sleep(1.1)                        # make's timestamps have 1 s resolution on some filesystems
    os.utime(world.path(rel))
    run_step_command(world, cmd)


@step("the command succeeds")
def command_succeeds(world):
    res = last(world)
    assert res.rc == 0, f"{res.cmd!r} exited {res.rc}:\n{res.out[-3000:]}"


@step(R(r'the command fails with "(?P<msg>.*)"'))
def command_fails_with(world, msg):
    res = last(world)
    assert res.rc != 0, f"{res.cmd!r} succeeded"
    assert msg in res.out, f"{msg!r} not in output:\n{res.out[-3000:]}"


@step(R(r"the exit status is (?P<rc>\d+)"))
def exit_status(world, rc):
    res = last(world)
    assert res.rc == int(rc), f"{res.cmd!r} exited {res.rc}:\n{res.out}"


@step(R(r'the output contains "(?P<text>.*)"'))
def output_contains(world, text):
    res = last(world)
    assert text in res.out, f"{text!r} not in output of {res.cmd!r}:\n{res.out[-3000:]}"


@step(R(r'the output does not contain "(?P<text>.*)"'))
def output_lacks(world, text):
    res = last(world)
    if res.cmd.split()[0] == "make":
        # a build that stopped early proves nothing about warnings
        assert res.rc == 0, f"{res.cmd!r} exited {res.rc}:\n{res.out[-3000:]}"
    assert text not in res.out, f"{text!r} in output of {res.cmd!r}"


@step(R(r'the output of "(?P<cmd>[^"]*)" contains "(?P<text>.*)"'))
def output_of_contains(world, cmd, text):
    # "make" right after "make clean all" would print nothing (up to date):
    # the output of the scenario's latest make run is the one meant.
    res = None
    if cmd.split()[0] == "make":
        res = next((r for r in reversed(world.runs) if r.cmd.startswith("make")), None)
    if res is None:
        res = run_step_command(world, cmd)
    assert text in res.out, f"{text!r} not in output of {res.cmd!r}:\n{res.out[-3000:]}"


@step(R(r'the file "(?P<name>[^"]+)" exists'))
def file_exists(world, name):
    assert world.path(name).exists(), f"{name} does not exist"


@step(R(r"none of (?P<names>.+) exists"))
def none_exist(world, names):
    found = [n for n in re.findall(r'"([^"]+)"', names) if world.path(n).exists()]
    assert not found, f"still present: {found}"


@step(R(r'"(?P<a>[^"]+)" is identical to "(?P<b>[^"]+)"'))
def identical(world, a, b):
    assert filecmp.cmp(world.path(a), world.path(b), shallow=False)


@step(R(r'"(?P<name>docs/[^"]+)" is unchanged'))
def doc_unchanged(world, name):
    new, old = world.path(name), E32 / name
    assert new.read_text() == old.read_text(), \
        f"{name} differs from a fresh regeneration: run python3 tools/tracecheck.py and commit it"


# --------------------------------------------------------------------------
# Link, map and disassembly
# --------------------------------------------------------------------------

@step(R(r'the link command contains "(?P<flag>[^"]+)"'))
def link_contains(world, flag):
    assert flag in link_line(world).split()


@step("the only library on the link line is libgcc")
def only_libgcc(world):
    words = link_line(world).split()
    libs = [w for w in words if w.endswith(".a") or (w.startswith("-l") and w != "-lgcc")]
    assert libs and all(os.path.basename(w) == "libgcc.a" or w == "-lgcc" for w in libs), libs


@step(R(r'"e32\.map" lists no archive member from any library'))
def map_no_archive(world):
    text = (world.tree / "e32.map").read_text()
    members = re.findall(r"^\S+\.a\(\S+\.o\)", text, re.M)
    assert not members, f"archive members linked: {members}"


@step(R(r'"e32\.map" places \.rodata in DRAM'))
def rodata_in_dram(world):
    secs = [s for s in map_sections(world, ".rodata") if s[2] > 0]
    assert secs, "no .rodata input section in e32.map"
    bad = [s for s in secs if not 0x3FFB0000 <= s[1] <= 0x3FFDBFFF]
    assert not bad, f".rodata outside DRAM: {bad}"


@step(R(rf"no call or jump instruction targets an address from (?P<lo>{HEX}) to (?P<hi>{HEX})"))
def no_rom_calls(world, lo, hi):
    bad = rom_targets(world, int(lo, 16), int(hi, 16))
    assert not bad, "ROM targets:\n" + "\n".join(bad)


def rom_targets(world, lo, hi):
    """Direct calls, jumps and branches whose target lies in [lo, hi]."""
    bad = []
    for addr, _, mn, ops in instructions(objdump(world)):
        if mn.startswith(("call", "j")) or (mn.startswith("b") and not mn.startswith("break")):
            m = re.search(r"\b([0-9a-f]{8})\b(?: <[^>]*>)?\s*$", ops)
            if m and lo <= int(m.group(1), 16) <= hi:
                bad.append(f"{addr:08x}: {mn} {ops}")
    return bad


def _find(insns, start, rx):
    for i in range(start, len(insns)):
        addr, _, mn, ops = insns[i]
        if re.search(rx, f"{mn} {ops}"):
            return i
    return None


@step(R(r'the instruction "(?P<a>[^"]+)" appears in (?P<fn>\w+) before "(?P<b>[^"]+)"'))
def insn_before(world, a, fn, b):
    insns = instructions(objdump(world), fn)
    assert insns, f"function {fn} not found in the disassembly"
    rx_b = re.escape(b.split()[0]) + r"\s+.*<" + re.escape(b.split()[1]) + ">" if " " in b else re.escape(b)
    ia, ib = _find(insns, 0, rf"^{re.escape(a)}\b"), _find(insns, 0, rx_b)
    assert ia is not None and ib is not None and ia < ib, f"{a} at {ia}, {b} at {ib}"


@step(R(r'I disassemble "(?P<fn>\w+)"'))
def disassemble(world, fn):
    world.data["func"] = fn
    world.data["insns"] = instructions(objdump(world), fn)
    assert world.data["insns"], f"{fn} not found in the disassembly"


def _sr(name):
    return rf"^wsr\.{name}\b|^wsr\s+a\d+,\s*{name}\b"


# Each row of CMP-01-S01's table as a sequence of instruction patterns.
# The register values named in the table ("with 0x40080000") are not
# traced through literal pools: only the instructions and their order are.
ORDER_ROWS = {
    "wsr.intenable with 0": [_sr("intenable")],
    "wsr.windowstart with 1": [_sr("windowstart")],
    "wsr.windowbase with 0, then rsync": [_sr("windowbase"), r"^rsync\b"],
    "wsr.vecbase with 0x40080000, then rsync": [_sr("vecbase"), r"^rsync\b"],
    "a1 loaded with 0x3ffdc000": [r"^(?:l32r|movi(?:\.n)?)\s+a1,"],
    "wsr.ps with 0x00040020, then rsync": [_sr("ps"), r"^rsync\b"],
    "a loop storing zero from __bss_start to __bss_end": [r"^s32i(?:\.n)?\s", r"^(?:j|b\w+)\s"],
    "call4 wdt_disable": [r"^call4\s.*<wdt_disable>"],
    "call4 serial_setup": [r"^call4\s.*<serial_setup>"],
    "call4 main": [r"^call4\s.*<main>"],
}


@step("the instructions appear in this order:")
def insns_in_order(world, datatable):
    insns = world.data["insns"]
    pos = 0
    for (row,) in datatable[1:]:
        row = row.strip()
        if row == "a jump to itself":
            hit = next((i for i in range(pos, len(insns)) if insns[i][2] in ("j", "j.l")
                        and re.match(rf"^{insns[i][0]:x}\b", insns[i][3])), None)
            assert hit is not None, f"no self-jump after instruction {pos}"
            pos = hit + 1
            continue
        assert row in ORDER_ROWS, f"no pattern for table row {row!r}"
        for rx in ORDER_ROWS[row]:
            hit = _find(insns, pos, rx)
            assert hit is not None, f"{row!r}: /{rx}/ not found after instruction {pos} of {world.data['func']}"
            pos = hit + 1


@step(R(rf'the symbol "(?P<sym>\w+)" has the value (?P<val>{HEX})'))
def symbol_value(world, sym, val):
    syms = nm_symbols(world)
    assert syms.get(sym) == int(val, 16), f"{sym} = {syms.get(sym)!r}"


@step(R(r'the symbols "(?P<a>\w+)" and "(?P<b>\w+)" have the same value'))
def symbols_same(world, a, b):
    syms = nm_symbols(world)
    assert a in syms and b in syms and syms[a] == syms[b], f"{a}={syms.get(a)} {b}={syms.get(b)}"


@step(R(rf'the code for "(?P<vector>[^"]+)" starts at (?P<base>{HEX}) \+ (?P<off>{HEX})'))
def vector_starts(world, vector, base, off):
    start = int(base, 16) + int(off, 16)
    world.data["vector_start"] = start
    if re.match(r"^\w+$", vector):              # a real symbol
        syms = nm_symbols(world)
        assert syms.get(vector) == start, f"{vector} at {syms.get(vector)!r}, expected {start:#x}"
    # stubs have no symbol: there must be an instruction exactly there
    addrs = {a for a, *_ in instructions(objdump(world))}
    assert start in addrs, f"no instruction at {start:#x} for {vector}"


@step(R(rf"it ends before (?P<base>{HEX}) \+ (?P<nxt>{HEX})"))
def vector_ends(world, base, nxt):
    start, end = world.data["vector_start"], int(base, 16) + int(nxt, 16)
    inside = [(a, n) for a, n, *_ in instructions(objdump(world)) if start <= a < end]
    assert inside, "no code in the slot"
    assert all(a + n <= end for a, n in inside), f"an instruction crosses {end:#x}"


@step("every C object is compiled again")
def every_c_recompiled(world):
    out = last(world).out
    srcs = sorted(p.name for p in world.tree.glob("*.c"))
    missing = [s for s in srcs if not re.search(rf"\s-c {re.escape(s)}\b", out)]
    assert not missing, f"not recompiled: {missing}"


# --------------------------------------------------------------------------
# Images
# --------------------------------------------------------------------------

@step(R(r'the size of "(?P<name>[^"]+)" is (?P<n>\d+) bytes'))
def size_is(world, name, n):
    assert world.path(name).stat().st_size == int(n)


@step(R(r'the size of "(?P<name>[^"]+)" is a multiple of (?P<n>\d+)'))
def size_multiple(world, name, n):
    world.data["file"] = name
    assert world.path(name).stat().st_size % int(n) == 0


@step(R(rf'bytes (?P<off>{HEX}) onwards of "(?P<a>[^"]+)" equal "(?P<b>[^"]+)"'))
def bytes_equal(world, off, a, b):
    off = int(off, 16)
    img, binary = world.path(a).read_bytes(), world.path(b).read_bytes()
    world.data["region"] = (off, off + len(binary))
    assert img[off:off + len(binary)] == binary


@step(R(r'every other byte of "(?P<name>[^"]+)" is 0xff'))
def other_bytes_ff(world, name):
    img = world.path(name).read_bytes()
    lo, hi = world.data["region"]
    assert set(img[:lo]) <= {0xFF} and set(img[hi:]) <= {0xFF}


@step(R(r'I read byte (?P<off>\d+) of "(?P<name>[^"]+)"'))
def read_byte(world, off, name):
    world.data["byte"] = world.path(name).read_bytes()[int(off)]


@step(R(rf"its value is (?P<val>{HEX})"))
def byte_value(world, val):
    assert world.data["byte"] == int(val, 16), f"byte is {world.data['byte']:#04x}"


@step(R(r"its last byte equals 0xef XOR every segment data byte"))
def checksum_ok(world):
    data = world.path(world.data.get("file", "e32.bin")).read_bytes()
    segs, _ = image_segments(data)
    ck = 0xEF
    for _, body in segs:
        for b in body:
            ck ^= b
    assert data[-1] == ck, f"last byte {data[-1]:#04x}, checksum {ck:#04x}"


@step(R(rf'segment (?P<n>\d+) is loaded at (?P<addr>{HEX}) with memory type "(?P<kind>\w+)"'))
def esptool_segment(world, n, addr, kind):
    out = last(world).out
    rx = rf"^\s*(?:Segment\s+)?{n}\b[:\s].*\b{addr[2:]}\b.*\b{kind}\b"
    assert re.search(rx, out, re.M | re.I), f"segment {n} at {addr} [{kind}] not in:\n{out}"


@step(R(rf"every segment lies in (?P<a>{HEX})-(?P<b>{HEX}) or (?P<c>{HEX})-(?P<d>{HEX})"))
def segments_in_sram(world, a, b, c, d):
    segs, _ = image_segments((world.tree / "e32.bin").read_bytes())
    ranges = [(int(a, 16), int(b, 16)), (int(c, 16), int(d, 16))]
    for addr, body in segs:
        end = addr + len(body) - 1
        assert any(lo <= addr and end <= hi for lo, hi in ranges), f"segment {addr:#x}-{end:#x}"


@step(R(rf"no source refers to (?P<a>{HEX})-(?P<b>{HEX}) or (?P<c>{HEX})-(?P<d>{HEX})"))
def no_source_refs(world, a, b, c, d):
    ranges = [(int(a, 16), int(b, 16)), (int(c, 16), int(d, 16))]
    hits = []
    for pat in ("*.c", "*.S", "*.lds", "include/*.h"):
        for p in world.tree.glob(pat):
            for m in re.finditer(r"\b0x([0-9a-fA-F]{8})\b", p.read_text()):
                v = int(m.group(1), 16)
                if any(lo <= v <= hi for lo, hi in ranges):
                    hits.append(f"{p.name}: {m.group(0)}")
    assert not hits, hits


# --------------------------------------------------------------------------
# mkimage: crafted ELF files
# --------------------------------------------------------------------------

def craft_elf(kind):
    """A minimal 32-bit LE Xtensa (EM 94) ELF with the named defect."""
    def ehdr(phnum):
        ident = b"\x7fELF" + bytes([1, 1, 1]) + bytes(9)
        return ident + struct.pack("<HHIIIIIHHHHHH", 2, 94, 1, 0x40080000, 52, 0, 0,
                                   52, 32, phnum, 40, 0, 0)

    def phdr(off, addr, filesz, memsz):
        return struct.pack("<IIIIIIII", 1, off, addr, addr, filesz, memsz, 5, 4)

    if kind == "many":
        n = 17
        data_off = 52 + 32 * n
        phs = b"".join(phdr(data_off + 4 * i, 0x3FFB0000 + 4 * i, 4, 4) for i in range(n))
        return ehdr(n) + phs + bytes(range(4 * n))
    if kind == "none":
        return ehdr(1) + phdr(0, 0x3FFB0000, 0, 64)
    if kind == "truncated":
        return ehdr(1) + phdr(84, 0x3FFB0000, 4096, 4096) + b"\0" * 16
    raise AssertionError(kind)


DEFECTS = {
    "17 PT_LOAD segments with contents": "many",
    "no PT_LOAD segment with file contents": "none",
    "a segment extending past the end of file": "truncated",
}


@step(R(r'an Xtensa ELF file "(?P<name>[^"]+)" crafted with (?P<defect>.+)'))
def crafted_elf(world, name, defect):
    assert defect in DEFECTS, f"unknown defect {defect!r}"
    world.path(name).write_bytes(craft_elf(DEFECTS[defect]))


# --------------------------------------------------------------------------
# Documentation
# --------------------------------------------------------------------------

@step(R(r'I read "(?P<name>[^"]+)"'))
@step(R(r"the learner reads (?P<name>README\.md)"))
def read_doc(world, name):
    world.data["doc"] = (E32 / name).read_text()


@step(R(r'it has a section or table about "(?P<topic>[^"]+)"'))
def has_topic(world, topic):
    assert readme_has_topic(world.data["doc"], topic), f"no section, table or lead-in about {topic!r}"


@step("boot, memory map, vectors, interrupts, faults and the LPC1343 mapping are explained")
def readme_explains(world):
    doc = world.data["doc"]
    topics = ["How it boots", "Memory map", "Interrupts and faults", "LPC1343 equivalent"]
    missing = [t for t in topics if not readme_has_topic(doc, t)]
    if not re.search(r"^\|\s*Offset\s*\|\s*Vector\s*\|", doc, re.M):
        missing.append("vector table")
    if not re.search(r"\bfault", doc, re.I):
        missing.append("faults")
    assert not missing, f"README does not explain: {missing}"


@step(R(r"it reports (?P<n>\d+) errors"))
def reports_errors(world, n):
    res = last(world)
    assert re.search(rf"\b{n} errors\b", res.out), res.out
    if int(n) == 0:
        assert res.rc == 0


# --------------------------------------------------------------------------
# Toolchain script
# --------------------------------------------------------------------------

@step("a Linux host with git, gcc, g++, make, flex, bison, texinfo and the GMP, MPFR and MPC headers")
def toolchain_host(world):
    tools = ["git", "gcc", "g++", "make", "flex", "bison", "makeinfo"]
    missing = [t for t in tools if not shutil.which(t)]
    inc = [Path("/usr/include"), Path("/usr/local/include")]
    missing += [h for h in ("gmp.h", "mpfr.h", "mpc.h") if not any((d / h).exists() for d in inc)]
    if missing and not ENV.force:
        pytest.skip(f"toolchain build prerequisites missing: {missing}")


@step(R(r'an empty directory "(?P<d>[^"]+)"'))
def empty_dir(world, d):
    p = world.path(d)
    shutil.rmtree(p, ignore_errors=True)
    p.mkdir(parents=True)


@step(R(r'the script has completed once in "(?P<d>[^"]+)"'))
def script_completed_once(world, d):
    res = run_step_command(world, f"PREFIX=/tmp/tc WORK={d} tools/build-toolchain.sh")
    assert res.rc == 0, res.out[-3000:]
