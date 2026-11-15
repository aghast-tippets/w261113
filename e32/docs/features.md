# Feature catalogue

Record index. A feature is one capability of one epic at one level, written
as one Gherkin file in [`features/<level>/`](features/). Inside it, every
requirement is one `Rule:` titled with its ID, with its EARS sentence as the
first description line; scenarios sit under the rule they illustrate and are
named `<REQ>-Snn`. See [`bdd-framework.md`](bdd-framework.md) §3.6.

Tags: the feature carries `@EP-nn @FEAT-nnn`; a rule carries `@<REQ>` and
`@US-nn` where it refines a story directly; scenarios inherit both and add
their environment (`@host`, `@qemu`, `@hardware`), `@pending` (not yet
automated), `@gtest` (implemented by GoogleTest rather than pytest-bdd),
the `@VER-…` entry they are evidence for, and the other requirements they
also exercise.

| ID | Capability | Epic | Level | File | Rules | Scenarios |
|---|---|---|---|---|---|---|
| FEAT-001 | Build from source | EP-01 | system | [system/build.feature](features/system/build.feature) | 4 | 2 |
| FEAT-002 | Build from source | EP-01 | subsystem | [subsystem/build.feature](features/subsystem/build.feature) | 3 | 2 |
| FEAT-003 | Build from source | EP-01 | software | [software/build.feature](features/software/build.feature) | 5 | 2 |
| FEAT-004 | Build from source | EP-01 | interface | [interface/build.feature](features/interface/build.feature) | 1 | 1 |
| FEAT-005 | Build from source | EP-01 | unit | [unit/build.feature](features/unit/build.feature) | 6 | 4 |
| FEAT-006 | Boot image generation | EP-01 | subsystem | [subsystem/image.feature](features/subsystem/image.feature) | 1 | 0 |
| FEAT-007 | Boot image generation | EP-01 | software | [software/image.feature](features/software/image.feature) | 6 | 4 |
| FEAT-008 | Boot image generation | EP-01 | interface | [interface/image.feature](features/interface/image.feature) | 1 | 0 |
| FEAT-009 | Boot image generation | EP-01 | unit | [unit/image.feature](features/unit/image.feature) | 1 | 1 |
| FEAT-010 | Toolchain from source | EP-01 | system | [system/toolchain.feature](features/system/toolchain.feature) | 1 | 0 |
| FEAT-011 | Toolchain from source | EP-01 | subsystem | [subsystem/toolchain.feature](features/subsystem/toolchain.feature) | 1 | 0 |
| FEAT-012 | Toolchain from source | EP-01 | unit | [unit/toolchain.feature](features/unit/toolchain.feature) | 1 | 2 |
| FEAT-013 | Stakeholder acceptance: Build from source without an SDK | EP-01 | acceptance | [acceptance/build.feature](features/acceptance/build.feature) | 2 | 2 |
| FEAT-014 | Boot paths (flash and RAM) | EP-02 | system | [system/boot.feature](features/system/boot.feature) | 4 | 0 |
| FEAT-015 | Boot paths (flash and RAM) | EP-02 | subsystem | [subsystem/boot.feature](features/subsystem/boot.feature) | 2 | 0 |
| FEAT-016 | Boot paths (flash and RAM) | EP-02 | hardware | [hardware/boot.feature](features/hardware/boot.feature) | 4 | 3 |
| FEAT-017 | Boot paths (flash and RAM) | EP-02 | software | [software/boot.feature](features/software/boot.feature) | 2 | 2 |
| FEAT-018 | Boot paths (flash and RAM) | EP-02 | interface | [interface/boot.feature](features/interface/boot.feature) | 2 | 2 |
| FEAT-019 | Boot paths (flash and RAM) | EP-02 | unit | [unit/boot.feature](features/unit/boot.feature) | 1 | 2 |
| FEAT-020 | Watchdog control | EP-02 | system | [system/watchdog.feature](features/system/watchdog.feature) | 1 | 2 |
| FEAT-021 | Watchdog control | EP-02 | subsystem | [subsystem/watchdog.feature](features/subsystem/watchdog.feature) | 1 | 0 |
| FEAT-022 | Watchdog control | EP-02 | software | [software/watchdog.feature](features/software/watchdog.feature) | 1 | 0 |
| FEAT-023 | Watchdog control | EP-02 | interface | [interface/watchdog.feature](features/interface/watchdog.feature) | 1 | 0 |
| FEAT-024 | Watchdog control | EP-02 | unit | [unit/watchdog.feature](features/unit/watchdog.feature) | 1 | 2 |
| FEAT-025 | Stakeholder acceptance: Boot and run on the ESP32 | EP-02 | acceptance | [acceptance/boot.feature](features/acceptance/boot.feature) | 3 | 3 |
| FEAT-026 | Console I/O | EP-03 | system | [system/console.feature](features/system/console.feature) | 3 | 1 |
| FEAT-027 | Console I/O | EP-03 | subsystem | [subsystem/console.feature](features/subsystem/console.feature) | 3 | 0 |
| FEAT-028 | Console I/O | EP-03 | software | [software/console.feature](features/software/console.feature) | 4 | 4 |
| FEAT-029 | Console I/O | EP-03 | interface | [interface/console.feature](features/interface/console.feature) | 2 | 1 |
| FEAT-030 | Console I/O | EP-03 | unit | [unit/console.feature](features/unit/console.feature) | 3 | 9 |
| FEAT-031 | Formatted output | EP-03 | subsystem | [subsystem/printf.feature](features/subsystem/printf.feature) | 1 | 0 |
| FEAT-032 | Formatted output | EP-03 | software | [software/printf.feature](features/software/printf.feature) | 2 | 2 |
| FEAT-033 | Formatted output | EP-03 | unit | [unit/printf.feature](features/unit/printf.feature) | 2 | 2 |
| FEAT-034 | Stakeholder acceptance: Console input and output | EP-03 | acceptance | [acceptance/console.feature](features/acceptance/console.feature) | 1 | 1 |
| FEAT-035 | Memory monitor | EP-04 | system | [system/monitor.feature](features/system/monitor.feature) | 3 | 3 |
| FEAT-036 | Memory monitor | EP-04 | subsystem | [subsystem/monitor.feature](features/subsystem/monitor.feature) | 3 | 1 |
| FEAT-037 | Memory monitor | EP-04 | software | [software/monitor.feature](features/software/monitor.feature) | 4 | 3 |
| FEAT-038 | Memory monitor | EP-04 | unit | [unit/monitor.feature](features/unit/monitor.feature) | 2 | 5 |
| FEAT-039 | Stakeholder acceptance: Interactive memory monitor (mimmo) | EP-04 | acceptance | [acceptance/monitor.feature](features/acceptance/monitor.feature) | 1 | 1 |
| FEAT-040 | GPIO control | EP-05 | system | [system/gpio.feature](features/system/gpio.feature) | 3 | 0 |
| FEAT-041 | GPIO control | EP-05 | subsystem | [subsystem/gpio.feature](features/subsystem/gpio.feature) | 2 | 1 |
| FEAT-042 | GPIO control | EP-05 | software | [software/gpio.feature](features/software/gpio.feature) | 5 | 4 |
| FEAT-043 | GPIO control | EP-05 | interface | [interface/gpio.feature](features/interface/gpio.feature) | 1 | 0 |
| FEAT-044 | GPIO control | EP-05 | unit | [unit/gpio.feature](features/unit/gpio.feature) | 3 | 6 |
| FEAT-045 | Blink mode | EP-05 | system | [system/blink.feature](features/system/blink.feature) | 1 | 0 |
| FEAT-046 | Blink mode | EP-05 | hardware | [hardware/blink.feature](features/hardware/blink.feature) | 1 | 1 |
| FEAT-047 | Blink mode | EP-05 | software | [software/blink.feature](features/software/blink.feature) | 1 | 0 |
| FEAT-048 | Blink mode | EP-05 | unit | [unit/blink.feature](features/unit/blink.feature) | 1 | 2 |
| FEAT-049 | Stakeholder acceptance: GPIO control | EP-05 | acceptance | [acceptance/gpio.feature](features/acceptance/gpio.feature) | 1 | 1 |
| FEAT-050 | Register windows and alloca | EP-06 | system | [system/register_windows.feature](features/system/register_windows.feature) | 1 | 0 |
| FEAT-051 | Register windows and alloca | EP-06 | subsystem | [subsystem/register_windows.feature](features/subsystem/register_windows.feature) | 2 | 0 |
| FEAT-052 | Register windows and alloca | EP-06 | software | [software/register_windows.feature](features/software/register_windows.feature) | 2 | 0 |
| FEAT-053 | Register windows and alloca | EP-06 | interface | [interface/register_windows.feature](features/interface/register_windows.feature) | 1 | 1 |
| FEAT-054 | Register windows and alloca | EP-06 | unit | [unit/register_windows.feature](features/unit/register_windows.feature) | 3 | 3 |
| FEAT-055 | Interrupts | EP-06 | system | [system/interrupts.feature](features/system/interrupts.feature) | 1 | 0 |
| FEAT-056 | Interrupts | EP-06 | subsystem | [subsystem/interrupts.feature](features/subsystem/interrupts.feature) | 2 | 0 |
| FEAT-057 | Interrupts | EP-06 | software | [software/interrupts.feature](features/software/interrupts.feature) | 10 | 3 |
| FEAT-058 | Interrupts | EP-06 | interface | [interface/interrupts.feature](features/interface/interrupts.feature) | 2 | 0 |
| FEAT-059 | Interrupts | EP-06 | unit | [unit/interrupts.feature](features/unit/interrupts.feature) | 4 | 9 |
| FEAT-060 | Timekeeping | EP-06 | system | [system/timekeeping.feature](features/system/timekeeping.feature) | 1 | 0 |
| FEAT-061 | Timekeeping | EP-06 | subsystem | [subsystem/timekeeping.feature](features/subsystem/timekeeping.feature) | 3 | 0 |
| FEAT-062 | Timekeeping | EP-06 | hardware | [hardware/timekeeping.feature](features/hardware/timekeeping.feature) | 1 | 1 |
| FEAT-063 | Timekeeping | EP-06 | software | [software/timekeeping.feature](features/software/timekeeping.feature) | 4 | 0 |
| FEAT-064 | Timekeeping | EP-06 | unit | [unit/timekeeping.feature](features/unit/timekeeping.feature) | 2 | 6 |
| FEAT-065 | Stakeholder acceptance: Exception and interrupt handling | EP-06 | acceptance | [acceptance/interrupts.feature](features/acceptance/interrupts.feature) | 2 | 2 |
| FEAT-066 | Faults and recovery | EP-07 | system | [system/faults.feature](features/system/faults.feature) | 3 | 3 |
| FEAT-067 | Faults and recovery | EP-07 | subsystem | [subsystem/faults.feature](features/subsystem/faults.feature) | 5 | 0 |
| FEAT-068 | Faults and recovery | EP-07 | hardware | [hardware/faults.feature](features/hardware/faults.feature) | 1 | 0 |
| FEAT-069 | Faults and recovery | EP-07 | software | [software/faults.feature](features/software/faults.feature) | 7 | 1 |
| FEAT-070 | Faults and recovery | EP-07 | unit | [unit/faults.feature](features/unit/faults.feature) | 4 | 6 |
| FEAT-071 | Stakeholder acceptance: Fault reporting and recovery | EP-07 | acceptance | [acceptance/faults.feature](features/acceptance/faults.feature) | 1 | 2 |
| FEAT-072 | Self test | EP-08 | system | [system/self_test.feature](features/system/self_test.feature) | 1 | 2 |
| FEAT-073 | Self test | EP-08 | software | [software/self_test.feature](features/software/self_test.feature) | 1 | 0 |
| FEAT-074 | Self test | EP-08 | unit | [unit/self_test.feature](features/unit/self_test.feature) | 1 | 2 |
| FEAT-075 | Emulation and stress | EP-08 | system | [system/emulation.feature](features/system/emulation.feature) | 1 | 0 |
| FEAT-076 | Emulation and stress | EP-08 | subsystem | [subsystem/emulation.feature](features/subsystem/emulation.feature) | 2 | 2 |
| FEAT-077 | Emulation and stress | EP-08 | software | [software/emulation.feature](features/software/emulation.feature) | 1 | 1 |
| FEAT-078 | Emulation and stress | EP-08 | interface | [interface/emulation.feature](features/interface/emulation.feature) | 1 | 1 |
| FEAT-079 | Stakeholder acceptance: Verification and emulation | EP-08 | acceptance | [acceptance/verification.feature](features/acceptance/verification.feature) | 1 | 1 |
| FEAT-080 | Documentation | EP-09 | subsystem | [subsystem/documentation.feature](features/subsystem/documentation.feature) | 1 | 2 |
| FEAT-081 | Documentation | EP-09 | software | [software/documentation.feature](features/software/documentation.feature) | 1 | 1 |
| FEAT-082 | Documentation | EP-09 | unit | [unit/documentation.feature](features/unit/documentation.feature) | 1 | 1 |
| FEAT-083 | Stakeholder acceptance: Documentation and traceability | EP-09 | acceptance | [acceptance/documentation.feature](features/acceptance/documentation.feature) | 1 | 1 |

## Retired

The v1 features were one file per capability, mixing levels. Framework v2.0
needs one level per file, so each was split; the v1 IDs are retired.

| ID | v1 feature | Replaced by | Date |
|---|---|---|---|
| F-01 | Build from source (build.feature) | FEAT-001, FEAT-002, FEAT-003, FEAT-004, FEAT-005 | 2026-11-15 |
| F-02 | Boot image generation (image.feature) | FEAT-006, FEAT-007, FEAT-008, FEAT-009 | 2026-11-15 |
| F-03 | Toolchain from source (toolchain.feature) | FEAT-010, FEAT-011, FEAT-012 | 2026-11-15 |
| F-04 | Boot paths (flash and RAM) (boot.feature) | FEAT-014, FEAT-015, FEAT-016, FEAT-017, FEAT-018, FEAT-019 | 2026-11-15 |
| F-05 | Watchdog control (watchdog.feature) | FEAT-020, FEAT-021, FEAT-022, FEAT-023, FEAT-024 | 2026-11-15 |
| F-06 | Console I/O (console.feature) | FEAT-026, FEAT-027, FEAT-028, FEAT-029, FEAT-030 | 2026-11-15 |
| F-07 | Formatted output (printf.feature) | FEAT-031, FEAT-032, FEAT-033 | 2026-11-15 |
| F-08 | Memory monitor (monitor.feature) | FEAT-035, FEAT-036, FEAT-037, FEAT-038 | 2026-11-15 |
| F-09 | GPIO control (gpio.feature) | FEAT-040, FEAT-041, FEAT-042, FEAT-043, FEAT-044 | 2026-11-15 |
| F-10 | Blink mode (blink.feature) | FEAT-045, FEAT-046, FEAT-047, FEAT-048 | 2026-11-15 |
| F-11 | Register windows and alloca (register_windows.feature) | FEAT-050, FEAT-051, FEAT-052, FEAT-053, FEAT-054 | 2026-11-15 |
| F-12 | Interrupts (interrupts.feature) | FEAT-055, FEAT-056, FEAT-057, FEAT-058, FEAT-059 | 2026-11-15 |
| F-13 | Timekeeping (timekeeping.feature) | FEAT-060, FEAT-061, FEAT-062, FEAT-063, FEAT-064 | 2026-11-15 |
| F-14 | Faults and recovery (faults.feature) | FEAT-066, FEAT-067, FEAT-068, FEAT-069, FEAT-070 | 2026-11-15 |
| F-15 | Self test (self_test.feature) | FEAT-072, FEAT-073, FEAT-074 | 2026-11-15 |
| F-16 | Emulation and stress (emulation.feature) | FEAT-075, FEAT-076, FEAT-077, FEAT-078 | 2026-11-15 |
| F-17 | Documentation (documentation.feature) | FEAT-080, FEAT-081, FEAT-082 | 2026-11-15 |
| F-18 | Stakeholder acceptance (acceptance.feature) | FEAT-013, FEAT-025, FEAT-034, FEAT-039, FEAT-049, FEAT-065, FEAT-071, FEAT-079, FEAT-083 | 2026-11-15 |

## Step vocabulary

The scenarios use one small, consistent set of steps, so that a single step
library can automate all of them in Phase 3.

**Given**

* `the firmware is built`: run `make` in a clean tree.
* `the firmware is booted in QEMU from flash`: run QEMU with machine
  `esp32` and `flash.img`, with the console on a pipe.
* `the firmware is loaded into RAM in QEMU download mode`: run QEMU with
  strap mode `0x0f`, then `esptool load-ram` over TCP.
* `the firmware is running on a board`: a physical ESP32, on `PORT`.
* `the monitor prompt is shown`: wait for `> ` after `Ready to get input`.
* `a build variant with <change>`: copy the tree, apply the change, build.

**When**

* `I enter "<line>"`: send the line followed by CR.
* `I send the bytes <hex>`: raw bytes, for control characters.
* `I press any key`: send one byte.
* `I wait <n> seconds`
* `I run "<command>"`: on the build host.

**Then**

* `the console shows "<text>"`: the text appears in the output after the
  last input.
* `the console shows a line matching /<regex>/`
* `the console does not show "<text>"`
* `the chip resets <n> times within <t> seconds`: count `rst:` lines from
  the ROM.
* `the command succeeds` / `the command fails with "<text>"`
* `the file <f> exists` / `the output of <command> contains "<text>"`
* `pin <n> measures <level>`: a hardware measurement with a meter or logic
  probe.
