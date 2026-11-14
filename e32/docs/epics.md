# Epics

An epic is a large body of work that delivers business value on its own.
Each epic lists the business requirements it serves, the roles involved, its
features (one `.feature` file each), its stories and the system requirements
it delivers.

---

## EP-01 — Build from source without an SDK

**Goal.** Turn the sources into a ROM-loadable image with nothing but a
bare cross-compiler, `make` and a host C compiler. Optionally, build that
cross-compiler from source too.

* **Business value:** BR-02 (vendor independence), BR-06 (original,
  distributable code)
* **Roles:** Developer, Maintainer
* **Features:** F-01 Build, F-02 Boot image generation, F-03 Toolchain from
  source
* **Stories:** US-01, US-02, US-03, US-04
* **System requirements:** SYS-01, SYS-02, SYS-03, SYS-25, SYS-29
* **Done when:** `make` on a clean tree yields `e32.elf` and `e32.bin` with
  no warnings; `esptool image-info` accepts the image; and the toolchain
  script reproduces the compiler.

## EP-02 — Boot and run on the ESP32

**Goal.** Take over from the boot ROM, whether it loaded the image from
flash or over UART. Set up a C environment, stop the watchdogs, and keep
running from internal SRAM only.

* **Business value:** BR-02, BR-03 (cheap commodity boards)
* **Roles:** Developer, Tester, Learner
* **Features:** F-04 Boot paths, F-05 Watchdog control
* **Stories:** US-05, US-06, US-07, US-08
* **System requirements:** SYS-04, SYS-05, SYS-08, SYS-09, SYS-23, SYS-26,
  SYS-27
* **Done when:** both boot paths reach the monitor prompt; there is no
  spontaneous reset for at least 60 s; and no ROM code is executed after the
  handover.

## EP-03 — Console input and output

**Goal.** Provide a dependable serial console: output with newline
translation, line input with editing, interrupt-driven reception that loses
nothing while the CPU is busy, and a small `printf`.

* **Business value:** BR-01 (learnable), BR-04 (foundation for projects)
* **Roles:** Operator, Integrator
* **Features:** F-06 Console, F-07 Formatted output
* **Stories:** US-09, US-10, US-11
* **System requirements:** SYS-06, SYS-07, SYS-18
* **Done when:** the banner and prompt appear at 115200 8N1; backspace
  works; 256 characters typed during busy work are all received; and the
  `printf` output matches ISO C for the supported subset.

## EP-04 — Interactive memory monitor (mimmo)

**Goal.** Let an operator read, write and dump any word, call code, and see
system statistics from a terminal: the ESP32 version of Rubini's `mimmo`.

* **Business value:** BR-01
* **Roles:** Operator, Learner, Tester
* **Features:** F-08 Monitor
* **Stories:** US-12, US-13, US-14, US-29
* **System requirements:** SYS-10, SYS-11, SYS-31
* **Done when:** every command produces its documented output, and every
  malformed line yields `?? (h for help)` with no side effects.

## EP-05 — GPIO control

**Goal.** Drive and read pins with flat numbers 0–39, select alternate
functions with AF0 always meaning GPIO, refuse dangerous pins, and offer a
blink mode for boards without a console.

* **Business value:** BR-01, BR-03
* **Roles:** Operator, Integrator
* **Features:** F-09 GPIO, F-10 Blink mode
* **Stories:** US-15, US-16, US-17
* **System requirements:** SYS-12, SYS-13, SYS-14, SYS-22
* **Done when:** the pin levels measured on hardware match the commands,
  and the flash pins and input-only pins are refused.

## EP-06 — Exception and interrupt handling

**Goal.** Replace the ROM's vectors with our own:

* register-window spill and fill, so deep C works;
* the alloca fix-up, so variable-length arrays work;
* level-1 interrupt entry and exit with C dispatch;
* interrupt-matrix routing;
* a 100 Hz tick that never stalls.

* **Business value:** BR-04
* **Roles:** Integrator, Developer, Learner, Tester
* **Features:** F-11 Register windows and alloca, F-12 Interrupts, F-13
  Timekeeping
* **Stories:** US-18, US-19, US-20, US-21
* **System requirements:** SYS-15, SYS-16, SYS-17
* **Done when:** a 200-deep recursion and a VLA with its caller spilled give
  correct results, and a 20 kHz tick interrupting that work produces no
  errors.

## EP-07 — Fault reporting and recovery

**Goal.** Turn any crash into a readable report (cause, PC, registers,
caller) printed from a private stack, then reboot on a key press.

* **Business value:** BR-04
* **Roles:** Developer, Operator, Tester
* **Features:** F-14 Faults
* **Stories:** US-22, US-23, US-26
* **System requirements:** SYS-19, SYS-20, SYS-30
* **Done when:** each fault type yields a correct report and a key press
  produces `rst:0x3 (SW_RESET)`.

## EP-08 — Verification and emulation

**Goal.** Make most of the verification possible without hardware: QEMU
with the real ROM, a built-in self test, a stress configuration, and
stakeholder acceptance scenarios.

* **Business value:** BR-05 (verifiable without hardware)
* **Roles:** Tester, Maintainer
* **Features:** F-15 Self test, F-16 Emulation and stress, F-18 Stakeholder
  acceptance
* **Stories:** US-24, US-25, US-26
* **System requirements:** SYS-21, SYS-24
* **Done when:** at least 80 % of the system requirements have a
  QEMU-executable verification, and the self test reports `all ok`.

## EP-09 — Documentation and traceability

**Goal.** Explain every part, mapped to the LPC1343 original. Keep the
requirements traceable from business need to unit, with a checker that
catches broken links.

* **Business value:** BR-01, BR-02 (long-term maintainability)
* **Roles:** Learner, Maintainer
* **Features:** F-17 Documentation
* **Stories:** US-27, US-28
* **System requirements:** SYS-28, SYS-32
* **Done when:** `tools/tracecheck.py --check` exits 0, and the README
  covers every topic listed in SYS-28.
