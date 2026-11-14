# Feature catalogue

Each feature has one Gherkin file in [`features/`](features/). Scenarios
carry tags for:

* the epic and feature (`@EP-06 @F-12`);
* the requirements they exercise (`@SYS-16 @SUB-EXC-03 …`);
* the verification entry they provide evidence for (`@VER-SYS-12`);
* the environment: `@host` (build machine only), `@qemu` (emulator with the
  real boot ROM), or `@hardware` (physical board needed).

Each scenario's name starts with its ID, `<REQ>-Snn` (see
[`README.md`](README.md#entry-format)).

Unit-level (`CMP`) scenarios for the C components live in
[`features/unit/`](features/unit/). These four files reuse the feature IDs
of the system-level files they refine. Their scenarios run on the host
against a simulated SoC, implemented by the GoogleTest suite in
[`../tests/gtest`](../tests/gtest):

| File | Components | Feature |
|---|---|---|
| [unit/io.feature](features/unit/io.feature) | `io.c` | F-06 |
| [unit/irq_timer_wdt.feature](features/unit/irq_timer_wdt.feature) | `irq.c`, `timer.c`, `wdt.c` | F-12 |
| [unit/monitor_panic_main.feature](features/unit/monitor_panic_main.feature) | `mimmo.c`, `panic.c`, `main.c` | F-08 |
| [unit/gpio_lib_printf.feature](features/unit/gpio_lib_printf.feature) | `gpio.c`, `lib.c`, `pp_printf.c` | F-09 |

| ID | Feature | Epic | File | Main requirements | Environments |
|---|---|---|---|---|---|
| F-01 | Build from source | EP-01 | [build.feature](features/build.feature) | SYS-01, SYS-02, SYS-03 | host |
| F-02 | Boot image generation | EP-01 | [image.feature](features/image.feature) | SYS-03, SYS-04, IF-01 | host |
| F-03 | Toolchain from source | EP-01 | [toolchain.feature](features/toolchain.feature) | SYS-25 | host |
| F-04 | Boot paths (flash and RAM) | EP-02 | [boot.feature](features/boot.feature) | SYS-04, SYS-05, SYS-06, SYS-08, SYS-23, SYS-26, SYS-27 | qemu, hardware |
| F-05 | Watchdog control | EP-02 | [watchdog.feature](features/watchdog.feature) | SYS-09 | qemu, hardware |
| F-06 | Console I/O | EP-03 | [console.feature](features/console.feature) | SYS-06, SYS-07, SYS-18 | qemu, hardware |
| F-07 | Formatted output | EP-03 | [printf.feature](features/printf.feature) | SUB-CON-04 | host, qemu |
| F-08 | Memory monitor | EP-04 | [monitor.feature](features/monitor.feature) | SYS-10, SYS-11, SYS-31 | qemu |
| F-09 | GPIO control | EP-05 | [gpio.feature](features/gpio.feature) | SYS-12, SYS-13, SYS-14 | qemu, hardware |
| F-10 | Blink mode | EP-05 | [blink.feature](features/blink.feature) | SYS-22 | qemu, hardware |
| F-11 | Register windows and alloca | EP-06 | [register_windows.feature](features/register_windows.feature) | SYS-15 | qemu |
| F-12 | Interrupts | EP-06 | [interrupts.feature](features/interrupts.feature) | SYS-16, SYS-18 | qemu |
| F-13 | Timekeeping | EP-06 | [timekeeping.feature](features/timekeeping.feature) | SYS-17 | qemu, hardware |
| F-14 | Faults and recovery | EP-07 | [faults.feature](features/faults.feature) | SYS-19, SYS-20, SYS-30 | qemu, hardware |
| F-15 | Self test | EP-08 | [self_test.feature](features/self_test.feature) | SYS-21 | qemu, hardware |
| F-16 | Emulation and stress | EP-08 | [emulation.feature](features/emulation.feature) | SYS-24 | qemu |
| F-17 | Documentation | EP-09 | [documentation.feature](features/documentation.feature) | SYS-28, SYS-32 | host |
| F-18 | Stakeholder acceptance | EP-01…EP-09 | [acceptance.feature](features/acceptance.feature) | STK-01 … STK-20 | host, qemu, hardware |

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
