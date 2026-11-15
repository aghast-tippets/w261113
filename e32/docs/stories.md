# User stories

Record. Every story, whatever its status; nothing is deleted. What is left
to do is in [`backlog.md`](backlog.md). Process:
[`bdd-framework.md`](bdd-framework.md) (v2.0).

Status: 💡 Proposed · ⏳ Open · ✅ Done · ⛔ RETIRED. A story is Done when
every Test-verified requirement that traces to it (directly, or through
Derives from) has a Rule whose scenarios are all ✅ in
[`traceability.md`](traceability.md).

Actors are those of [`actors.md`](actors.md); the narrative names the actor's
role, as the v1 stories did.

## Index

| ID | Title | Epic | Actor | Priority | Status |
|---|---|---|---|---|---|
| US-01 | One-command build | EP-01 | ACT-H1 | Must | ⏳ Open |
| US-02 | Warning-free build with size report | EP-01 | ACT-H1 | Must | ⏳ Open |
| US-03 | Image generated automatically | EP-01 | ACT-H1 | Must | ⏳ Open |
| US-04 | Reproducible toolchain | EP-01 | ACT-H4 | Must | ⏳ Open |
| US-05 | Run from RAM over serial | EP-02 | ACT-H1 | Must | ⏳ Open |
| US-06 | Run from flash at every reset | EP-02 | ACT-H1 | Must | ⏳ Open |
| US-07 | No spontaneous resets | EP-02 | ACT-H3 | Must | ⏳ Open |
| US-08 | Fits a basic board | EP-02 | ACT-H1 | Must | ⏳ Open |
| US-09 | Banner and prompt | EP-03 | ACT-H3 | Must | ⏳ Open |
| US-10 | Line editing and no lost input | EP-03 | ACT-H3 | Must | ⏳ Open |
| US-11 | printf | EP-03 | ACT-H1 | Must | ⏳ Open |
| US-12 | Read, write and dump memory | EP-04 | ACT-H3 | Must | ⏳ Open |
| US-13 | Safe error handling | EP-04 | ACT-H3 | Must | ⏳ Open |
| US-14 | Call code | EP-04 | ACT-H3 | Must | ⏳ Open |
| US-29 | Uptime and interrupt counts | EP-04 | ACT-H3 | Must | ⏳ Open |
| US-15 | Drive and read pins | EP-05 | ACT-H3 | Must | ⏳ Open |
| US-16 | Dangerous pins refused | EP-05 | ACT-H3 | Must | ⏳ Open |
| US-17 | Blink without a console | EP-05 | ACT-H3 | Must | ⏳ Open |
| US-18 | Ordinary C just works | EP-06 | ACT-H1 | Must | ⏳ Open |
| US-19 | Attach handlers to interrupts | EP-06 | ACT-H1 | Must | ⏳ Open |
| US-20 | Time base | EP-06 | ACT-H1 | Must | ⏳ Open |
| US-21 | Critical sections | EP-06 | ACT-H1 | Must | ⏳ Open |
| US-22 | Crash report | EP-07 | ACT-H1 | Must | ⏳ Open |
| US-23 | Reboot after a crash | EP-07 | ACT-H1 | Must | ⏳ Open |
| US-24 | Self test | EP-08 | ACT-H3 | Must | ⏳ Open |
| US-25 | Verify without hardware | EP-08 | ACT-H3 | Must | ⏳ Open |
| US-26 | Provoke faults on purpose | EP-08 | ACT-H3 | Must | ⏳ Open |
| US-27 | Learn the system | EP-09 | ACT-H2 | Must | ✅ Done |
| US-28 | Traceable requirements | EP-09 | ACT-H4 | Must | ✅ Done |


## US-01 — One-command build
- **Epic:** EP-01 · **Actor:** ACT-H1 Firmware developer · **Priority:** Must
- **Story:** As a developer, I want to build the firmware with a single `make`
  using only a bare cross-compiler, so that I depend on no vendor SDK or C
  library.
- **Acceptance criteria → requirements:**
  1. `make` in a clean tree produces `e32.elf` and `e32.bin`. → SUB-BLD-01
  2. The link map lists no library members except, optionally, libgcc. →
     SUB-BLD-01
  3. No call or jump targets the boot ROM address range. → SYS-08
- **Refined by:** STK-01, STK-18 · **Feature(s):** FEAT-001, FEAT-002, FEAT-003, FEAT-004, FEAT-005, FEAT-006, FEAT-007, FEAT-008, FEAT-013, FEAT-015, FEAT-018
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-02 — Warning-free build with size report
- **Epic:** EP-01 · **Actor:** ACT-H1 Firmware developer · **Priority:** Must
- **Story:** As a developer, I want a warning-free build that reports the
  section sizes, so that I notice regressions immediately.
- **Acceptance criteria → requirements:**
  1. Zero lines containing `warning`, and a `size` summary line. → SYS-02
- **Refined by:** STK-01 · **Feature(s):** FEAT-001, FEAT-002, FEAT-003, FEAT-005, FEAT-006, FEAT-007, FEAT-008, FEAT-013
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-03 — Image generated automatically
- **Epic:** EP-01 · **Actor:** ACT-H1 Firmware developer · **Priority:** Must
- **Story:** As a developer, I want the ELF converted into a boot-ROM image as
  part of the build, so that I can load or flash it directly.
- **Acceptance criteria → requirements:**
  1. A valid image is decoded by an independent implementation; The real
     boot ROM accepts the image; Invalid input is rejected; Unloadable ELF
     files are rejected; Header bytes are as specified; The checksum is the
     last byte of a 16-byte block. → CMP-33, HW-11, SW-IMG-01, SW-IMG-03,
     SW-IMG-04, SW-IMG-05
- **Refined by:** STK-03, STK-04 · **Feature(s):** FEAT-001, FEAT-004, FEAT-005, FEAT-006, FEAT-007, FEAT-008, FEAT-009, FEAT-014, FEAT-015, FEAT-016, FEAT-018, FEAT-019, FEAT-025
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-04 — Reproducible toolchain
- **Epic:** EP-01 · **Actor:** ACT-H4 Maintainer · **Priority:** Must
- **Story:** As a maintainer, I want a script that builds the cross-compiler
  from pinned sources, so that anyone can reproduce the exact toolchain.
- **Acceptance criteria → requirements:**
  1. The script builds a working C toolchain; A second run does not clone
     again. → CMP-36
- **Refined by:** STK-02 · **Feature(s):** FEAT-010, FEAT-011, FEAT-012, FEAT-013
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-05 — Run from RAM over serial
- **Epic:** EP-02 · **Actor:** ACT-H1 Firmware developer · **Priority:** Must
- **Story:** As a developer, I want to load and start the firmware in RAM over
  the serial port, so that I iterate without writing flash.
- **Acceptance criteria → requirements:**
  1. RAM boot through ROM download mode. → IF-04
- **Refined by:** STK-03 · **Feature(s):** FEAT-001, FEAT-004, FEAT-005, FEAT-006, FEAT-007, FEAT-008, FEAT-014, FEAT-015, FEAT-016, FEAT-018, FEAT-025
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-06 — Run from flash at every reset
- **Epic:** EP-02 · **Actor:** ACT-H1 Firmware developer · **Priority:** Must
- **Story:** As a developer, I want to store the firmware in flash at
  `0x1000`, so that it starts on its own after every reset.
- **Acceptance criteria → requirements:**
  1. Flash boot through the ROM; Flash with make flash on a board. → HW-11,
     SW-BLD-03
- **Refined by:** STK-04 · **Feature(s):** FEAT-001, FEAT-005, FEAT-006, FEAT-007, FEAT-008, FEAT-014, FEAT-016, FEAT-017, FEAT-019
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-07 — No spontaneous resets
- **Epic:** EP-02 · **Actor:** ACT-H3 Bench operator / tester · **Priority:** Must
- **Story:** As an operator, I want the board to stay up indefinitely, so that
  my monitor session is not interrupted by watchdogs the ROM armed.
- **Acceptance criteria → requirements:**
  1. An armed watchdog is disabled at startup; Negative control: without
     wdt_disable the chip keeps resetting; A board stays up. → CMP-14,
     SYS-09
- **Refined by:** STK-12 · **Feature(s):** FEAT-005, FEAT-020, FEAT-021, FEAT-022, FEAT-023, FEAT-024, FEAT-025
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-08 — Fits a basic board
- **Epic:** EP-02 · **Actor:** ACT-H1 Firmware developer · **Priority:** Must
- **Story:** As a developer, I want the firmware to run from internal SRAM
  only, so that the cheapest ESP32 boards without PSRAM work.
- **Acceptance criteria → requirements:**
  1. Firmware runs from internal SRAM only. → HW-09
- **Refined by:** STK-17 · **Feature(s):** FEAT-002, FEAT-003, FEAT-004, FEAT-016, FEAT-025
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-09 — Banner and prompt
- **Epic:** EP-03 · **Actor:** ACT-H3 Bench operator / tester · **Priority:** Must
- **Story:** As an operator, I want a banner and a prompt at 115200 8N1 when
  the board starts, so that I know it is alive and ready.
- **Acceptance criteria → requirements:**
  1. Banner and prompt after boot. → IF-03
- **Refined by:** STK-05 · **Feature(s):** FEAT-003, FEAT-005, FEAT-015, FEAT-016, FEAT-017, FEAT-018, FEAT-019, FEAT-026, FEAT-027, FEAT-028, FEAT-029, FEAT-030, FEAT-031, FEAT-032, FEAT-033, FEAT-034, FEAT-036, FEAT-047
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-10 — Line editing and no lost input
- **Epic:** EP-03 · **Actor:** ACT-H3 Bench operator / tester · **Priority:** Must
- **Story:** As an operator, I want to correct typing with backspace and to
  paste lines while the firmware is busy, so that no input is lost or mangled.
- **Acceptance criteria → requirements:**
  1. Backspace erases the last character; Input typed while busy is kept. →
     CMP-16, CMP-17
- **Refined by:** STK-06, STK-19 · **Feature(s):** FEAT-026, FEAT-027, FEAT-028, FEAT-030, FEAT-035, FEAT-036, FEAT-039, FEAT-047, FEAT-056, FEAT-057, FEAT-058
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-11 — printf
- **Epic:** EP-03 · **Actor:** ACT-H1 Firmware developer · **Priority:** Must
- **Story:** As an integrator, I want a `printf` with the common integer,
  string and pointer conversions, so that application output is easy to write.
- **Acceptance criteria → requirements:**
  1. pp_sprintf matches ISO C for the supported subset; Cases that differ
     from or extend ISO C; Pointer and padded formats on the target. →
     CMP-19, SW-FMT-01
- **Refined by:** STK-05 · **Feature(s):** FEAT-003, FEAT-005, FEAT-015, FEAT-016, FEAT-017, FEAT-018, FEAT-019, FEAT-026, FEAT-027, FEAT-028, FEAT-029, FEAT-030, FEAT-031, FEAT-032, FEAT-033, FEAT-034, FEAT-036, FEAT-047
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-12 — Read, write and dump memory
- **Epic:** EP-04 · **Actor:** ACT-H3 Bench operator / tester · **Priority:** Must
- **Story:** As an operator, I want to read, write and dump 32-bit words at
  any address, so that I can inspect and poke registers and RAM.
- **Acceptance criteria → requirements:**
  1. Write then read a word of RAM; Dump defaults to 16 words, 4 per line;
     Dump with a count. → CMP-24, SW-MON-03, SYS-10
- **Refined by:** STK-06 · **Feature(s):** FEAT-003, FEAT-027, FEAT-028, FEAT-029, FEAT-031, FEAT-032, FEAT-033, FEAT-035, FEAT-036, FEAT-037, FEAT-038, FEAT-039, FEAT-069, FEAT-073
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-13 — Safe error handling
- **Epic:** EP-04 · **Actor:** ACT-H3 Bench operator / tester · **Priority:** Must
- **Story:** As an operator, I want malformed or unaligned commands rejected
  with a short hint, so that a typo never pokes memory.
- **Acceptance criteria → requirements:**
  1. Malformed commands are rejected. → SUB-MON-02
- **Refined by:** STK-06 · **Feature(s):** FEAT-035, FEAT-036, FEAT-037, FEAT-039
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-14 — Call code
- **Epic:** EP-04 · **Actor:** ACT-H3 Bench operator / tester · **Priority:** Must
- **Story:** As an operator, I want to call a function at a given address, so
  that I can run code I loaded or try out a routine.
- **Acceptance criteria → requirements:**
  1. Call a function by address. → SYS-10
- **Refined by:** STK-06 · **Feature(s):** FEAT-003, FEAT-027, FEAT-028, FEAT-029, FEAT-031, FEAT-032, FEAT-033, FEAT-035, FEAT-036, FEAT-037, FEAT-038, FEAT-039, FEAT-069, FEAT-073
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-29 — Uptime and interrupt counts
- **Epic:** EP-04 · **Actor:** ACT-H3 Bench operator / tester · **Priority:** Must
- **Story:** As an operator, I want to see the uptime and per-line interrupt
  counts, so that I can tell whether interrupts are firing.
- **Acceptance criteria → requirements:**
  1. Interrupt statistics. → SW-MON-06
- **Refined by:** STK-08, STK-09 · **Feature(s):** FEAT-004, FEAT-005, FEAT-015, FEAT-018, FEAT-035, FEAT-036, FEAT-037, FEAT-038, FEAT-047, FEAT-055, FEAT-056, FEAT-057, FEAT-058, FEAT-060, FEAT-061, FEAT-063, FEAT-065, FEAT-069, FEAT-073
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-15 — Drive and read pins
- **Epic:** EP-05 · **Actor:** ACT-H3 Bench operator / tester · **Priority:** Must
- **Story:** As an operator, I want to set a pin high or low and read a pin
  from the monitor, so that I can test the board's wiring.
- **Acceptance criteria → requirements:**
  1. Drive a GPIO output; Read a GPIO input; GPIO command paths in the
     emulator. → SUB-GPIO-01, SW-GPIO-03, SW-GPIO-05
- **Refined by:** STK-07 · **Feature(s):** FEAT-040, FEAT-041, FEAT-042, FEAT-043, FEAT-044, FEAT-049
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-16 — Dangerous pins refused
- **Epic:** EP-05 · **Actor:** ACT-H3 Bench operator / tester · **Priority:** Must
- **Story:** As an operator, I want the firmware to refuse the flash pins and
  output on input-only pins, so that I can't brick the session or the board.
- **Acceptance criteria → requirements:**
  1. Refused pins. → SW-GPIO-01
- **Refined by:** STK-07 · **Feature(s):** FEAT-040, FEAT-041, FEAT-042, FEAT-043, FEAT-044, FEAT-049
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-17 — Blink without a console
- **Epic:** EP-05 · **Actor:** ACT-H3 Bench operator / tester · **Priority:** Must
- **Story:** As an operator without a serial connection, I want a build mode
  that blinks the LED, so that I can see the firmware running.
- **Acceptance criteria → requirements:**
  1. The LED state alternates every half second; The LED blinks on a board.
     → CMP-32, HW-06
- **Refined by:** STK-16 · **Feature(s):** FEAT-036, FEAT-045, FEAT-046, FEAT-047, FEAT-048, FEAT-061, FEAT-063
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-18 — Ordinary C just works
- **Epic:** EP-06 · **Actor:** ACT-H1 Firmware developer · **Priority:** Must
- **Story:** As a developer, I want deep recursion and variable-length arrays
  to work as in hosted C, so that I don't have to know about register windows.
- **Acceptance criteria → requirements:**
  1. Recursion 200 frames deep; call12 frames are spilled and filled; A
     variable-length array with its caller spilled; Stress with an alloca
     counter. → CMP-03, CMP-04, CMP-07, IF-15
- **Refined by:** STK-11 · **Feature(s):** FEAT-004, FEAT-005, FEAT-015, FEAT-018, FEAT-050, FEAT-051, FEAT-052, FEAT-053, FEAT-054, FEAT-057, FEAT-065
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-19 — Attach handlers to interrupts
- **Epic:** EP-06 · **Actor:** ACT-H1 Firmware developer · **Priority:** Must
- **Story:** As an integrator, I want to route a peripheral to a CPU interrupt
  line and attach a C handler, so that my code reacts to events.
- **Acceptance criteria → requirements:**
  1. Heavy interrupt load leaves computations intact; Initialisation
     disconnects every matrix source; Only level-1 lines can be requested;
     An enabled line without a handler is disabled; The tick and the matrix-
     routed UART are counted; Waiting for input sleeps without losing a
     wake-up; A software interrupt runs its handler once. → CMP-08, CMP-10,
     CMP-11, CMP-12, SW-CON-04, SW-CON-06, SW-EXC-06
- **Refined by:** STK-08 · **Feature(s):** FEAT-004, FEAT-005, FEAT-015, FEAT-018, FEAT-035, FEAT-036, FEAT-037, FEAT-038, FEAT-047, FEAT-055, FEAT-056, FEAT-057, FEAT-058, FEAT-059, FEAT-065, FEAT-069, FEAT-073
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-20 — Time base
- **Epic:** EP-06 · **Actor:** ACT-H1 Firmware developer · **Priority:** Must
- **Story:** As an integrator, I want a 100 Hz tick and microsecond delays, so
  that I can measure and wait for time.
- **Acceptance criteria → requirements:**
  1. The tick never stalls under load (regression); About ten ticks per 100
     ms delay; Uptime follows wall-clock time on a board. → CMP-13, CMP-31,
     HW-02
- **Refined by:** STK-09 · **Feature(s):** FEAT-005, FEAT-035, FEAT-036, FEAT-037, FEAT-038, FEAT-047, FEAT-056, FEAT-057, FEAT-058, FEAT-060, FEAT-061, FEAT-062, FEAT-063, FEAT-064, FEAT-069, FEAT-073
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-21 — Critical sections
- **Epic:** EP-06 · **Actor:** ACT-H1 Firmware developer · **Priority:** Must
- **Story:** As an integrator, I want `irq_save()`/`irq_restore()`, so that
  data shared with handlers is updated consistently.
- **Acceptance criteria → requirements:**
  1. Waiting for input sleeps without losing a wake-up. → SW-CON-06
- **Refined by:** STK-08 · **Feature(s):** FEAT-004, FEAT-005, FEAT-015, FEAT-018, FEAT-035, FEAT-036, FEAT-037, FEAT-038, FEAT-047, FEAT-055, FEAT-056, FEAT-057, FEAT-058, FEAT-065, FEAT-069, FEAT-073
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-22 — Crash report
- **Epic:** EP-07 · **Actor:** ACT-H1 Firmware developer · **Priority:** Must
- **Story:** As a developer, I want a crash to print the cause, PC and all
  registers, so that I can find the bug with `addr2line`.
- **Acceptance criteria → requirements:**
  1. Deliberate faults; Memory faults show the faulting address; High-level
     interrupts show their level; The report prints even when the stack
     pointer is unusable; The PC maps to a source line. → CMP-09, CMP-27,
     STK-10, SYS-19
- **Refined by:** STK-10 · **Feature(s):** FEAT-003, FEAT-005, FEAT-029, FEAT-031, FEAT-032, FEAT-033, FEAT-036, FEAT-037, FEAT-038, FEAT-057, FEAT-066, FEAT-067, FEAT-068, FEAT-069, FEAT-070, FEAT-071, FEAT-073
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-23 — Reboot after a crash
- **Epic:** EP-07 · **Actor:** ACT-H1 Firmware developer · **Priority:** Must
- **Story:** As a developer, I want to reboot with a key press after a crash,
  so that I don't need to reach for the reset button.
- **Acceptance criteria → requirements:**
  1. A key press reboots after a fault. → CMP-29
- **Refined by:** STK-10 · **Feature(s):** FEAT-036, FEAT-037, FEAT-038, FEAT-066, FEAT-067, FEAT-068, FEAT-069, FEAT-070, FEAT-071, FEAT-073
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-24 — Self test
- **Epic:** EP-08 · **Actor:** ACT-H3 Bench operator / tester · **Priority:** Must
- **Story:** As an operator, I want one command that checks the core
  mechanisms, so that I can confirm a board and a build in seconds.
- **Acceptance criteria → requirements:**
  1. Self test passes after a flash boot; Self test passes after a RAM boot;
     Self test passes on a basic board. → CMP-26, SYS-21
- **Refined by:** STK-14 · **Feature(s):** FEAT-036, FEAT-037, FEAT-038, FEAT-061, FEAT-063, FEAT-066, FEAT-069, FEAT-072, FEAT-073, FEAT-074
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-25 — Verify without hardware
- **Epic:** EP-08 · **Actor:** ACT-H3 Bench operator / tester · **Priority:** Must
- **Story:** As a tester, I want to run the firmware in QEMU with the real
  boot ROM, so that I can verify most requirements without a board.
- **Acceptance criteria → requirements:**
  1. Both QEMU invocations work; make clean removes all build outputs; make
     qemu boots to the monitor; The QEMU flash image has the right layout. →
     IF-16, SUB-BLD-05, SUB-VEN-01, SW-BLD-02
- **Refined by:** STK-13 · **Feature(s):** FEAT-003, FEAT-005, FEAT-075, FEAT-076, FEAT-077, FEAT-078, FEAT-079
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-26 — Provoke faults on purpose
- **Epic:** EP-08 · **Actor:** ACT-H3 Bench operator / tester · **Priority:** Must
- **Story:** As a tester, I want commands that raise each fault type, so that
  the fault handler can be verified on demand.
- **Acceptance criteria → requirements:**
  1. Deliberate faults. → CMP-27
- **Refined by:** STK-10, STK-14 · **Feature(s):** FEAT-036, FEAT-037, FEAT-038, FEAT-066, FEAT-067, FEAT-068, FEAT-069, FEAT-070, FEAT-071, FEAT-073
- **INVEST:** not yet assessed
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0

## US-27 — Learn the system
- **Epic:** EP-09 · **Actor:** ACT-H2 Learner · **Priority:** Must
- **Story:** As a learner, I want documentation that explains the boot,
  interrupt and fault paths and maps each file to the LPC1343 original, so
  that I can understand and modify everything.
- **Acceptance criteria → requirements:**
  1. README covers the required topics. → SUB-DOC-01
- **Refined by:** STK-15 · **Feature(s):** FEAT-080, FEAT-083
- **INVEST:** not yet assessed
- **Status:** ✅ Done
- **Completion record:** 2026-11-15 · Rules ✅: CMP-40 (CMP-40-S01-T01) · SW-DOC-01 (SW-DOC-01-S01-T01) · Other verification: VER-STK-12 Inspection: Passed
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0 · 2026-11-15 Done

## US-28 — Traceable requirements
- **Epic:** EP-09 · **Actor:** ACT-H4 Maintainer · **Priority:** Must
- **Story:** As a maintainer, I want every requirement linked to its parent
  and verification, with a checker, so that changes never leave orphans or
  untested requirements.
- **Acceptance criteria → requirements:**
  1. The trace check passes. → SW-DOC-01
- **Refined by:** STK-20 · **Feature(s):** FEAT-081, FEAT-082
- **INVEST:** not yet assessed
- **Status:** ✅ Done
- **Completion record:** 2026-11-15 · Rules ✅: CMP-40 (CMP-40-S01-T01) · SW-DOC-01 (SW-DOC-01-S01-T01) · Other verification: VER-STK-12 Inspection: Passed
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15 Migrated to framework v2.0 · 2026-11-15 Done
