# System requirements (SYS)

Level 3. What must the *whole system* do? "The system" means the e32
firmware running on an ESP32, together with its build tooling. Each
requirement derives from stakeholder needs and is verified by a system
(end-to-end) test, unless another method is stated in its `VER` entry.

---

## Build

### SYS-01 — Bare-toolchain build
- **Type:** System
- **EARS:** Ubiquitous
- **Statement:** The e32 build shall produce the firmware from source using only an xtensa-esp32-elf GCC toolchain (compiler, binutils, libgcc), GNU make and a host C compiler.
- **Derives from:** STK-01, STK-18
- **Verified by:** VER-SYS-01

### SYS-02 — Warning-free build
- **Type:** System
- **EARS:** Ubiquitous
- **Statement:** The e32 build shall complete with no compiler or linker warnings with `-Wall` enabled.
- **Derives from:** STK-01
- **Verified by:** VER-SYS-01

### SYS-03 — Build outputs
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When `make` is run, the e32 build shall produce `e32.elf` and a boot-ROM image `e32.bin`, and print the section sizes.
- **Derives from:** STK-01, STK-03, STK-04
- **Verified by:** VER-SYS-01

### SYS-25 — Toolchain from source
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When `tools/build-toolchain.sh` is run on a Linux host with the build prerequisites and access to the pinned source repositories, it shall build and install a C-only xtensa-esp32-elf toolchain with libgcc under `PREFIX`.
- **Derives from:** STK-02
- **Verified by:** VER-SYS-21

### SYS-29 — No third-party code
- **Type:** System
- **EARS:** Ubiquitous
- **Statement:** The e32 firmware and host tools shall contain no source code copied from ESP-IDF, Arduino, newlib or other third-party firmware.
- **Derives from:** STK-18
- **Verified by:** VER-SYS-23

## Boot and run

### SYS-04 — Flash boot
- **Type:** System
- **EARS:** Ubiquitous
- **Statement:** The e32 image shall be accepted and started by the ESP32 boot ROM when stored at flash offset `0x1000`.
- **Derives from:** STK-04
- **Verified by:** VER-SYS-02

### SYS-05 — RAM boot
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When the boot ROM, in UART download mode, loads the image into RAM and jumps to its entry point, the e32 firmware shall start and behave as after a flash boot.
- **Derives from:** STK-03
- **Verified by:** VER-SYS-03

### SYS-26 — Flash programming target
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When `make flash` is run with a board in download mode on `PORT`, the system shall write `e32.bin` at flash offset `0x1000` without altering the image header.
- **Derives from:** STK-04
- **Verified by:** VER-SYS-04

### SYS-27 — RAM load target
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When `make ram` is run with a board in download mode on `PORT`, the system shall load `e32.bin` into RAM through the boot ROM and start it.
- **Derives from:** STK-03
- **Verified by:** VER-SYS-03, VER-SYS-04

### SYS-08 — No boot-ROM code at run time
- **Type:** System
- **EARS:** State-driven
- **Statement:** While the e32 firmware is running, it shall execute no code in the boot ROM: no ROM functions, and no ROM exception vectors after the vector base is installed.
- **Derives from:** STK-18
- **Verified by:** VER-SYS-05

### SYS-09 — No watchdog resets
- **Type:** System
- **EARS:** State-driven
- **Statement:** While the e32 firmware is running, the system shall not be reset by the RTC watchdog or by either timer-group watchdog.
- **Derives from:** STK-12
- **Verified by:** VER-SYS-07

### SYS-23 — Internal SRAM only
- **Type:** System
- **EARS:** Ubiquitous
- **Statement:** The e32 firmware shall execute and keep all its data in the ESP32's internal SRAM, with no PSRAM and no flash access after the boot ROM hands over control.
- **Derives from:** STK-17
- **Verified by:** VER-SYS-19

## Console

### SYS-06 — Start-up banner and prompt
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When the e32 firmware starts, it shall print on UART0 a banner with the program name and build date and time, a line with the BSS range and stack top, the line `mimmo.c: Ready to get input (h for help)` and the prompt `> `.
- **Derives from:** STK-05
- **Verified by:** VER-SYS-06

### SYS-07 — Serial line parameters
- **Type:** System
- **EARS:** Ubiquitous
- **Statement:** The e32 firmware shall use UART0 with the bit rate and frame format configured by the boot ROM, which is 115200 baud 8N1 with a 40 MHz crystal.
- **Derives from:** STK-05
- **Verified by:** VER-SYS-06

### SYS-18 — Receive buffering
- **Type:** System
- **EARS:** State-driven
- **Statement:** While console receive interrupts are enabled, the e32 firmware shall retain up to 256 received characters not yet read by the application, in addition to the UART's hardware FIFO.
- **Derives from:** STK-19
- **Verified by:** VER-SYS-14

## Monitor

### SYS-10 — Execute monitor commands
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When the operator enters a command line terminated by CR or LF, the e32 firmware shall execute the monitor command it names (`r`, `w`, `d`, `p`, `a`, `g`, `i`, `s`, `f`, `h` or `?`) and print its result, then a new prompt.
- **Derives from:** STK-06, STK-07, STK-14
- **Verified by:** VER-SYS-08

### SYS-11 — Reject malformed commands
- **Type:** System
- **EARS:** Unwanted behaviour
- **Statement:** If a command line names an unknown command, lacks a required argument, contains an invalid number, or gives an address that is not 4-byte aligned to `r`, `w` or `d`, then the e32 firmware shall print `?? (h for help)`, perform no memory access for that line, and print a new prompt.
- **Derives from:** STK-06
- **Verified by:** VER-SYS-08

### SYS-31 — Interrupt statistics
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When the operator enters `i`, the e32 firmware shall print the uptime in seconds with two decimals, the tick count, and the count of every interrupt line that has fired at least once.
- **Derives from:** STK-08, STK-09
- **Verified by:** VER-SYS-08

## GPIO

### SYS-12 — Drive a GPIO output
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When the operator requests a level on a GPIO that exists and is output-capable, the e32 firmware shall configure the pin as a push-pull GPIO output and drive the requested level.
- **Derives from:** STK-07
- **Verified by:** VER-SYS-09

### SYS-13 — Read a GPIO input
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When the operator requests a reading of a GPIO that exists, the e32 firmware shall configure the pin as a GPIO input and print its level as 0 or 1.
- **Derives from:** STK-07
- **Verified by:** VER-SYS-09

### SYS-14 — Refuse dangerous pins
- **Type:** System
- **EARS:** Unwanted behaviour
- **Statement:** If a GPIO request names a pin that does not exist, one of GPIO 6–11, an output on GPIO 34–39, or an alternate function outside 0–5, then the e32 firmware shall refuse it, write no pad or GPIO register, and print the reason.
- **Derives from:** STK-07
- **Verified by:** VER-SYS-10

### SYS-22 — Blink mode
- **Type:** System
- **EARS:** Optional feature
- **Statement:** Where blink mode is selected at build time, the e32 firmware shall toggle `LED_GPIO` (GPIO2 by default) every 500 ms and print each new state on UART0.
- **Derives from:** STK-16
- **Verified by:** VER-SYS-18

## Execution model, interrupts and time

### SYS-15 — Deep calls and variable-length arrays
- **Type:** System
- **EARS:** Ubiquitous
- **Statement:** The e32 firmware shall support nested C calls at least 200 frames deep, and variable-length arrays or `alloca` at any call depth, limited only by stack space.
- **Derives from:** STK-11
- **Verified by:** VER-SYS-11

### SYS-16 — Interrupt handling
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When an enabled level-1 interrupt occurs, the e32 firmware shall run the C handler registered for its line and then resume the interrupted code with its registers and processor state unchanged.
- **Derives from:** STK-08
- **Verified by:** VER-SYS-12

### SYS-17 — Tick
- **Type:** System
- **EARS:** Ubiquitous
- **Statement:** The e32 firmware shall count ticks at `HZ` (100) per second of CPU time, measured in `CPU_HZ` cycles, and shall keep counting even when a tick interrupt is serviced late.
- **Derives from:** STK-09
- **Verified by:** VER-SYS-13

## Faults

### SYS-19 — Fault report
- **Type:** System
- **EARS:** Unwanted behaviour
- **Statement:** If a fatal exception, a kernel exception, a double exception, or an interrupt of level 2–7 occurs, then the e32 firmware shall print on UART0 a report containing:
  - the fault kind;
  - the cause number and name, where one applies;
  - PC and PS;
  - EXCVADDR, for memory faults;
  - registers a0–a15;
  - SAR, LBEG, LEND and LCOUNT;
  - WINDOWBASE and WINDOWSTART;
  - the caller address.
- **Derives from:** STK-10
- **Verified by:** VER-SYS-15

### SYS-20 — Reboot after a fault
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When a character is received after a fault report, the e32 firmware shall perform a software system reset.
- **Derives from:** STK-10
- **Verified by:** VER-SYS-16

### SYS-30 — Deliberate faults
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When the operator enters `f <n>` with n from 0 to 5, the e32 firmware shall raise a fault on purpose:
  - 0: a load from address 0;
  - 1: an illegal instruction;
  - 2: an integer divide by zero;
  - 3: a `break` instruction;
  - 4: a stack pointer corrupted so that the next interrupt causes a double exception;
  - 5: a level-3 software interrupt.
- **Derives from:** STK-10, STK-14
- **Verified by:** VER-SYS-15

## Verification support

### SYS-21 — Self test
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When the operator enters `s`, the e32 firmware shall check deep recursion, a variable-length array with its caller spilled, a software interrupt and the tick rate, print `ok` or `BAD` for each, and finish with `all ok` or `FAILED`.
- **Derives from:** STK-14
- **Verified by:** VER-SYS-17

### SYS-24 — Emulator boot
- **Type:** System
- **EARS:** Event-driven
- **Statement:** When `make qemu` is run with Espressif's QEMU available as `QEMU`, the system shall boot the firmware in machine `esp32` through the real ESP32 boot ROM from a 4 MB flash image.
- **Derives from:** STK-13
- **Verified by:** VER-SYS-20

## Documentation

### SYS-28 — Documentation content
- **Type:** System
- **EARS:** Ubiquitous
- **Statement:** The project documentation shall cover:
  - building and loading;
  - the boot sequence;
  - the memory map;
  - the vector table and the interrupt and fault paths;
  - the interrupt API;
  - the monitor commands;
  - the GPIO constraints;
  - the rules for interrupt handlers;
  - the verification status;
  - a file-by-file mapping to the LPC1343 original.
- **Derives from:** STK-15
- **Verified by:** VER-SYS-22

### SYS-32 — Traceability check
- **Type:** System
- **EARS:** Ubiquitous
- **Statement:** The project shall link every requirement to its parent and its verification, and shall provide a checker that reports any broken link, wrong-level parent, unverified requirement or unknown scenario tag.
- **Derives from:** STK-20
- **Verified by:** VER-SYS-22
