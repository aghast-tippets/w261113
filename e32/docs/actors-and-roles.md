# Actors and roles

An **actor** is anyone or anything that interacts with e32 from outside a
given boundary. A **role** is the hat an actor wears while doing so. One
person can hold several roles, and one role can be filled by several actors.

## Human actors

| ID | Actor | Description | Typical roles |
|---|---|---|---|
| ACT-H1 | Firmware developer | Writes, builds and loads e32 firmware; extends it with application code. Has C and Unix experience, as in Rubini's prerequisites. | Developer, Integrator |
| ACT-H2 | Learner | A student following the package to understand bare-metal ESP32, chapter by chapter, as Rubini's students did with the LPC1343 notes. | Learner, Operator |
| ACT-H3 | Bench operator / tester | Connects a board, uses the serial monitor, runs the self test, and checks pins and faults on hardware. | Operator, Tester |
| ACT-H4 | Maintainer | Owns the package: toolchain pinning, documentation, verification status and releases. | Maintainer, Tester |

## System actors (external to the firmware)

| ID | Actor | Kind | Interaction |
|---|---|---|---|
| ACT-S1 | ESP32 boot ROM | Mask ROM firmware in the SoC | Loads the image from flash at `0x1000`, or over UART in download mode; checks the checksum; calls the entry point; prints its own boot lines on UART0. |
| ACT-S2 | ESP32 SoC peripherals | Hardware | UART0, GPIO matrix, IO_MUX, interrupt matrix, timer groups, RTC_CNTL. The firmware reads and writes their registers. |
| ACT-S3 | Xtensa LX6 CPU core | Hardware | Executes the code. Raises window, alloca, interrupt and fault exceptions through `VECBASE`. |
| ACT-S4 | Host build machine | Computer | Runs the cross-compiler, `make`, `tools/mkimage` and the trace checker. |
| ACT-S5 | Cross toolchain | Software | `xtensa-esp32-elf-gcc`/binutils, built by `tools/build-toolchain.sh` or supplied by the developer. |
| ACT-S6 | esptool | Host software | The serial transport only: `load_ram` and `write_flash` through the ROM protocol. |
| ACT-S7 | Serial terminal | Host software | `minicom` or similar, on the USB-serial port at 115200 8N1. |
| ACT-S8 | QEMU (Espressif fork) | Emulator | Runs the real ESP32 boot ROM and the firmware without hardware. |
| ACT-S9 | Peripheral interrupt sources | Hardware | For example UART0 RX, routed through the interrupt matrix to a CPU line. |
| ACT-S10 | Board circuitry | Hardware | USB-serial bridge, BOOT (GPIO0) and EN buttons, optional LED on GPIO2, SPI flash on GPIO6–11. |

## Roles

| Role | Goal | Held by | Uses |
|---|---|---|---|
| Developer | Build and load firmware quickly, without vendor SDKs. | ACT-H1 | `make`, `make ram`, `make flash`, toolchain script |
| Integrator | Add application code: interrupt handlers, time base, GPIO, console. | ACT-H1 | `irq.h`, `gpio.h`, `io.h` APIs |
| Operator | Inspect and drive a running board interactively. | ACT-H2, ACT-H3 | mimmo commands over the serial console |
| Tester | Prove the requirements, in QEMU and on hardware. | ACT-H3, ACT-H4 | `.feature` scenarios, self test, `make qemu` |
| Learner | Understand every step from reset to C, interrupts and faults. | ACT-H2 | README, source comments, these docs |
| Maintainer | Keep the package building, documented and traceable. | ACT-H4 | `tools/tracecheck.py`, requirement files |

## Role ↔ epic involvement

| Role | EP-01 Build | EP-02 Boot | EP-03 Console | EP-04 Monitor | EP-05 GPIO | EP-06 Exc/IRQ | EP-07 Faults | EP-08 Verification | EP-09 Docs |
|---|---|---|---|---|---|---|---|---|---|
| Developer | ● | ● | ○ | ○ | ○ | ○ | ● | ○ | ○ |
| Integrator | ○ | | ● | | ● | ● | ● | | ○ |
| Operator | | ○ | ● | ● | ● | | ● | ○ | |
| Tester | ○ | ● | ● | ● | ● | ● | ● | ● | |
| Learner | ○ | ● | ○ | ● | ○ | ● | ● | | ● |
| Maintainer | ● | | | | | | | ● | ● |

● primary, ○ secondary

## Context diagram (text)

    Developer ──make──▶ Host build machine ──gcc/ld──▶ e32.elf ──mkimage──▶ e32.bin
                                              │
                                    esptool (load_ram | write_flash)
                                              ▼
    Operator ◀──UART0 115200──▶ [ ESP32 boot ROM ──▶ e32 firmware ] ◀── interrupt sources
                                    │                  │
                                 Board: BOOT/EN    SoC peripherals, LX6 core
                                              ▲
                     Tester ──make qemu──▶ QEMU (real boot ROM)
