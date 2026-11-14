# Verification and test requirements (VER)

How is each requirement proven met, and at what level? Each entry names
exactly one TAID method:

* **T**est
* **A**nalysis
* **I**nspection
* **D**emonstration

Each entry also gives the level and environment, the procedure, the
evidence, the pass criteria, and the current status (see
[`../README.md`](../README.md#verification-status)).

Evidence written as `@VER-…` refers to the Gherkin scenarios in
[`../features/`](../features/) that carry that tag.

**Environments:**

* **Host:** the build machine.
* **QEMU:** Espressif QEMU `esp-develop-9.2.2-20261109`, machine `esp32`,
  with the real boot ROM "ets Jul 29 2019" (rev 3).
* **Board:** a physical ESP32 board, which no test has used yet.

**Caution:** the QEMU results below were obtained before the host-build
seams were added to the sources (`E32_HOST` in `types.h` and `xtensa.h`,
and the `cpu_*()` macros). Those seams should not change the target code,
but the target has not been rebuilt since. Re-run the QEMU procedures with
a fresh build before relying on them.

Host results dated 2026-11-14 come from `tests/run_all.sh`; see
[`../test-results.md`](../test-results.md).

All results marked Passed were obtained on 2026-11-14, with the toolchain
built from `esp-2.47.0_20261109` and `esp-14.4.0_20261030`.

---

## Business level

### VER-BR-01 — Size and learnability analysis
- **Type:** Verification
- **Verifies:** BR-01
- **Method:** Analysis
- **Level:** Business
- **Environment:** Host
- **Procedure:** Count lines with `wc -l *.c *.S *.lds include/*.h tools/mkimage.c tools/build-toolchain.sh Makefile`, and check that the README's file table names every source file.
- **Evidence:** Line count recorded in the traceability report; README file table.
- **Pass criteria:** At most 2,500 lines, and every source file has a stated purpose.
- **Status:** Partial. The size KPI is met (see the traceability summary). Comprehension by real learners has not been assessed yet.

### VER-BR-02 — Dependency inventory
- **Type:** Verification
- **Verifies:** BR-02
- **Method:** Inspection
- **Level:** Business
- **Environment:** Host
- **Procedure:** Inspect the Makefile and the link map (`e32.map`) for linked libraries. Inspect `objdump -d e32.elf` for any `call`/`j` into `0x40000000`–`0x4006FFFF`. List all tools that the build and load steps need.
- **Evidence:** The link map shows no library members pulled in (libgcc is on the link line but supplies nothing); no branch targets the ROM; the tools are gcc, binutils, make, cc and esptool.
- **Pass criteria:** The inventory matches the KPI of BR-02.
- **Status:** Passed (Host).

### VER-BR-03 — Memory budget analysis
- **Type:** Verification
- **Verifies:** BR-03
- **Method:** Analysis
- **Level:** Business
- **Environment:** Host
- **Procedure:** Run `xtensa-esp32-elf-size e32.elf`, and compare it with the IRAM (128 KB) and DRAM (176 KB) regions in `esp32.lds`.
- **Evidence:** text 5,908 B (4.5 % of IRAM); data 2,324 B + bss 2,880 B (2.9 % of DRAM, excluding the stack).
- **Pass criteria:** IRAM and DRAM use each at most 50 %, with no external memory.
- **Status:** Passed (Host).

### VER-BR-04 — Extensibility demonstration
- **Type:** Verification
- **Verifies:** BR-04
- **Method:** Demonstration
- **Level:** Business
- **Environment:** QEMU
- **Procedure:** Show that new interrupt-driven behaviour works with no change to `boot.S` or `vectors.S`: the self test's software-interrupt handler, the UART receive handler and the tick are all attached through `irq_request` and `irq_map` only.
- **Evidence:** @VER-BR-04
- **Pass criteria:** The handlers run, and `git diff`/inspection shows no startup or vector change needed for them.
- **Status:** Passed (QEMU).

### VER-BR-05 — Emulator coverage analysis
- **Type:** Verification
- **Verifies:** BR-05
- **Method:** Analysis
- **Level:** Business
- **Environment:** Host
- **Procedure:** `tools/tracecheck.py` computes the share of `SYS` requirements for which at least one verifying `VER` entry has an environment including QEMU or Host.
- **Evidence:** The "Emulator/host coverage" line in `../traceability.md`.
- **Pass criteria:** At least 80 %.
- **Status:** Passed (Host). See the computed figure in the traceability summary.

### VER-BR-06 — Originality inspection
- **Type:** Verification
- **Verifies:** BR-06
- **Method:** Inspection
- **Level:** Business
- **Environment:** Host
- **Procedure:** Review every file in the tree for third-party origin. The window spill and fill sequences are the forms the Xtensa ISA defines, and are written from that definition.
- **Evidence:** The VER-SYS-23 result.
- **Pass criteria:** No third-party source in the firmware or tools.
- **Status:** Partial. The author's inspection is complete; an independent review is recommended before any release.

## Stakeholder level (acceptance)

### VER-STK-01 — Acceptance: SDK-free build
- **Type:** Verification
- **Verifies:** STK-01, STK-18
- **Method:** Demonstration
- **Level:** Stakeholder
- **Environment:** Host
- **Procedure:** On a host with only the bare toolchain, run `make clean all` and show the outputs, the dependency inventory and the absence of ROM calls.
- **Evidence:** @VER-STK-01
- **Pass criteria:** Both outputs are produced; no SDK, libc or ROM routine is used.
- **Status:** Passed (Host).

### VER-STK-02 — Acceptance: toolchain reproduction
- **Type:** Verification
- **Verifies:** STK-02
- **Method:** Demonstration
- **Level:** Stakeholder
- **Environment:** Host
- **Procedure:** Run `tools/build-toolchain.sh` in an empty work directory, then build e32 with the result.
- **Evidence:** @VER-STK-02
- **Pass criteria:** The script exits 0, and the firmware builds without warnings.
- **Status:** Partial. The toolchain used for every test was built with the same sources, overlay and configure options by hand. The script itself has not been run end to end.

### VER-STK-03 — Acceptance: both load paths
- **Type:** Verification
- **Verifies:** STK-03, STK-04
- **Method:** Demonstration
- **Level:** Stakeholder
- **Environment:** QEMU, Board
- **Procedure:** Show `make ram` and `make flash` on a board, and the equivalent paths in QEMU.
- **Evidence:** @VER-STK-03
- **Pass criteria:** The monitor prompt appears after each path; after `make flash` it also appears after a reset.
- **Status:** Partial. Both paths pass in QEMU (load-ram over TCP; flash image at `0x1000`). Board pending.

### VER-STK-04 — Acceptance: console
- **Type:** Verification
- **Verifies:** STK-05, STK-19
- **Method:** Demonstration
- **Level:** Stakeholder
- **Environment:** QEMU, Board
- **Procedure:** Connect a terminal at 115200 8N1, show the banner and prompt, and paste 20 commands while the self test runs.
- **Evidence:** @VER-STK-04
- **Pass criteria:** The banner is readable, and all 20 pasted commands are answered.
- **Status:** Partial. Passed in QEMU (20 of 20 answered). Board pending.

### VER-STK-05 — Acceptance: memory monitor
- **Type:** Verification
- **Verifies:** STK-06
- **Method:** Demonstration
- **Level:** Stakeholder
- **Environment:** QEMU
- **Procedure:** Run a session with `h`, `r`, `w`, `d`, `g`, one malformed line and one unaligned address.
- **Evidence:** @VER-STK-05
- **Pass criteria:** The outputs match SW-MON-02, and errors give `?? (h for help)`.
- **Status:** Passed (QEMU).

### VER-STK-06 — Acceptance: pins and blink
- **Type:** Verification
- **Verifies:** STK-07, STK-16
- **Method:** Demonstration
- **Level:** Stakeholder
- **Environment:** Board
- **Procedure:** On a board, drive GPIO2 with `p 2 1` and `p 2 0` and watch the LED or a meter, read a jumpered input, try `p 7 1` and `p 36 1`, and flash the blink build.
- **Evidence:** @VER-STK-06
- **Pass criteria:** The LED follows the commands, the refusals are printed, and the blink build blinks at about 1 Hz.
- **Status:** Pending (hardware). The refusals and the blink console output already pass in QEMU (VER-SYS-10, VER-SYS-18).

### VER-STK-07 — Acceptance: interrupts and time base
- **Type:** Verification
- **Verifies:** STK-08, STK-09
- **Method:** Demonstration
- **Level:** Stakeholder
- **Environment:** QEMU
- **Procedure:** Show `s` (software-interrupt handler attached at run time) and `i` (tick and UART counts rising).
- **Evidence:** @VER-STK-07
- **Pass criteria:** The self test says `ok` for the soft irq and the ticks; `i` shows lines 6 and 17 counting.
- **Status:** Passed (QEMU).

### VER-STK-08 — Acceptance: crash report and reboot
- **Type:** Verification
- **Verifies:** STK-10
- **Method:** Demonstration
- **Level:** Stakeholder
- **Environment:** QEMU, Board
- **Procedure:** Run `f 0`, read the report, map the PC with `addr2line`, and press a key.
- **Evidence:** @VER-STK-08
- **Pass criteria:** The report names `LoadProhibited`, `addr2line` points to `mimmo.c` `fault()`, and the chip reboots with `rst:0x3`.
- **Status:** Partial. Passed in QEMU. Board pending.

### VER-STK-09 — Acceptance: ordinary C semantics
- **Type:** Verification
- **Verifies:** STK-11
- **Method:** Demonstration
- **Level:** Stakeholder
- **Environment:** QEMU
- **Procedure:** Run `s` and show the recursion and VLA results.
- **Evidence:** @VER-STK-09
- **Pass criteria:** `recursion 200 deep: 20100 (ok)` and `VLA after spill: 919 (ok)`.
- **Status:** Passed (QEMU).

### VER-STK-10 — Acceptance: stays up
- **Type:** Verification
- **Verifies:** STK-12
- **Method:** Demonstration
- **Level:** Stakeholder
- **Environment:** Board
- **Procedure:** Boot from flash on a board and leave it idle at the prompt for 10 minutes.
- **Evidence:** @VER-STK-10
- **Pass criteria:** No ROM boot lines appear after the first boot.
- **Status:** Partial. In QEMU (where the power-on watchdog isn't armed) a test build that arms the TG0 watchdog shows `wdt_disable()` stops it. Board pending.

### VER-STK-11 — Acceptance: emulator and self test
- **Type:** Verification
- **Verifies:** STK-13, STK-14
- **Method:** Demonstration
- **Level:** Stakeholder
- **Environment:** QEMU
- **Procedure:** Run `make qemu`, then `s` and `f 0` to `f 5`, and run the download-mode load.
- **Evidence:** @VER-STK-11
- **Pass criteria:** The self test says `all ok`; each fault gives a report and reboots.
- **Status:** Passed (QEMU).

### VER-STK-12 — Acceptance: documentation and traceability
- **Type:** Verification
- **Verifies:** STK-15, STK-20
- **Method:** Inspection
- **Level:** Stakeholder
- **Environment:** Host
- **Procedure:** A reader checks the README against the SYS-28 topics, and runs `python3 tools/tracecheck.py --check`.
- **Evidence:** @VER-STK-12
- **Pass criteria:** Every topic is present, and the check exits 0.
- **Status:** Passed (Host).

### VER-STK-13 — Acceptance: basic board
- **Type:** Verification
- **Verifies:** STK-17
- **Method:** Demonstration
- **Level:** Stakeholder
- **Environment:** Board
- **Procedure:** Flash an ESP32-WROOM-32 DevKit without PSRAM, and run `s`.
- **Evidence:** @VER-STK-13
- **Pass criteria:** `all ok`.
- **Status:** Pending (hardware).

## System level

### VER-SYS-01 — Build test
- **Type:** Verification
- **Verifies:** SYS-01, SYS-02, SYS-03
- **Method:** Test
- **Level:** System
- **Environment:** Host
- **Procedure:** Run `make clean && make 2>&1 | tee log`; check the outputs, look for "warning" in the log and confirm the size line; inspect the link line.
- **Evidence:** @VER-SYS-01
- **Pass criteria:** Both files exist, there are 0 warnings, a size line is printed, and only gcc, binutils, libgcc, make and cc are used.
- **Status:** Passed (Host).

### VER-SYS-02 — Flash boot test
- **Type:** Verification
- **Verifies:** SYS-04
- **Method:** Test
- **Level:** System
- **Environment:** QEMU, Board
- **Procedure:** Boot `flash.img` (image at `0x1000`), and capture the ROM lines and the banner.
- **Evidence:** @VER-SYS-02
- **Pass criteria:** The ROM prints `load:0x3ffb0000`, `load:0x40080000` and `entry 0x400803dc` (or the current entry), followed by the banner.
- **Status:** Partial. Passed in QEMU. Board pending.

### VER-SYS-03 — RAM boot test
- **Type:** Verification
- **Verifies:** SYS-05, SYS-27
- **Method:** Test
- **Level:** System
- **Environment:** QEMU, Board
- **Procedure:** Start QEMU in download mode with the console on TCP, run `esptool --no-stub load-ram e32.bin` against it, then run `s`. On a board, run `make ram`.
- **Evidence:** @VER-SYS-03
- **Pass criteria:** esptool reports "Loaded 2 segments … executing", and `s` gives `all ok`.
- **Status:** Partial. Passed in QEMU using esptool directly. `make ram` against a board is pending.

### VER-SYS-04 — Flash and RAM targets on a board
- **Type:** Verification
- **Verifies:** SYS-26, SYS-27
- **Method:** Test
- **Level:** System
- **Environment:** Board
- **Procedure:** Run `make flash`, then reset and check the banner; read back with `esptool read_flash 0x1000 <len>` and compare with `e32.bin`. Then run `make ram`.
- **Evidence:** @VER-SYS-04
- **Pass criteria:** The read-back is identical (header unchanged), and both paths reach the prompt.
- **Status:** Pending (hardware).

### VER-SYS-05 — No ROM code at run time
- **Type:** Verification
- **Verifies:** SYS-08
- **Method:** Inspection
- **Level:** System
- **Environment:** Host
- **Procedure:** Inspect `objdump -d e32.elf` for `call*`/`j` targets in `0x40000000`–`0x4006FFFF`, and confirm that `call_start` writes `VECBASE` before its first call.
- **Evidence:** @VER-SYS-05
- **Pass criteria:** No ROM targets, and `VECBASE` is set before `call4 wdt_disable`.
- **Status:** Passed (Host).

### VER-SYS-06 — Banner and serial parameters
- **Type:** Verification
- **Verifies:** SYS-06, SYS-07
- **Method:** Test
- **Level:** System
- **Environment:** QEMU, Board
- **Procedure:** Boot and capture UART0. On a board, use a terminal at 115200 8N1.
- **Evidence:** @VER-SYS-06
- **Pass criteria:** The banner, memory line, ready line and `> ` appear in order and are readable at 115200 8N1.
- **Status:** Partial. Passed in QEMU (QEMU does not model the baud rate). Board pending.

### VER-SYS-07 — Watchdog test
- **Type:** Verification
- **Verifies:** SYS-09
- **Method:** Test
- **Level:** System
- **Environment:** QEMU, Board
- **Procedure:** In QEMU, run a test build that arms the TG0 watchdog (stage 0 = system reset, about 0.65 s) before startup proceeds, with and without `wdt_disable()`, and count the resets in 6 s. On a board, idle for 10 minutes after a flash boot.
- **Evidence:** @VER-SYS-07
- **Pass criteria:** With `wdt_disable()`: 1 boot. Without it: repeated resets in the QEMU variant. On the board: no reset.
- **Status:** Partial. QEMU: with disable, 1 boot; without, 6 boots in 6 s. The RTC watchdog (not modelled by QEMU) and the board are pending.

### VER-SYS-08 — Monitor command test
- **Type:** Verification
- **Verifies:** SYS-10, SYS-11, SYS-31
- **Method:** Test
- **Level:** System
- **Environment:** QEMU
- **Procedure:** Enter every command form from monitor.feature, including the malformed ones.
- **Evidence:** @VER-SYS-08
- **Pass criteria:** The output matches each scenario exactly.
- **Status:** Passed (QEMU). Executed by hand: `h`, `r`, `w`, `d`, `g`, `p`, `a`, `i`, `s` and `f`, unknown commands, missing arguments and unaligned addresses. Automation pending.

### VER-SYS-09 — GPIO drive and read on hardware
- **Type:** Verification
- **Verifies:** SYS-12, SYS-13
- **Method:** Test
- **Level:** System
- **Environment:** Board
- **Procedure:** Run `p 2 1` and `p 2 0` and measure GPIO2. Tie GPIO4 to GND, then 3V3, and run `p 4` each time. Run `a 2 3` and `a 2 0`.
- **Evidence:** @VER-SYS-09
- **Pass criteria:** GPIO2 measures ≥ 2.6 V and ≤ 0.3 V; `p 4` reports 0, then 1.
- **Status:** Partial. The command paths and messages pass in QEMU, which does not model pads. Board pending.

### VER-SYS-10 — Refused pins
- **Type:** Verification
- **Verifies:** SYS-14
- **Method:** Test
- **Level:** System
- **Environment:** QEMU
- **Procedure:** Enter `p 7 1`, `p 36 1`, `p 24`, `p 40` and `a 2 6`.
- **Evidence:** @VER-SYS-10
- **Pass criteria:** Each prints its refusal message; nothing else changes.
- **Status:** Passed (QEMU).

### VER-SYS-11 — Deep calls and VLA
- **Type:** Verification
- **Verifies:** SYS-15
- **Method:** Test
- **Level:** System
- **Environment:** QEMU
- **Procedure:** Run `s`, and run the stress build (2,000 rounds of `recurse(200)` and `vla_after_spill(100+k)`).
- **Evidence:** @VER-SYS-11
- **Pass criteria:** Correct results, with 0 bad rounds.
- **Status:** Passed (QEMU). Stress: 0 bad, 2,000 alloca fix-ups at 100 Hz and 2,048 at 20 kHz.

### VER-SYS-12 — Interrupt handling
- **Type:** Verification
- **Verifies:** SYS-16
- **Method:** Test
- **Level:** System
- **Environment:** QEMU
- **Procedure:** Run `s` (software interrupt), run `i` (tick and UART counts), and run the 20 kHz stress build, checking that the computation results are still correct.
- **Evidence:** @VER-SYS-12
- **Pass criteria:** The handlers are counted, and 0 bad results over at least 100,000 interrupts.
- **Status:** Passed (QEMU). About 260,000 tick interrupts, 0 bad results.

### VER-SYS-13 — Tick rate and robustness
- **Type:** Verification
- **Verifies:** SYS-17
- **Method:** Test
- **Level:** System
- **Environment:** QEMU, Board
- **Procedure:** In QEMU, run `s` (ticks in `udelay(100 ms)`), and run the 20 kHz build for more than 10 s. On a board, compare `i` uptime with a stopwatch over 60 s.
- **Evidence:** @VER-SYS-13
- **Pass criteria:** 9–11 ticks; the tick count keeps rising for the whole 20 kHz run; the board's uptime is within 1 % of the stopwatch.
- **Status:** Partial. QEMU passes. Before the timer fix the 20 kHz run stalled after 2,860 ticks; after the fix, ticks kept counting (8,785 during the stress loop). The board timing is pending.

### VER-SYS-14 — Receive buffering
- **Type:** Verification
- **Verifies:** SYS-18
- **Method:** Test
- **Level:** System
- **Environment:** QEMU, Board
- **Procedure:** Start `s` and immediately send 20 × `r 3ffb1000\r` (220 bytes), then count the `read` replies.
- **Evidence:** @VER-SYS-14
- **Pass criteria:** 20 replies.
- **Status:** Partial. QEMU: 20 of 20. QEMU's serial back-end applies flow control, so FIFO overflow is only meaningfully tested on a board. Board pending.

### VER-SYS-15 — Fault reports
- **Type:** Verification
- **Verifies:** SYS-19, SYS-30
- **Method:** Test
- **Level:** System
- **Environment:** QEMU
- **Procedure:** For n = 0 to 5, boot, enter `f n` and capture the report.
- **Evidence:** @VER-SYS-15
- **Pass criteria:** The report headings are, in order: `Fatal exception 28: LoadProhibited`, `Fatal exception 0: IllegalInstruction`, `Fatal exception 6: IntegerDivideByZero`, `Debug exception (break?)`, `Double exception (cause 29 …)`, and `Unexpected high-level interrupt` with `level 3`. Each has `pc`, `ps`, registers and `called from`.
- **Status:** Passed (QEMU) for all six. Kernel exceptions and NMI are not reachable from the monitor.

### VER-SYS-16 — Reboot after a fault
- **Type:** Verification
- **Verifies:** SYS-20
- **Method:** Test
- **Level:** System
- **Environment:** QEMU, Board
- **Procedure:** After each fault report, send one byte.
- **Evidence:** @VER-SYS-16
- **Pass criteria:** The ROM prints `rst:0x3 (SW_RESET)`, and the banner appears again.
- **Status:** Partial. Passed in QEMU for `f 0` to `f 5`. Board pending.

### VER-SYS-17 — Self test
- **Type:** Verification
- **Verifies:** SYS-21
- **Method:** Test
- **Level:** System
- **Environment:** QEMU, Board
- **Procedure:** Enter `s`.
- **Evidence:** @VER-SYS-17
- **Pass criteria:** Four `ok` lines and `all ok`.
- **Status:** Partial. Passed in QEMU after both flash boot and RAM boot. Board pending.

### VER-SYS-18 — Blink mode
- **Type:** Verification
- **Verifies:** SYS-22
- **Method:** Test
- **Level:** System
- **Environment:** QEMU, Board
- **Procedure:** Build with `if (0)` in `main.c`, boot, and capture the output for 4 s. On a board, watch the LED.
- **Evidence:** @VER-SYS-18
- **Pass criteria:** `led 0` and `led 1` alternate, about 2 lines per second; on the board the LED blinks.
- **Status:** Partial. QEMU: 8 alternating lines in about 4 s. The board LED is pending.

### VER-SYS-19 — Internal-SRAM-only execution
- **Type:** Verification
- **Verifies:** SYS-23
- **Method:** Inspection
- **Level:** System
- **Environment:** Host
- **Procedure:** Inspect the link map, the image segments (`esptool image-info`) and `regs.h`. No section or access should be outside IRAM, DRAM or the peripheral space, and there should be no flash-cache or PSRAM addresses (`0x3F400000`–`0x3F7FFFFF`, `0x3F800000`–`0x3FBFFFFF`, `0x400C2000`–`0x40BFFFFF`).
- **Evidence:** @VER-SYS-19
- **Pass criteria:** There are only two segments, at `0x3FFB0000` and `0x40080000`, and no such addresses.
- **Status:** Passed (Host).

### VER-SYS-20 — make qemu
- **Type:** Verification
- **Verifies:** SYS-24
- **Method:** Test
- **Level:** System
- **Environment:** QEMU
- **Procedure:** Run `make qemu QEMU=<path>`, send `h`, and check the banner and the help text.
- **Evidence:** @VER-SYS-20
- **Pass criteria:** The banner, ready line and help text appear.
- **Status:** Passed (QEMU).

### VER-SYS-21 — Toolchain script
- **Type:** Verification
- **Verifies:** SYS-25
- **Method:** Test
- **Level:** System
- **Environment:** Host
- **Procedure:** Run `PREFIX=/tmp/tc WORK=/tmp/w tools/build-toolchain.sh`, then `make CROSS_COMPILE=/tmp/tc/bin/xtensa-esp32-elf-`.
- **Evidence:** @VER-SYS-21
- **Pass criteria:** Exit status 0, and a warning-free firmware build.
- **Status:** Partial. The same steps were executed by hand and produced the toolchain used for all tests. The script itself is pending.

### VER-SYS-22 — Documentation and trace check
- **Type:** Verification
- **Verifies:** SYS-28, SYS-32
- **Method:** Inspection
- **Level:** System
- **Environment:** Host
- **Procedure:** Inspect the README for each SYS-28 topic, and run `python3 tools/tracecheck.py --check`.
- **Evidence:** @VER-SYS-22
- **Pass criteria:** All topics are present, and the check exits 0.
- **Status:** Passed (Host).

### VER-SYS-23 — Originality inspection
- **Type:** Verification
- **Verifies:** SYS-29
- **Method:** Inspection
- **Level:** System
- **Environment:** Host
- **Procedure:** Review each source file against its authorship record. All files were written for this package; `tools/build-toolchain.sh` fetches third-party toolchain sources at build time but includes none.
- **Evidence:** Author's review.
- **Pass criteria:** No copied third-party source.
- **Status:** Partial. The author's review is done; an independent review is pending.

## Subsystem / integration level

### VER-SUB-01 — Compilation rules and layout
- **Type:** Verification
- **Verifies:** SUB-BLD-01, SUB-BLD-02
- **Method:** Inspection
- **Level:** Subsystem
- **Environment:** Host
- **Procedure:** Inspect the compile and link command lines printed by `make`, and the section addresses in `e32.map` and in `nm -n e32.elf`.
- **Evidence:** @VER-SUB-01
- **Pass criteria:** The flags match; `_vector_table` = `0x40080000`; `.data` starts at `0x3FFB0000`; `_stack_top` = `0x3FFDC000`.
- **Status:** Passed (Host).

### VER-SUB-02 — Layout guards
- **Type:** Verification
- **Verifies:** SUB-BLD-03
- **Method:** Test
- **Level:** Subsystem
- **Environment:** Host
- **Procedure:** Add `char big_buffer[170*1024];` to a copy of `lib.c` and link.
- **Evidence:** @VER-SUB-02
- **Pass criteria:** The link fails with "less than 8kB left for stack".
- **Status:** Passed (Host). The vector-placement assertion has not been tested negatively (that would need a modified linker script).

### VER-SUB-03 — Image conversion integration
- **Type:** Verification
- **Verifies:** SUB-BLD-04
- **Method:** Test
- **Level:** Subsystem
- **Environment:** Host, QEMU
- **Procedure:** Run `esptool --chip esp32 image-info e32.bin`, and boot the image in QEMU through the ROM.
- **Evidence:** @VER-SUB-03
- **Pass criteria:** esptool reports 2 segments and "Checksum: … (valid)"; the ROM loads and starts the image.
- **Status:** Passed (Host, QEMU).

### VER-SUB-04 — Make targets
- **Type:** Verification
- **Verifies:** SUB-BLD-05
- **Method:** Test
- **Level:** Subsystem
- **Environment:** Host, QEMU, Board
- **Procedure:** Run `make all`, `make e32.dis`, `make flash.img`, `make qemu QEMU=…`, `make clean`, and (on a board) `make ram` and `make flash`.
- **Evidence:** @VER-SUB-04
- **Pass criteria:** Each target does what SW-BLD-02 and SW-BLD-03 say.
- **Status:** Partial. `all`, `flash.img`, `qemu` and `clean` pass; `ram` and `flash` are pending (hardware).

### VER-SUB-05 — Toolchain subsystem
- **Type:** Verification
- **Verifies:** SUB-BLD-06
- **Method:** Test
- **Level:** Subsystem
- **Environment:** Host
- **Procedure:** As VER-SYS-21, plus check `xtensa-esp32-elf-gcc -v` for C only, and the overlay's `xtensa-config.h` in the gcc tree.
- **Evidence:** @VER-SYS-21
- **Pass criteria:** The compiler reports `--enable-languages=c` and builds e32.
- **Status:** Partial. Same reason as VER-SYS-21.

### VER-SUB-06 — Boot environment
- **Type:** Verification
- **Verifies:** SUB-BOOT-01
- **Method:** Test
- **Level:** Subsystem
- **Environment:** QEMU
- **Procedure:** Boot. Check that the banner shows `stack top 0x3ffdc000`, that faults are reported by our handler (proving `VECBASE`), and that `s` passes (window state and stack usable).
- **Evidence:** @VER-SUB-06
- **Pass criteria:** All three hold.
- **Status:** Passed (QEMU).

### VER-SUB-07 — Watchdog subsystem
- **Type:** Verification
- **Verifies:** SUB-BOOT-02
- **Method:** Test
- **Level:** Subsystem
- **Environment:** QEMU, Board
- **Procedure:** As VER-SYS-07.
- **Evidence:** @VER-SYS-07
- **Pass criteria:** As VER-SYS-07.
- **Status:** Partial. Same reason as VER-SYS-07.

### VER-SUB-08 — Console inheritance
- **Type:** Verification
- **Verifies:** SUB-BOOT-03
- **Method:** Test
- **Level:** Subsystem
- **Environment:** QEMU, Board
- **Procedure:** Boot, and check that the ROM's last line (`entry 0x…`) is complete and separate from the banner, and that the banner is readable at 115200.
- **Evidence:** @VER-SUB-08
- **Pass criteria:** No interleaved or garbled characters.
- **Status:** Partial. QEMU passes; the board is pending.

### VER-SUB-09 — Windows and alloca integration
- **Type:** Verification
- **Verifies:** SUB-EXC-01, SUB-EXC-02
- **Method:** Test
- **Level:** Subsystem
- **Environment:** QEMU
- **Procedure:** Run the stress build with an alloca counter in `_alloca_handler`.
- **Evidence:** @VER-SUB-09
- **Pass criteria:** 0 bad results, and alloca count ≥ number of VLA calls.
- **Status:** Passed (QEMU) for call8 frames; call4 is used by startup and interrupt entry. call12 frames are not generated by GCC, so the call12 handlers are not exercised (see VER-CMP-02).

### VER-SUB-10 — Interrupt integration
- **Type:** Verification
- **Verifies:** SUB-EXC-03, SUB-EXC-04
- **Method:** Test
- **Level:** Subsystem
- **Environment:** QEMU
- **Procedure:** Run the 20 kHz stress build, and run `s` and `i` (matrix-routed UART on line 17).
- **Evidence:** @VER-SUB-10
- **Pass criteria:** As VER-SYS-12, and line 17 is counted on input.
- **Status:** Passed (QEMU).

### VER-SUB-11 — Fault routing
- **Type:** Verification
- **Verifies:** SUB-EXC-05
- **Method:** Test
- **Level:** Subsystem
- **Environment:** QEMU
- **Procedure:** Run `f 0` to `f 5` (user, debug/level 6, double and level-3 paths).
- **Evidence:** @VER-SYS-15
- **Pass criteria:** Each report states the correct kind.
- **Status:** Partial. Passed for the user, level-6, double and level-3 paths. Kernel, NMI and levels 2, 4 and 5 are not reachable without extra hardware stimulus.

### VER-SUB-12 — Timekeeping integration
- **Type:** Verification
- **Verifies:** SUB-TIME-01, SUB-TIME-02, SUB-TIME-03
- **Method:** Test
- **Level:** Subsystem
- **Environment:** QEMU
- **Procedure:** As VER-SYS-13 (QEMU part).
- **Evidence:** @VER-SYS-13
- **Pass criteria:** As VER-SYS-13.
- **Status:** Passed (QEMU).

### VER-SUB-13 — Console integration
- **Type:** Verification
- **Verifies:** SUB-CON-01, SUB-CON-02, SUB-CON-03
- **Method:** Test
- **Level:** Subsystem
- **Environment:** QEMU
- **Procedure:** Check CR LF in the captured output; edit with backspace (`r 3ffb0001`, BS, `0`); do the 20-command busy test.
- **Evidence:** @VER-SUB-13
- **Pass criteria:** Lines end in CR LF; the edited command reads `3ffb0000`; there are 20 replies.
- **Status:** Passed (QEMU).

### VER-SUB-14 — printf integration
- **Type:** Verification
- **Verifies:** SUB-CON-04
- **Method:** Test
- **Level:** Subsystem
- **Environment:** Host, QEMU
- **Procedure:** Compare `pp_sprintf` with glibc `snprintf` on the printf.feature examples, and check `%p`, `%08x` and `%-2u` in the target output (banner, fault report).
- **Evidence:** @VER-SUB-14
- **Pass criteria:** Identical strings.
- **Status:** Passed (Host, QEMU).

### VER-SUB-15 — GPIO subsystem
- **Type:** Verification
- **Verifies:** SUB-GPIO-01, SUB-GPIO-02
- **Method:** Test
- **Level:** Subsystem
- **Environment:** QEMU, Board
- **Procedure:** As VER-SYS-09 and VER-SYS-10, plus `r` of the IO_MUX register after `a 2 3` on a board.
- **Evidence:** @VER-SYS-09
- **Pass criteria:** As VER-SYS-09 and VER-SYS-10; `MCU_SEL` reads back as 3.
- **Status:** Partial. The protection part passes in QEMU; the register and pad effects are pending (hardware).

### VER-SUB-16 — Monitor subsystem
- **Type:** Verification
- **Verifies:** SUB-MON-01, SUB-MON-02, SUB-MON-03
- **Method:** Test
- **Level:** Subsystem
- **Environment:** QEMU
- **Procedure:** As VER-SYS-08, plus check the start-up order (the banner comes before the first interrupt count).
- **Evidence:** @VER-SYS-08
- **Pass criteria:** As VER-SYS-08.
- **Status:** Passed (QEMU).

### VER-SUB-17 — Fault subsystem
- **Type:** Verification
- **Verifies:** SUB-FLT-01, SUB-FLT-02, SUB-FLT-03, SUB-FLT-04
- **Method:** Test
- **Level:** Subsystem
- **Environment:** QEMU
- **Procedure:** Run `f 4` (the faulting stack is unusable, yet the report prints, proving the private stack). Run `f 0`, then press a key. For the nested case, use a test build that faults inside `panic_handler`.
- **Evidence:** @VER-SUB-17
- **Pass criteria:** The report prints even with a bad SP, the key reboots, and the nested fault halts silently.
- **Status:** Partial. Everything except the nested case passes in QEMU; the nested-fault build is pending (automation).

### VER-SUB-18 — Support library
- **Type:** Verification
- **Verifies:** SUB-LIB-01
- **Method:** Test
- **Level:** Subsystem
- **Environment:** Host
- **Procedure:** As VER-CMP-15.
- **Evidence:** @VER-CMP-15
- **Pass criteria:** As VER-CMP-15.
- **Status:** Passed (Host).

### VER-SUB-19 — Verification environment
- **Type:** Verification
- **Verifies:** SUB-VEN-01
- **Method:** Test
- **Level:** Subsystem
- **Environment:** QEMU
- **Procedure:** Boot in flash mode with the console on stdio, and in download mode with the console on TCP; run `s` in each.
- **Evidence:** @VER-SUB-19
- **Pass criteria:** `all ok` in both.
- **Status:** Passed (QEMU).

### VER-SUB-20 — Document set
- **Type:** Verification
- **Verifies:** SUB-DOC-01
- **Method:** Inspection
- **Level:** Subsystem
- **Environment:** Host
- **Procedure:** List `docs/`, and confirm the presence of every file named in SUB-DOC-01, the README provenance section, and that `traceability.md` is regenerated by the checker.
- **Evidence:** @VER-SYS-22
- **Pass criteria:** All present; regeneration gives no diff.
- **Status:** Passed (Host).

### VER-SUB-21 — Target hardware fitness
- **Type:** Verification
- **Verifies:** SUB-TGT-01, SUB-TGT-02
- **Method:** Inspection
- **Level:** Subsystem
- **Environment:** Board
- **Procedure:** Inspect the board and module markings, the schematic (USB-serial, BOOT, EN, LED) and the output of `esptool chip_id` and `flash_id`.
- **Evidence:** Inspection record (to be filed per board).
- **Pass criteria:** Every HW requirement is satisfied by the board.
- **Status:** Pending (hardware).

## Hardware level

### VER-HW-01 — SoC identity
- **Type:** Verification
- **Verifies:** HW-01, HW-14
- **Method:** Inspection
- **Level:** Hardware
- **Environment:** Board
- **Procedure:** Run `esptool --chip esp32 chip_id` and read the module marking.
- **Evidence:** Inspection record.
- **Pass criteria:** The chip is ESP32 (D0WD/D0WDQ6); no PSRAM needed. The firmware runs either way.
- **Status:** Pending (hardware).

### VER-HW-02 — Crystal frequency
- **Type:** Verification
- **Verifies:** HW-02
- **Method:** Analysis
- **Level:** Hardware
- **Environment:** Board
- **Procedure:** Read the ROM boot lines at 115200. With a 26 MHz crystal they would only be readable at 74880, since 115200 × 26/40 = 74880.
- **Evidence:** Terminal capture.
- **Pass criteria:** The ROM lines are readable at 115200.
- **Status:** Pending (hardware).

### VER-HW-03 — Flash
- **Type:** Verification
- **Verifies:** HW-03
- **Method:** Inspection
- **Level:** Hardware
- **Environment:** Board
- **Procedure:** Run `esptool flash_id`, and read the ROM line `mode:DIO, clock div:…` at boot.
- **Evidence:** Inspection record.
- **Pass criteria:** The size is ≥ 1 MB and the flash boots in DIO.
- **Status:** Pending (hardware).

### VER-HW-04 — Serial and boot controls
- **Type:** Verification
- **Verifies:** HW-04, HW-05
- **Method:** Test
- **Level:** Hardware
- **Environment:** Board
- **Procedure:** Hold BOOT and press EN, and check that the ROM prints `waiting for download`; then run `esptool chip_id` without manual intervention, using the auto-reset circuit.
- **Evidence:** Terminal capture.
- **Pass criteria:** Both work.
- **Status:** Pending (hardware).

### VER-HW-05 — LED
- **Type:** Verification
- **Verifies:** HW-06
- **Method:** Test
- **Level:** Hardware
- **Environment:** Board
- **Procedure:** Run `p 2 1` and then `p 2 0`.
- **Evidence:** Observation.
- **Pass criteria:** The LED changes state.
- **Status:** Pending (hardware).

### VER-HW-06 — Pad constraints
- **Type:** Verification
- **Verifies:** HW-07, HW-08
- **Method:** Inspection
- **Level:** Hardware
- **Environment:** Host
- **Procedure:** Compare `gpio.c`'s pad table and refusal rules against the ESP32 datasheet pin list and the module datasheet (the flash connection).
- **Evidence:** Review record.
- **Pass criteria:** The tables agree.
- **Status:** Pending. The table was written from the Technical Reference Manual register list; an independent cross-check against the datasheet is still to be done.

### VER-HW-07 — Memory map
- **Type:** Verification
- **Verifies:** HW-09, HW-10
- **Method:** Inspection
- **Level:** Hardware
- **Environment:** Host, QEMU
- **Procedure:** Compare `esp32.lds` with the Technical Reference Manual memory map and with ESP-IDF's documented application memory layout; confirm no byte access to IRAM (all `.rodata` is in DRAM according to the link map).
- **Evidence:** `e32.map`; the QEMU run uses both regions successfully.
- **Pass criteria:** The regions lie within the documented free SRAM; `.rodata` is in DRAM.
- **Status:** Partial. The link map and QEMU run are consistent; the board is pending.

### VER-HW-08 — Boot ROM behaviour
- **Type:** Verification
- **Verifies:** HW-11
- **Method:** Test
- **Level:** Hardware
- **Environment:** QEMU, Board
- **Procedure:** Boot from flash and from download mode.
- **Evidence:** @VER-SYS-02, @VER-SYS-03
- **Pass criteria:** The ROM loads, checks and starts the image; UART0 works at once.
- **Status:** Partial. Passed with the real ROM binary in QEMU; the silicon is pending.

### VER-HW-09 — Software reset
- **Type:** Verification
- **Verifies:** HW-12
- **Method:** Test
- **Level:** Hardware
- **Environment:** QEMU, Board
- **Procedure:** As VER-SYS-16.
- **Evidence:** @VER-SYS-16
- **Pass criteria:** `rst:0x3 (SW_RESET)`.
- **Status:** Partial. QEMU passes; the board is pending.

### VER-HW-10 — Core configuration
- **Type:** Verification
- **Verifies:** HW-13
- **Method:** Inspection
- **Level:** Hardware
- **Environment:** Host
- **Procedure:** Compare the constants in `include/xtensa.h` and `vectors.S` with `xtensa/config/core-isa.h` from the `xtensa_esp32` overlay (`XCHAL_*_VECOFS`, `XCHAL_INTLEVEL1_MASK`, `XCHAL_TIMER0_INTERRUPT`, `XCHAL_NUM_AREGS`, `XCHAL_HAVE_LOOPS`, `XCHAL_HAVE_DIV32`, `XCHAL_NUM_MISC_REGS`, `XCHAL_EXCM_LEVEL`).
- **Evidence:** Review notes (2026-11-14).
- **Pass criteria:** All values match.
- **Status:** Passed (Host).

## Software level

### VER-SW-01 — Startup sequence
- **Type:** Verification
- **Verifies:** SW-BOOT-01, SW-BOOT-02, SW-BOOT-03, SW-BOOT-04, SW-BOOT-05, SW-BOOT-06
- **Method:** Inspection
- **Level:** Software
- **Environment:** Host
- **Procedure:** Disassemble `call_start` and check the instruction order and the literal values (`VECBASE` = `0x40080000`, `a1` = `0x3FFDC000`, `PS` = `0x00040020`).
- **Evidence:** @VER-SW-01
- **Pass criteria:** It matches the requirements.
- **Status:** Passed (Host).

### VER-SW-02 — Watchdog software
- **Type:** Verification
- **Verifies:** SW-WDT-01
- **Method:** Test
- **Level:** Software
- **Environment:** QEMU
- **Procedure:** As VER-SYS-07 (QEMU part).
- **Evidence:** @VER-SYS-07
- **Pass criteria:** As VER-SYS-07.
- **Status:** Partial. The TG0 path is shown working; the RTC and TG1 writes are confirmed only by inspection.

### VER-SW-03 — Output software
- **Type:** Verification
- **Verifies:** SW-CON-01, SW-CON-02
- **Method:** Test
- **Level:** Software
- **Environment:** QEMU
- **Procedure:** Capture the raw output bytes and check for CR LF. Inspect `serial_setup` for UART writes.
- **Evidence:** @VER-SUB-13
- **Pass criteria:** Every LF is preceded by CR, and there are no CLKDIV or CONF0 writes.
- **Status:** Passed (QEMU).

### VER-SW-04 — Line input software
- **Type:** Verification
- **Verifies:** SW-CON-03, SW-CON-07
- **Method:** Test
- **Level:** Software
- **Environment:** QEMU
- **Procedure:** Send a backspace edit, a control character (`0x01`) inside a command, an 85-character line, and an LF-terminated line.
- **Evidence:** @VER-SW-04
- **Pass criteria:** The backspace edit works, the control character is ignored, the line is truncated at 79 characters, and LF ends the line.
- **Status:** Partial. The backspace edit passes; the others are pending (automation).

### VER-SW-05 — Interrupt receive software
- **Type:** Verification
- **Verifies:** SW-CON-04, SW-CON-05, SW-CON-06
- **Method:** Test
- **Level:** Software
- **Environment:** QEMU
- **Procedure:** Do the 20-command busy test; check that `i` shows line 17. For overruns, use a test build with a 4-byte ring and check `rx_overruns` > 0.
- **Evidence:** @VER-SYS-14
- **Pass criteria:** 20 replies, line 17 counted, and overruns counted in the small-ring build.
- **Status:** Partial. Replies and counting pass; the overrun build is pending (automation).

### VER-SW-06 — Formatting software
- **Type:** Verification
- **Verifies:** SW-FMT-01, SW-FMT-02, SW-FMT-03
- **Method:** Test
- **Level:** Software
- **Environment:** Host, QEMU
- **Procedure:** Run the host comparison (VER-CMP-11), and check with `nm` that `printf` and `pp_printf` have the same address.
- **Evidence:** @VER-CMP-11
- **Pass criteria:** All examples match, and the addresses are equal.
- **Status:** Passed (Host).

### VER-SW-07 — Window and alloca software
- **Type:** Verification
- **Verifies:** SW-EXC-01, SW-EXC-04
- **Method:** Test
- **Level:** Software
- **Environment:** QEMU
- **Procedure:** As VER-SUB-09.
- **Evidence:** @VER-SUB-09
- **Pass criteria:** As VER-SUB-09.
- **Status:** Partial. call4 and call8 are exercised; call12 is not (see VER-CMP-02).

### VER-SW-08 — Exception entry software
- **Type:** Verification
- **Verifies:** SW-EXC-02, SW-EXC-03
- **Method:** Test
- **Level:** Software
- **Environment:** QEMU
- **Procedure:** As VER-SUB-10, plus `f 0` (non-interrupt cause to `_panic`).
- **Evidence:** @VER-SUB-10
- **Pass criteria:** As VER-SUB-10.
- **Status:** Passed (QEMU).

### VER-SW-09 — Interrupt API software
- **Type:** Verification
- **Verifies:** SW-EXC-05, SW-EXC-06, SW-EXC-07, SW-EXC-08, SW-EXC-09, SW-EXC-10
- **Method:** Test
- **Level:** Software
- **Environment:** QEMU
- **Procedure:** Run `s` (`irq_request`, `INTSET`, `irq_disable`) and `i`. For the unhandled-line and invalid-line cases, use a test build that calls `irq_request(11, …)` (expect −1) and enables line 9 without a handler, then sets it with `INTSET`.
- **Evidence:** @VER-SW-09
- **Pass criteria:** Normal paths work; −1 is returned; `irq 9: no handler, disabled` is printed.
- **Status:** Partial. Normal paths pass; the negative cases are pending (automation).

### VER-SW-10 — Fatal vectors software
- **Type:** Verification
- **Verifies:** SW-EXC-11
- **Method:** Test
- **Level:** Software
- **Environment:** QEMU
- **Procedure:** `f 3` (level 6), `f 4` (double), `f 5` (level 3).
- **Evidence:** @VER-SYS-15
- **Pass criteria:** The kind is reported correctly.
- **Status:** Partial. Passed for levels 3, 6 and double; levels 2, 4, 5, 7 and kernel are pending.

### VER-SW-11 — Timekeeping software
- **Type:** Verification
- **Verifies:** SW-TIME-01, SW-TIME-02, SW-TIME-03, SW-TIME-04
- **Method:** Test
- **Level:** Software
- **Environment:** QEMU
- **Procedure:** As VER-SYS-13 (QEMU part), plus inspect `HZ` and `CPU_HZ`.
- **Evidence:** @VER-SYS-13
- **Pass criteria:** As VER-SYS-13.
- **Status:** Passed (QEMU).

### VER-SW-12 — GPIO software
- **Type:** Verification
- **Verifies:** SW-GPIO-01, SW-GPIO-02, SW-GPIO-03, SW-GPIO-04, SW-GPIO-05
- **Method:** Test
- **Level:** Software
- **Environment:** QEMU, Board
- **Procedure:** Run the refusal cases in QEMU. On a board, read the IO_MUX, `FUNC_OUT_SEL`, `ENABLE` and `OUT` registers with `r` after `p 2 1`, and compare with the expected values.
- **Evidence:** @VER-SW-12
- **Pass criteria:** Refusals are correct; registers hold `MCU_SEL` = 2, `FUN_IE` = 1, `OUT_SEL` = `0x500` (256 + `OEN_SEL`), and `ENABLE`/`OUT` bit 2 set.
- **Status:** Partial. Refusals pass; the register effects are pending (hardware), because QEMU's GPIO model does not read back.

### VER-SW-13 — Monitor software
- **Type:** Verification
- **Verifies:** SW-MON-01, SW-MON-02, SW-MON-03, SW-MON-04, SW-MON-05, SW-MON-06, SW-MON-07
- **Method:** Test
- **Level:** Software
- **Environment:** QEMU
- **Procedure:** As VER-SYS-08, VER-SYS-15, VER-SYS-17 and VER-SYS-18.
- **Evidence:** @VER-SYS-08
- **Pass criteria:** The formats match exactly.
- **Status:** Passed (QEMU).

### VER-SW-14 — Fault software
- **Type:** Verification
- **Verifies:** SW-FLT-01, SW-FLT-02, SW-FLT-03, SW-FLT-04, SW-FLT-05
- **Method:** Test
- **Level:** Software
- **Environment:** QEMU
- **Procedure:** As VER-SUB-17.
- **Evidence:** @VER-SUB-17
- **Pass criteria:** As VER-SUB-17.
- **Status:** Partial. The nested case is pending.

### VER-SW-15 — Library software
- **Type:** Verification
- **Verifies:** SW-LIB-01
- **Method:** Test
- **Level:** Software
- **Environment:** Host
- **Procedure:** As VER-CMP-15.
- **Evidence:** @VER-CMP-15
- **Pass criteria:** 0 failures.
- **Status:** Passed (Host).

### VER-SW-16 — Image tool software
- **Type:** Verification
- **Verifies:** SW-IMG-01, SW-IMG-02, SW-IMG-03, SW-IMG-04, SW-IMG-05, SW-IMG-06
- **Method:** Test
- **Level:** Software
- **Environment:** Host
- **Procedure:** As VER-CMP-18.
- **Evidence:** @VER-CMP-18
- **Pass criteria:** As VER-CMP-18.
- **Status:** Passed (Host, 2026-11-14). The usage, non-ELF, non-Xtensa and missing-file cases pass, as do esptool decoding and the checksum. The >16-segment, zero-segment and truncated-file cases are now automated (SW-IMG-03-S01, in both suites) and pass.

### VER-SW-17 — Build scripts
- **Type:** Verification
- **Verifies:** SW-BLD-01, SW-BLD-02, SW-BLD-03, SW-BLD-04, SW-BLD-05
- **Method:** Test
- **Level:** Software
- **Environment:** Host, QEMU
- **Procedure:** As VER-SUB-04 and VER-SUB-02, plus inspect the compile and link lines printed by `make` against SW-BLD-05. For `flash.img`, check its size (4,194,304 bytes), check that the bytes at `0x1000` equal `e32.bin`, and check that the other bytes are `0xFF`.
- **Evidence:** @VER-SUB-04
- **Pass criteria:** As stated.
- **Status:** Partial. The serial targets are pending (hardware).

### VER-SW-18 — Toolchain script
- **Type:** Verification
- **Verifies:** SW-TC-01
- **Method:** Inspection
- **Level:** Software
- **Environment:** Host
- **Procedure:** Review the script against SW-TC-01 (variables, tags, overlay copy, configure options, `set -e`).
- **Evidence:** Review notes.
- **Pass criteria:** All items present.
- **Status:** Passed (Host). Execution is covered by VER-SYS-21.

### VER-SW-19 — Trace checker
- **Type:** Verification
- **Verifies:** SW-DOC-01
- **Method:** Test
- **Level:** Software
- **Environment:** Host
- **Procedure:** As VER-CMP-21.
- **Evidence:** @VER-CMP-21
- **Pass criteria:** As VER-CMP-21.
- **Status:** Passed (Host).

## Interface level

### VER-IF-01 — Image format contract
- **Type:** Verification
- **Verifies:** IF-01
- **Method:** Test
- **Level:** Interface
- **Environment:** Host, QEMU
- **Procedure:** Decode `e32.bin` with `esptool image-info` (an independent implementation of the format), and boot it with the real ROM.
- **Evidence:** @VER-SUB-03
- **Pass criteria:** The fields decode as specified, the checksum is valid, and the ROM accepts the image.
- **Status:** Passed (Host, QEMU).

### VER-IF-02 — Hand-over contract
- **Type:** Verification
- **Verifies:** IF-02
- **Method:** Test
- **Level:** Interface
- **Environment:** QEMU
- **Procedure:** Boot through both ROM paths (which leave different ROM states) and run `s`.
- **Evidence:** @VER-SUB-19
- **Pass criteria:** `all ok` in both.
- **Status:** Passed (QEMU).

### VER-IF-03 — Console protocol contract
- **Type:** Verification
- **Verifies:** IF-03
- **Method:** Test
- **Level:** Interface
- **Environment:** QEMU, Board
- **Procedure:** Run the console.feature and monitor.feature scenarios.
- **Evidence:** @VER-SYS-06
- **Pass criteria:** All pass.
- **Status:** Partial. QEMU passes; the board's line parameters are pending.

### VER-IF-04 — Loader transport contract
- **Type:** Verification
- **Verifies:** IF-04
- **Method:** Test
- **Level:** Interface
- **Environment:** QEMU, Board
- **Procedure:** Run `esptool load-ram` against QEMU in download mode; run `write_flash` against a board.
- **Evidence:** @VER-SYS-03
- **Pass criteria:** Both succeed.
- **Status:** Partial. `load-ram` passes; `write_flash` is pending (hardware).

### VER-IF-05 — Vector layout
- **Type:** Verification
- **Verifies:** IF-05
- **Method:** Inspection
- **Level:** Interface
- **Environment:** Host
- **Procedure:** Run `nm -n e32.elf` and `objdump -d` on `.vectors`: check that each entry is at its offset and that no entry overruns the next.
- **Evidence:** @VER-IF-05
- **Pass criteria:** The offsets are exact.
- **Status:** Passed (Host).

### VER-IF-06 — Frame layouts
- **Type:** Verification
- **Verifies:** IF-06, IF-07
- **Method:** Inspection
- **Level:** Interface
- **Environment:** Host
- **Procedure:** Compile `panic.c`, whose `_Static_assert`s compare `offsetof` and `sizeof` in C with the `IF_*`/`PF_*` constants used by the assembly.
- **Evidence:** The build succeeds (a mismatch fails compilation).
- **Pass criteria:** It compiles.
- **Status:** Passed (Host).

### VER-IF-07 — Linker symbols
- **Type:** Verification
- **Verifies:** IF-08
- **Method:** Inspection
- **Level:** Interface
- **Environment:** Host
- **Procedure:** Run `nm` and check each symbol's value and alignment.
- **Evidence:** @VER-SUB-01
- **Pass criteria:** As IF-08.
- **Status:** Passed (Host).

### VER-IF-08 — Interrupt API contract
- **Type:** Verification
- **Verifies:** IF-09
- **Method:** Test
- **Level:** Interface
- **Environment:** QEMU
- **Procedure:** As VER-SW-09.
- **Evidence:** @VER-SW-09
- **Pass criteria:** As VER-SW-09.
- **Status:** Partial. Same as VER-SW-09.

### VER-IF-09 — GPIO API contract
- **Type:** Verification
- **Verifies:** IF-10
- **Method:** Test
- **Level:** Interface
- **Environment:** QEMU, Board
- **Procedure:** As VER-SW-12.
- **Evidence:** @VER-SW-12
- **Pass criteria:** As VER-SW-12.
- **Status:** Partial. Same as VER-SW-12.

### VER-IF-10 — Console API contract
- **Type:** Verification
- **Verifies:** IF-11
- **Method:** Test
- **Level:** Interface
- **Environment:** Host, QEMU
- **Procedure:** The build compiles every user of `io.h` with format checking. The behaviour is covered by VER-SUB-13 and VER-SUB-14.
- **Evidence:** @VER-SUB-13
- **Pass criteria:** No warnings; scenarios pass.
- **Status:** Passed (Host, QEMU).

### VER-IF-11 — Interrupt matrix contract
- **Type:** Verification
- **Verifies:** IF-12
- **Method:** Test
- **Level:** Interface
- **Environment:** QEMU, Board
- **Procedure:** Show that UART0 input raises CPU line 17 only after `irq_map(34, 17)`, and that line 17 counts with `i`.
- **Evidence:** @VER-SUB-10
- **Pass criteria:** Line 17 is counted.
- **Status:** Partial. QEMU passes; the board is pending.

### VER-IF-12 — Register map
- **Type:** Verification
- **Verifies:** IF-13
- **Method:** Inspection
- **Level:** Interface
- **Environment:** Host, QEMU
- **Procedure:** Compare `regs.h` with the Technical Reference Manual. Behaviour in QEMU confirms the UART, TIMG, RTC_CNTL and matrix addresses.
- **Evidence:** Review notes; QEMU behaviour.
- **Pass criteria:** All match.
- **Status:** Partial. The GPIO and IO_MUX offsets are not observable in QEMU; a board read-back is pending.

### VER-IF-13 — Watchdog protocol
- **Type:** Verification
- **Verifies:** IF-14
- **Method:** Test
- **Level:** Interface
- **Environment:** QEMU
- **Procedure:** The QEMU test build arms TG0 through the key protocol (proving the unlock works), then `wdt_disable` disarms it.
- **Evidence:** @VER-SYS-07
- **Pass criteria:** Resets stop.
- **Status:** Passed (QEMU).

### VER-IF-14 — Windowed-ABI contract
- **Type:** Verification
- **Verifies:** IF-15
- **Method:** Test
- **Level:** Interface
- **Environment:** QEMU
- **Procedure:** As VER-SUB-09 and VER-SUB-10. Interrupts that spill windows while VLAs move SP check that the save areas are honoured.
- **Evidence:** @VER-SUB-09
- **Pass criteria:** 0 bad results.
- **Status:** Passed (QEMU).

### VER-IF-15 — Emulator invocation
- **Type:** Verification
- **Verifies:** IF-16
- **Method:** Test
- **Level:** Interface
- **Environment:** QEMU
- **Procedure:** Use both invocations (VER-SUB-19).
- **Evidence:** @VER-SUB-19
- **Pass criteria:** Both boot.
- **Status:** Passed (QEMU).

## Component / unit level

### VER-CMP-01 — call_start unit
- **Type:** Verification
- **Verifies:** CMP-01
- **Method:** Inspection
- **Level:** Unit
- **Environment:** Host
- **Procedure:** As VER-SW-01.
- **Evidence:** @VER-SW-01
- **Pass criteria:** As VER-SW-01.
- **Status:** Passed (Host).

### VER-CMP-02 — Window handler units
- **Type:** Verification
- **Verifies:** CMP-02, CMP-03, CMP-04
- **Method:** Test
- **Level:** Unit
- **Environment:** QEMU
- **Procedure:** Use `recurse(200)` (call8 frames). For call4, use the startup and interrupt entry. For call12, use a hand-written assembly test that calls a recursive function with `call12` from a frame reserving the 32-byte extra save area.
- **Evidence:** @VER-SYS-11
- **Pass criteria:** Correct results in all three.
- **Status:** Partial. call8 and call4 pass. GCC never emits `call12`, so the call12 test is pending (automation).

### VER-CMP-03 — Vector dispatch units
- **Type:** Verification
- **Verifies:** CMP-05, CMP-06
- **Method:** Test
- **Level:** Unit
- **Environment:** QEMU
- **Procedure:** As VER-SW-08 and VER-SW-10.
- **Evidence:** @VER-SYS-15
- **Pass criteria:** As those.
- **Status:** Partial. As VER-SW-10.

### VER-CMP-04 — Alloca handler unit
- **Type:** Verification
- **Verifies:** CMP-07
- **Method:** Test
- **Level:** Unit
- **Environment:** QEMU
- **Procedure:** Use an alloca counter test build: run `vla_after_spill` 2,000 times.
- **Evidence:** @VER-SUB-09
- **Pass criteria:** Count = 2,000 at 100 Hz, and correct results.
- **Status:** Partial. Passed for call8 callers (count exactly 2,000). call4 and call12 callers are pending.

### VER-CMP-05 — Level-1 handler unit
- **Type:** Verification
- **Verifies:** CMP-08
- **Method:** Test
- **Level:** Unit
- **Environment:** QEMU
- **Procedure:** As VER-SYS-12 (20 kHz stress).
- **Evidence:** @VER-SYS-12
- **Pass criteria:** 0 bad results.
- **Status:** Passed (QEMU).

### VER-CMP-06 — _panic unit
- **Type:** Verification
- **Verifies:** CMP-09
- **Method:** Test
- **Level:** Unit
- **Environment:** QEMU
- **Procedure:** Run `f 4`: with SP = `0x100`, the report must still print, from the private stack.
- **Evidence:** @VER-SYS-15
- **Pass criteria:** The report is printed.
- **Status:** Passed (QEMU).

### VER-CMP-07 — irq.c unit
- **Type:** Verification
- **Verifies:** CMP-10, CMP-11, CMP-12
- **Method:** Test
- **Level:** Unit
- **Environment:** QEMU, Host
- **Procedure:** As VER-SW-09.
- **Evidence:** @VER-SW-09
- **Pass criteria:** As VER-SW-09.
- **Status:** Partial. On the host (2026-11-14) the unit scenarios CMP-10-S02, CMP-10-S03, CMP-11-S02, CMP-12-S02 and CMP-12-S03 pass, including the invalid-line and no-handler cases. On the target the negative cases are still pending (automation), as VER-SW-09.

### VER-CMP-08 — timer.c unit
- **Type:** Verification
- **Verifies:** CMP-13
- **Method:** Test
- **Level:** Unit
- **Environment:** QEMU, Host
- **Procedure:** Run at 20 kHz for more than 10 s, and check that `jiffies` never stalls.
- **Evidence:** @VER-SYS-13
- **Pass criteria:** Monotonic growth throughout.
- **Status:** Passed (QEMU), after the fix. Passed (Host, 2026-11-14): CMP-13-S02 to CMP-13-S04, including the catch-up regression.

### VER-CMP-09 — wdt.c unit
- **Type:** Verification
- **Verifies:** CMP-14
- **Method:** Test
- **Level:** Unit
- **Environment:** QEMU, Host
- **Procedure:** As VER-SW-02.
- **Evidence:** @VER-SYS-07
- **Pass criteria:** As VER-SW-02.
- **Status:** Partial. Passed (Host, 2026-11-14): CMP-14-S02 checks the exact write sequence for all three watchdogs. The target checks remain as VER-SW-02.

### VER-CMP-10 — io.c unit
- **Type:** Verification
- **Verifies:** CMP-15, CMP-16, CMP-17, CMP-18
- **Method:** Test
- **Level:** Unit
- **Environment:** QEMU, Host
- **Procedure:** As VER-SW-03, VER-SW-04 and VER-SW-05.
- **Evidence:** @VER-SUB-13
- **Pass criteria:** As those.
- **Status:** Partial. Passed (Host, 2026-11-14): CMP-15-S02, CMP-15-S03, CMP-16-S02, CMP-16-S03, CMP-17-S02, CMP-17-S03 and CMP-18-S02, including the overrun and truncation cases. On the target the overrun and truncation cases are still pending.

### VER-CMP-11 — pp_printf unit
- **Type:** Verification
- **Verifies:** CMP-19, CMP-20
- **Method:** Test
- **Level:** Unit
- **Environment:** Host
- **Procedure:** Compile `pp_printf.c` for the host with a stub `putc`, and compare `pp_sprintf` with glibc `snprintf` on every example in printf.feature.
- **Evidence:** @VER-CMP-11
- **Pass criteria:** All identical.
- **Status:** Passed (Host, 2026-11-14). The full printf.feature example table (CMP-19-S01, 10 rows), the extension cases (SW-FMT-01-S01) and CMP-20-S01 are automated and pass.

### VER-CMP-12 — gpio.c unit
- **Type:** Verification
- **Verifies:** CMP-21, CMP-22, CMP-23
- **Method:** Test
- **Level:** Unit
- **Environment:** Host
- **Procedure:** Compile `gpio.c` for the host with `readl`/`writel` redirected to a fake register file; check the table, the refusals (no writes) and the register values written for `p 2 1`, `p 34` and `a 2 3`.
- **Evidence:** @VER-CMP-12
- **Pass criteria:** The expected writes and no writes on refusal.
- **Status:** Passed (Host, 2026-11-14): CMP-21-S01 to CMP-21-S04, CMP-22-S01 and CMP-23-S01 against a mocked register bus. The `p 34` case is covered by the equivalent upper-port input case for GPIO 35 (CMP-22-S01).

### VER-CMP-13 — mimmo.c unit
- **Type:** Verification
- **Verifies:** CMP-24, CMP-25, CMP-26, CMP-27
- **Method:** Test
- **Level:** Unit
- **Environment:** QEMU, Host
- **Procedure:** As VER-SW-13.
- **Evidence:** @VER-SYS-08
- **Pass criteria:** As VER-SW-13.
- **Status:** Passed (QEMU). Passed (Host, 2026-11-14): CMP-24-S02, CMP-25-S01 to CMP-25-S03 and CMP-26-S02 (the self test on the simulated CPU). `fault()` itself (CMP-27) is checked on the target only.

### VER-CMP-14 — panic.c unit
- **Type:** Verification
- **Verifies:** CMP-28, CMP-29
- **Method:** Test
- **Level:** Unit
- **Environment:** QEMU, Host
- **Procedure:** As VER-SW-14.
- **Evidence:** @VER-SUB-17
- **Pass criteria:** As VER-SW-14.
- **Status:** Partial. Passed (Host, 2026-11-14): CMP-28-S01, CMP-28-S02 and CMP-29-S02 (report formats for every frame kind, the reboot write). The nested case is pending.

### VER-CMP-15 — lib.c unit
- **Type:** Verification
- **Verifies:** CMP-30, CMP-31
- **Method:** Test
- **Level:** Unit
- **Environment:** Host, QEMU
- **Procedure:** Compile `lib.c` for the host (renamed symbols) and compare `memset` (lengths 0–64), `memcpy` (0–32 at an offset) and `strlen` (4 strings) with glibc. Check `udelay` through the tick ratio in `s`.
- **Evidence:** @VER-CMP-15
- **Pass criteria:** 0 failures; 9–11 ticks.
- **Status:** Passed (Host, QEMU). On the host `udelay` is also checked directly, across CCOUNT wrap-around (CMP-31-S02), and against the tick (CMP-13-S04).

### VER-CMP-16 — main.c unit
- **Type:** Verification
- **Verifies:** CMP-32
- **Method:** Test
- **Level:** Unit
- **Environment:** QEMU, Host
- **Procedure:** Boot normally and in blink mode.
- **Evidence:** @VER-SYS-18
- **Pass criteria:** As VER-SYS-06 and VER-SYS-18.
- **Status:** Passed (QEMU). Passed (Host, 2026-11-14): CMP-32-S02 (banner, interrupt set-up, monitor entry). Blink mode is checked on the target only.

### VER-CMP-17 — Header units
- **Type:** Verification
- **Verifies:** CMP-37, CMP-38, CMP-39
- **Method:** Inspection
- **Level:** Unit
- **Environment:** Host
- **Procedure:** Review the headers against IF-06, IF-07, IF-12, IF-13 and HW-13; the `_Static_assert`s cover the frames.
- **Evidence:** Review notes; successful compile.
- **Pass criteria:** All values match.
- **Status:** Passed (Host).

### VER-CMP-18 — mkimage unit
- **Type:** Verification
- **Verifies:** CMP-33
- **Method:** Test
- **Level:** Unit
- **Environment:** Host
- **Procedure:** Run every example in image.feature, covering the valid and invalid inputs.
- **Evidence:** @VER-CMP-18
- **Pass criteria:** The exit status and output as specified.
- **Status:** Passed (Host, 2026-11-14). As VER-SW-16.

### VER-CMP-19 — Linker script and Makefile units
- **Type:** Verification
- **Verifies:** CMP-34, CMP-35
- **Method:** Inspection
- **Level:** Unit
- **Environment:** Host
- **Procedure:** Review both against CMP-34 and CMP-35. Touch a header and confirm the C objects rebuild.
- **Evidence:** Review notes.
- **Pass criteria:** As specified.
- **Status:** Passed (Host).

### VER-CMP-20 — Toolchain script unit
- **Type:** Verification
- **Verifies:** CMP-36
- **Method:** Inspection
- **Level:** Unit
- **Environment:** Host
- **Procedure:** Review the script: POSIX `sh` constructs only, `set -e`, and clone steps guarded by `[ -d … ] ||`.
- **Evidence:** Review notes.
- **Pass criteria:** As specified.
- **Status:** Passed (Host).

### VER-CMP-21 — tracecheck unit
- **Type:** Verification
- **Verifies:** CMP-40
- **Method:** Test
- **Level:** Unit
- **Environment:** Host
- **Procedure:** Run `tools/tracecheck.py --self-test`, which checks each error class against small built-in fixtures, then run `--check` on the real docs.
- **Evidence:** @VER-CMP-21
- **Pass criteria:** The self test passes, and the real check exits 0.
- **Status:** Passed (Host).
