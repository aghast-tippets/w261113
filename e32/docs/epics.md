# Epics

Record. Every epic, whatever its status; nothing is deleted. What is left to
do is in [`backlog.md`](backlog.md).

Status: 💡 Proposed · ⏳ Open · ✅ Done (all non-retired stories Done) · ⛔ RETIRED

## Index

| ID | Epic | Realises | Priority | Stories | Status |
|---|---|---|---|---|---|
| EP-01 | Build from source without an SDK | BR-02, BR-06 | Must | US-01, US-02, US-03, US-04 | ⏳ Open |
| EP-02 | Boot and run on the ESP32 | BR-02, BR-03 | Must | US-05, US-06, US-07, US-08 | ⏳ Open |
| EP-03 | Console input and output | BR-01, BR-04 | Must | US-09, US-10, US-11 | ⏳ Open |
| EP-04 | Interactive memory monitor (mimmo) | BR-01 | Must | US-12, US-13, US-14, US-29 | ⏳ Open |
| EP-05 | GPIO control | BR-01, BR-03 | Must | US-15, US-16, US-17 | ⏳ Open |
| EP-06 | Exception and interrupt handling | BR-04 | Must | US-18, US-19, US-20, US-21 | ⏳ Open |
| EP-07 | Fault reporting and recovery | BR-04 | Must | US-22, US-23 | ⏳ Open |
| EP-08 | Verification and emulation | BR-05 | Must | US-24, US-25, US-26 | ⏳ Open |
| EP-09 | Documentation and traceability | BR-01, BR-02 | Must | US-27, US-28 | ✅ Done |

## EP-01 — Build from source without an SDK
- **Goal:** Turn the sources into a ROM-loadable image with nothing but a bare
  cross-compiler, `make` and a host C compiler. Optionally, build that cross-
  compiler from source too.
- **Realises:** BR-02, BR-06 · **Priority:** Must
- **Stories:** US-01, US-02, US-03, US-04 (0 of 4 Done)
- **Business check:** VER-BR-02 (Inspection) for BR-02; VER-BR-06 (Inspection)
  for BR-06
- **Outcome sought:** `make` on a clean tree yields `e32.elf` and `e32.bin`
  with no warnings; `esptool image-info` accepts the image; and the toolchain
  script reproduces the compiler.
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15
  Migrated to framework v2.0

## EP-02 — Boot and run on the ESP32
- **Goal:** Take over from the boot ROM, whether it loaded the image from
  flash or over UART. Set up a C environment, stop the watchdogs, and keep
  running from internal SRAM only.
- **Realises:** BR-02, BR-03 · **Priority:** Must
- **Stories:** US-05, US-06, US-07, US-08 (0 of 4 Done)
- **Business check:** VER-BR-02 (Inspection) for BR-02; VER-BR-03 (Analysis)
  for BR-03
- **Outcome sought:** both boot paths reach the monitor prompt; there is no
  spontaneous reset for at least 60 s; and no ROM code is executed after the
  handover.
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15
  Migrated to framework v2.0

## EP-03 — Console input and output
- **Goal:** Provide a dependable serial console: output with newline
  translation, line input with editing, interrupt-driven reception that loses
  nothing while the CPU is busy, and a small `printf`.
- **Realises:** BR-01, BR-04 · **Priority:** Must
- **Stories:** US-09, US-10, US-11 (0 of 3 Done)
- **Business check:** VER-BR-01 (Analysis) for BR-01; VER-BR-04
  (Demonstration) for BR-04
- **Outcome sought:** the banner and prompt appear at 115200 8N1; backspace
  works; 256 characters typed during busy work are all received; and the
  `printf` output matches ISO C for the supported subset.
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15
  Migrated to framework v2.0

## EP-04 — Interactive memory monitor (mimmo)
- **Goal:** Let an operator read, write and dump any word, call code, and see
  system statistics from a terminal: the ESP32 version of Rubini's `mimmo`.
- **Realises:** BR-01 · **Priority:** Must
- **Stories:** US-12, US-13, US-14, US-29 (0 of 4 Done)
- **Business check:** VER-BR-01 (Analysis) for BR-01
- **Outcome sought:** every command produces its documented output, and every
  malformed line yields `?? (h for help)` with no side effects.
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15
  Migrated to framework v2.0

## EP-05 — GPIO control
- **Goal:** Drive and read pins with flat numbers 0–39, select alternate
  functions with AF0 always meaning GPIO, refuse dangerous pins, and offer a
  blink mode for boards without a console.
- **Realises:** BR-01, BR-03 · **Priority:** Must
- **Stories:** US-15, US-16, US-17 (0 of 3 Done)
- **Business check:** VER-BR-01 (Analysis) for BR-01; VER-BR-03 (Analysis) for
  BR-03
- **Outcome sought:** the pin levels measured on hardware match the commands,
  and the flash pins and input-only pins are refused.
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15
  Migrated to framework v2.0

## EP-06 — Exception and interrupt handling
- **Goal:** Replace the ROM's vectors with our own:
- **Realises:** BR-04 · **Priority:** Must
- **Stories:** US-18, US-19, US-20, US-21 (0 of 4 Done)
- **Business check:** VER-BR-04 (Demonstration) for BR-04
- **Outcome sought:** a 200-deep recursion and a VLA with its caller spilled
  give correct results, and a 20 kHz tick interrupting that work produces no
  errors.
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15
  Migrated to framework v2.0

## EP-07 — Fault reporting and recovery
- **Goal:** Turn any crash into a readable report (cause, PC, registers,
  caller) printed from a private stack, then reboot on a key press.
- **Realises:** BR-04 · **Priority:** Must
- **Stories:** US-22, US-23 (0 of 2 Done)
- **Business check:** VER-BR-04 (Demonstration) for BR-04
- **Outcome sought:** each fault type yields a correct report and a key press
  produces `rst:0x3 (SW_RESET)`.
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15
  Migrated to framework v2.0; US-26 removed from this epic's list (a story has
  one epic; stories.md files it under EP-08)

## EP-08 — Verification and emulation
- **Goal:** Make most of the verification possible without hardware: QEMU with
  the real ROM, a built-in self test, a stress configuration, and stakeholder
  acceptance scenarios.
- **Realises:** BR-05 · **Priority:** Must
- **Stories:** US-24, US-25, US-26 (0 of 3 Done)
- **Business check:** VER-BR-05 (Analysis) for BR-05
- **Outcome sought:** at least 80 % of the system requirements have a QEMU-
  executable verification, and the self test reports `all ok`.
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15
  Migrated to framework v2.0

## EP-09 — Documentation and traceability
- **Goal:** Explain every part, mapped to the LPC1343 original. Keep the
  requirements traceable from business need to unit, with a checker that
  catches broken links.
- **Realises:** BR-01, BR-02 · **Priority:** Must
- **Stories:** US-27, US-28 (2 of 2 Done)
- **Business check:** VER-BR-01 (Analysis) for BR-01; VER-BR-02 (Inspection)
  for BR-02
- **Outcome sought:** `tools/tracecheck.py --check` exits 0, and the README
  covers every topic listed in SYS-28.
- **Status:** ✅ Done
- **Completion record:** 2026-11-15 · US-27 Done · US-28 Done
- **History:** 2026-11-14 Approved (framework v1 baseline) · 2026-11-15
  Migrated to framework v2.0 · 2026-11-15 Done
