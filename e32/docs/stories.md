# User stories

Format: **As a** \<role\>, **I want** \<capability\>, **so that** \<benefit\>.
Each story traces to the stakeholder needs (`STK`) it expresses, and lists
acceptance criteria that point to Gherkin scenarios.

## EP-01 — Build from source without an SDK

### US-01 — One-command build
**As a** developer, **I want** to build the firmware with a single `make`
using only a bare cross-compiler, **so that** I depend on no vendor SDK or C
library.
*Traces to:* STK-01, STK-18
*Acceptance criteria:*
1. `make` in a clean tree produces `e32.elf` and `e32.bin`
   (build.feature: "Clean build produces the ELF and the image").
2. The link map lists no library members except, optionally, libgcc
   (build.feature: "Only libgcc may be linked").
3. No call or jump targets the boot ROM address range
   (build.feature: "No ROM code is referenced").

### US-02 — Warning-free build with size report
**As a** developer, **I want** a warning-free build that reports the section
sizes, **so that** I notice regressions immediately.
*Traces to:* STK-01
*Acceptance criteria:* zero lines containing `warning`, and a `size`
summary line (build.feature: "Build is warning-free").

### US-03 — Image generated automatically
**As a** developer, **I want** the ELF converted into a boot-ROM image as
part of the build, **so that** I can load or flash it directly.
*Traces to:* STK-03, STK-04
*Acceptance criteria:* all scenarios in image.feature.

### US-04 — Reproducible toolchain
**As a** maintainer, **I want** a script that builds the cross-compiler
from pinned sources, **so that** anyone can reproduce the exact toolchain.
*Traces to:* STK-02
*Acceptance criteria:* toolchain.feature.

## EP-02 — Boot and run

### US-05 — Run from RAM over serial
**As a** developer, **I want** to load and start the firmware in RAM over
the serial port, **so that** I iterate without writing flash.
*Traces to:* STK-03
*Acceptance criteria:* boot.feature: "RAM boot through ROM download mode".

### US-06 — Run from flash at every reset
**As a** developer, **I want** to store the firmware in flash at `0x1000`,
**so that** it starts on its own after every reset.
*Traces to:* STK-04
*Acceptance criteria:* boot.feature: "Flash boot through the ROM" and
"Flash with make flash on a board".

### US-07 — No spontaneous resets
**As an** operator, **I want** the board to stay up indefinitely, **so
that** my monitor session is not interrupted by watchdogs the ROM armed.
*Traces to:* STK-12
*Acceptance criteria:* watchdog.feature.

### US-08 — Fits a basic board
**As a** developer, **I want** the firmware to run from internal SRAM only,
**so that** the cheapest ESP32 boards without PSRAM work.
*Traces to:* STK-17
*Acceptance criteria:* boot.feature: "Firmware runs from internal SRAM only".

## EP-03 — Console I/O

### US-09 — Banner and prompt
**As an** operator, **I want** a banner and a prompt at 115200 8N1 when the
board starts, **so that** I know it is alive and ready.
*Traces to:* STK-05
*Acceptance criteria:* console.feature: "Banner and prompt after boot".

### US-10 — Line editing and no lost input
**As an** operator, **I want** to correct typing with backspace and to
paste lines while the firmware is busy, **so that** no input is lost or
mangled.
*Traces to:* STK-06, STK-19
*Acceptance criteria:* console.feature: "Backspace erases the last
character" and "Input typed while busy is kept".

### US-11 — printf
**As an** integrator, **I want** a `printf` with the common integer, string
and pointer conversions, **so that** application output is easy to write.
*Traces to:* STK-05
*Acceptance criteria:* printf.feature.

## EP-04 — Memory monitor

### US-12 — Read, write and dump memory
**As an** operator, **I want** to read, write and dump 32-bit words at any
address, **so that** I can inspect and poke registers and RAM.
*Traces to:* STK-06
*Acceptance criteria:* monitor.feature: read, write, dump scenarios.

### US-13 — Safe error handling
**As an** operator, **I want** malformed or unaligned commands rejected
with a short hint, **so that** a typo never pokes memory.
*Traces to:* STK-06
*Acceptance criteria:* monitor.feature: "Malformed commands are rejected".

### US-14 — Call code
**As an** operator, **I want** to call a function at a given address,
**so that** I can run code I loaded or try out a routine.
*Traces to:* STK-06
*Acceptance criteria:* monitor.feature: "Call a function by address".

### US-29 — Uptime and interrupt counts
**As an** operator, **I want** to see the uptime and per-line interrupt
counts, **so that** I can tell whether interrupts are firing.
*Traces to:* STK-08, STK-09
*Acceptance criteria:* monitor.feature: "Interrupt statistics".

## EP-05 — GPIO

### US-15 — Drive and read pins
**As an** operator, **I want** to set a pin high or low and read a pin
from the monitor, **so that** I can test the board's wiring.
*Traces to:* STK-07
*Acceptance criteria:* gpio.feature: output, input and alternate-function
scenarios.

### US-16 — Dangerous pins refused
**As an** operator, **I want** the firmware to refuse the flash pins and
output on input-only pins, **so that** I can't brick the session or the
board.
*Traces to:* STK-07
*Acceptance criteria:* gpio.feature: "Refused pins".

### US-17 — Blink without a console
**As an** operator without a serial connection, **I want** a build mode
that blinks the LED, **so that** I can see the firmware running.
*Traces to:* STK-16
*Acceptance criteria:* blink.feature.

## EP-06 — Exceptions and interrupts

### US-18 — Ordinary C just works
**As a** developer, **I want** deep recursion and variable-length arrays
to work as in hosted C, **so that** I don't have to know about register
windows.
*Traces to:* STK-11
*Acceptance criteria:* register_windows.feature.

### US-19 — Attach handlers to interrupts
**As an** integrator, **I want** to route a peripheral to a CPU interrupt
line and attach a C handler, **so that** my code reacts to events.
*Traces to:* STK-08
*Acceptance criteria:* interrupts.feature.

### US-20 — Time base
**As an** integrator, **I want** a 100 Hz tick and microsecond delays,
**so that** I can measure and wait for time.
*Traces to:* STK-09
*Acceptance criteria:* timekeeping.feature.

### US-21 — Critical sections
**As an** integrator, **I want** `irq_save()`/`irq_restore()`, **so that**
data shared with handlers is updated consistently.
*Traces to:* STK-08
*Acceptance criteria:* interrupts.feature: "Waiting for input sleeps
without losing a wake-up".

## EP-07 — Faults

### US-22 — Crash report
**As a** developer, **I want** a crash to print the cause, PC and all
registers, **so that** I can find the bug with `addr2line`.
*Traces to:* STK-10
*Acceptance criteria:* faults.feature: the fault report outline.

### US-23 — Reboot after a crash
**As a** developer, **I want** to reboot with a key press after a crash,
**so that** I don't need to reach for the reset button.
*Traces to:* STK-10
*Acceptance criteria:* faults.feature: "Key press reboots after a fault".

## EP-08 — Verification

### US-24 — Self test
**As an** operator, **I want** one command that checks the core mechanisms,
**so that** I can confirm a board and a build in seconds.
*Traces to:* STK-14
*Acceptance criteria:* self_test.feature.

### US-25 — Verify without hardware
**As a** tester, **I want** to run the firmware in QEMU with the real boot
ROM, **so that** I can verify most requirements without a board.
*Traces to:* STK-13
*Acceptance criteria:* emulation.feature.

### US-26 — Provoke faults on purpose
**As a** tester, **I want** commands that raise each fault type, **so
that** the fault handler can be verified on demand.
*Traces to:* STK-10, STK-14
*Acceptance criteria:* faults.feature: "Deliberate faults".

## EP-09 — Documentation

### US-27 — Learn the system
**As a** learner, **I want** documentation that explains the boot,
interrupt and fault paths and maps each file to the LPC1343 original,
**so that** I can understand and modify everything.
*Traces to:* STK-15
*Acceptance criteria:* documentation.feature: "README covers the
required topics".

### US-28 — Traceable requirements
**As a** maintainer, **I want** every requirement linked to its parent and
verification, with a checker, **so that** changes never leave orphans or
untested requirements.
*Traces to:* STK-20
*Acceptance criteria:* documentation.feature: "Trace check passes".

---

## Story map

| Epic | Stories |
|---|---|
| EP-01 | US-01, US-02, US-03, US-04 |
| EP-02 | US-05, US-06, US-07, US-08 |
| EP-03 | US-09, US-10, US-11 |
| EP-04 | US-12, US-13, US-14, US-29 |
| EP-05 | US-15, US-16, US-17 |
| EP-06 | US-18, US-19, US-20, US-21 |
| EP-07 | US-22, US-23 |
| EP-08 | US-24, US-25, US-26 |
| EP-09 | US-27, US-28 |
