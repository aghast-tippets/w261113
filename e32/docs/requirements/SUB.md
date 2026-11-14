# Subsystem requirements (SUB)

Level 4. What must each *subsystem* do? Each requirement derives from system
requirements, is allocated to one subsystem, and is verified by a subsystem
or integration test.

## Subsystem decomposition

| ID | Subsystem | Kind | Realised by |
|---|---|---|---|
| SS-BLD | Build and image tooling | Software (host) | `Makefile`, `esp32.lds`, `tools/mkimage.c`, `tools/build-toolchain.sh` |
| SS-BOOT | Boot and startup | Software (target) | `boot.S`, `wdt.c`, `io.c:serial_setup` |
| SS-EXC | Exception and interrupt core | Software (target) | `vectors.S`, `irq.c`, `include/xtensa.h`, `include/irq.h` |
| SS-TIME | Timekeeping | Software (target) | `timer.c`, `lib.c:udelay` |
| SS-CON | Console I/O and formatting | Software (target) | `io.c`, `pp_printf.c` |
| SS-GPIO | GPIO | Software (target) | `gpio.c`, `include/gpio.h` |
| SS-MON | Monitor application | Software (target) | `mimmo.c`, `main.c` |
| SS-FLT | Fault handling and recovery | Software (target) | `vectors.S:_panic`, `panic.c` |
| SS-LIB | Support library | Software (target) | `lib.c` |
| SS-VEN | Verification environment | Software (host) + emulator | `Makefile` (`flash.img`, `qemu`), Espressif QEMU, `docs/features` |
| SS-DOC | Documentation | Documents | `README.md`, `docs/`, `tools/tracecheck.py` |
| SS-TGT | Target hardware | Hardware | ESP32 module and board (not part of the deliverable; constrained by `HW` requirements) |

Allocation to level 5: SS-TGT → `HW`; all the software subsystems → `SW`;
boundaries between subsystems → `IF`.

---

## SS-BLD — Build and image tooling

### SUB-BLD-01 — Compilation rules
- **Type:** Subsystem
- **EARS:** Ubiquitous
- **Statement:** The build subsystem shall compile every firmware source with `-Os -g -Wall -ffreestanding -nostdlib -mtext-section-literals`, and link with `-nostdlib` against libgcc only.
- **Derives from:** SYS-01, SYS-02
- **Allocated to:** SS-BLD
- **Verified by:** VER-SUB-01

### SUB-BLD-02 — Memory layout
- **Type:** Subsystem
- **EARS:** Ubiquitous
- **Statement:** The build subsystem shall link:
  - the vector table at the start of IRAM, `0x40080000`;
  - all code and literal pools after it in IRAM (128 KB);
  - read-only and initialised data in DRAM from `0x3ffb0000`;
  - BSS after the data, with the initial stack top at `0x3ffdc000`.
- **Derives from:** SYS-23, SYS-08
- **Allocated to:** SS-BLD
- **Verified by:** VER-SUB-01

### SUB-BLD-03 — Layout guards
- **Type:** Subsystem
- **EARS:** Unwanted behaviour
- **Statement:** If fewer than 8 KB remain between the end of BSS and the stack top, or the vector table is not at the start of IRAM, then the build subsystem shall fail the link with a message.
- **Derives from:** SYS-23
- **Allocated to:** SS-BLD
- **Verified by:** VER-SUB-02

### SUB-BLD-04 — Image conversion
- **Type:** Subsystem
- **EARS:** Event-driven
- **Statement:** When `e32.elf` has been linked, the build subsystem shall convert it into an ESP32 boot image (IF-01), with one image segment per loadable ELF segment that has file contents.
- **Derives from:** SYS-03, SYS-04, SYS-05
- **Allocated to:** SS-BLD
- **Verified by:** VER-SUB-03

### SUB-BLD-05 — Make targets
- **Type:** Subsystem
- **EARS:** Ubiquitous
- **Statement:** The build subsystem shall provide the make targets `all`, `ram`, `flash`, `flash.img`, `qemu`, `e32.dis` and `clean`, with `CROSS_COMPILE`, `PORT`, `ESPTOOL`, `QEMU`, `HOSTCC` and `EXTRA_CFLAGS` overridable.
- **Derives from:** SYS-03, SYS-24, SYS-26, SYS-27
- **Allocated to:** SS-BLD
- **Verified by:** VER-SUB-04

### SUB-BLD-06 — Toolchain build
- **Type:** Subsystem
- **EARS:** Event-driven
- **Statement:** When run, the toolchain script shall fetch pinned binutils and GCC sources, apply the ESP32 core-configuration overlay, and build and install binutils, a C-only GCC and libgcc for the target `xtensa-esp32-elf`.
- **Derives from:** SYS-25
- **Allocated to:** SS-BLD
- **Verified by:** VER-SUB-05

## SS-BOOT — Boot and startup

### SUB-BOOT-01 — C environment
- **Type:** Subsystem
- **EARS:** Event-driven
- **Statement:** When the boot ROM transfers control to the entry point, the boot subsystem shall, before calling any C function:
  - disable all interrupts;
  - leave a single live register window;
  - install the firmware's vector table;
  - set the firmware's own stack and processor state;
  - clear BSS.
- **Derives from:** SYS-05, SYS-08, SYS-15, SYS-16
- **Allocated to:** SS-BOOT
- **Verified by:** VER-SUB-06

### SUB-BOOT-02 — Watchdogs off
- **Type:** Subsystem
- **EARS:** Event-driven
- **Statement:** When startup runs, the boot subsystem shall disable the RTC watchdog and the watchdogs of timer groups 0 and 1 before `main` is called.
- **Derives from:** SYS-09
- **Allocated to:** SS-BOOT
- **Verified by:** VER-SUB-07

### SUB-BOOT-03 — Inherit the console set-up
- **Type:** Subsystem
- **EARS:** Ubiquitous
- **Statement:** The boot subsystem shall keep the UART0 configuration left by the boot ROM, and shall wait until the ROM's pending output has left the transmit FIFO before the firmware prints.
- **Derives from:** SYS-07
- **Allocated to:** SS-BOOT
- **Verified by:** VER-SUB-08

## SS-EXC — Exception and interrupt core

### SUB-EXC-01 — Register-window spill and fill
- **Type:** Subsystem
- **EARS:** Event-driven
- **Statement:** When the CPU raises a window overflow or underflow exception for a call4, call8 or call12 frame, the exception subsystem shall store or reload that frame's registers in the stack areas defined by the windowed ABI (IF-15), and resume.
- **Derives from:** SYS-15
- **Allocated to:** SS-EXC
- **Verified by:** VER-SUB-09

### SUB-EXC-02 — Alloca fix-up
- **Type:** Subsystem
- **EARS:** Event-driven
- **Statement:** When a `movsp` raises the alloca exception because the caller's frame is spilled, the exception subsystem shall reload the caller's frame and re-execute the `movsp`.
- **Derives from:** SYS-15
- **Allocated to:** SS-EXC
- **Verified by:** VER-SUB-09

### SUB-EXC-03 — Interrupt context
- **Type:** Subsystem
- **EARS:** Event-driven
- **Statement:** When a level-1 interrupt is taken, the exception subsystem shall preserve the complete interrupted context, call the dispatcher as an ordinary windowed C function, and restore the context exactly before returning.
- **Derives from:** SYS-16
- **Allocated to:** SS-EXC
- **Verified by:** VER-SUB-10

### SUB-EXC-04 — Routing and dispatch
- **Type:** Subsystem
- **EARS:** Ubiquitous
- **Statement:** The exception subsystem shall route peripheral sources to CPU interrupt lines through the interrupt matrix, and dispatch every pending, enabled level-1 line to its registered handler.
- **Derives from:** SYS-16, SYS-18, SYS-31
- **Allocated to:** SS-EXC
- **Verified by:** VER-SUB-10

### SUB-EXC-05 — Route faults
- **Type:** Subsystem
- **EARS:** Unwanted behaviour
- **Statement:** If a user exception other than a level-1 interrupt or alloca, a kernel exception, a double exception, or an interrupt of level 2–7 occurs, then the exception subsystem shall transfer control to the fault subsystem, identifying which kind of fault it is.
- **Derives from:** SYS-19
- **Allocated to:** SS-EXC
- **Verified by:** VER-SUB-11

## SS-TIME — Timekeeping

### SUB-TIME-01 — Periodic tick
- **Type:** Subsystem
- **EARS:** Ubiquitous
- **Statement:** The timekeeping subsystem shall raise a level-1 interrupt from `CCOMPARE0` at a requested rate and count the ticks in `jiffies`.
- **Derives from:** SYS-17
- **Allocated to:** SS-TIME
- **Verified by:** VER-SUB-12

### SUB-TIME-02 — Missed-compare recovery
- **Type:** Subsystem
- **EARS:** Unwanted behaviour
- **Statement:** If, after a new compare value is written, `CCOUNT` has already reached it, then the timekeeping subsystem shall advance the value by whole periods, counting each one, until the value is ahead of `CCOUNT`.
- **Derives from:** SYS-17
- **Allocated to:** SS-TIME
- **Verified by:** VER-SUB-12

### SUB-TIME-03 — Busy-wait delay
- **Type:** Subsystem
- **EARS:** Ubiquitous
- **Statement:** The timekeeping subsystem shall provide a microsecond busy-wait delay based on `CCOUNT` and `CPU_HZ`.
- **Derives from:** SYS-21, SYS-22
- **Allocated to:** SS-TIME
- **Verified by:** VER-SUB-12

## SS-CON — Console I/O and formatting

### SUB-CON-01 — Output
- **Type:** Subsystem
- **EARS:** Ubiquitous
- **Statement:** The console subsystem shall transmit characters on UART0, translating each LF into CR LF.
- **Derives from:** SYS-06, SYS-07
- **Allocated to:** SS-CON
- **Verified by:** VER-SUB-13

### SUB-CON-02 — Line input
- **Type:** Subsystem
- **EARS:** Event-driven
- **Statement:** When a line is requested, the console subsystem shall read characters with echo and backspace editing until CR or LF is received.
- **Derives from:** SYS-10
- **Allocated to:** SS-CON
- **Verified by:** VER-SUB-13

### SUB-CON-03 — Interrupt-driven receive
- **Type:** Subsystem
- **EARS:** State-driven
- **Statement:** While receive interrupt mode is enabled, the console subsystem shall move received bytes from the UART FIFO into a 256-byte ring buffer from the interrupt handler, and the reader shall sleep until data is available.
- **Derives from:** SYS-18
- **Allocated to:** SS-CON
- **Verified by:** VER-SUB-13

### SUB-CON-04 — Formatted output
- **Type:** Subsystem
- **EARS:** Ubiquitous
- **Statement:** The console subsystem shall provide `printf` and `sprintf` supporting `%d %i %u %x %X %p %s %c %%`, the `-` and `0` flags, and a decimal field width.
- **Derives from:** SYS-06, SYS-10, SYS-19
- **Allocated to:** SS-CON
- **Verified by:** VER-SUB-14

## SS-GPIO — GPIO

### SUB-GPIO-01 — Pin configuration and access
- **Type:** Subsystem
- **EARS:** Ubiquitous
- **Statement:** The GPIO subsystem shall configure any valid pad, numbered 0–39, as a GPIO input or output or select one of its alternate functions 0–5 (0 always being GPIO), and set and read GPIO levels.
- **Derives from:** SYS-12, SYS-13, SYS-22
- **Allocated to:** SS-GPIO
- **Verified by:** VER-SUB-15

### SUB-GPIO-02 — Pin protection
- **Type:** Subsystem
- **EARS:** Unwanted behaviour
- **Statement:** If a pin does not exist, is connected to the flash (6–11), or is input-only (34–39) when output is requested, or the function number is outside 0–5, then the GPIO subsystem shall return an error without writing any register.
- **Derives from:** SYS-14
- **Allocated to:** SS-GPIO
- **Verified by:** VER-SUB-15

## SS-MON — Monitor application

### SUB-MON-01 — Command set
- **Type:** Subsystem
- **EARS:** Event-driven
- **Statement:** When a command line is read, the monitor subsystem shall execute `r`, `w`, `d`, `p`, `a`, `g`, `i`, `s`, `f`, `h` or `?`. Addresses and values are taken in hex, and GPIO and function numbers in decimal.
- **Derives from:** SYS-10, SYS-21, SYS-30, SYS-31
- **Allocated to:** SS-MON
- **Verified by:** VER-SUB-16

### SUB-MON-02 — Input validation
- **Type:** Subsystem
- **EARS:** Unwanted behaviour
- **Statement:** If a command is unknown, has a missing or invalid argument, or has an unaligned address (`r`, `w`, `d`), then the monitor subsystem shall print `?? (h for help)` without accessing memory.
- **Derives from:** SYS-11
- **Allocated to:** SS-MON
- **Verified by:** VER-SUB-16

### SUB-MON-03 — Start-up sequence
- **Type:** Subsystem
- **EARS:** Event-driven
- **Statement:** When `main` runs, the monitor subsystem shall:
  - print the banner;
  - initialise interrupts, the `HZ` tick and console receive interrupts;
  - then enter the command loop, or the blink loop when blink mode is selected.
- **Derives from:** SYS-06, SYS-16, SYS-17, SYS-18, SYS-22
- **Allocated to:** SS-MON
- **Verified by:** VER-SUB-16

## SS-FLT — Fault handling and recovery

### SUB-FLT-01 — Capture state
- **Type:** Subsystem
- **EARS:** Event-driven
- **Statement:** When entered, the fault subsystem shall capture all address registers and the relevant special registers into a static frame, and continue on a private stack, independent of the faulting stack.
- **Derives from:** SYS-19
- **Allocated to:** SS-FLT
- **Verified by:** VER-SUB-17

### SUB-FLT-02 — Report
- **Type:** Subsystem
- **EARS:** Event-driven
- **Statement:** When the state is captured, the fault subsystem shall print the fault report on UART0 using polled I/O with all maskable interrupts masked.
- **Derives from:** SYS-19
- **Allocated to:** SS-FLT
- **Verified by:** VER-SUB-17

### SUB-FLT-03 — Reboot
- **Type:** Subsystem
- **EARS:** Event-driven
- **Statement:** When a character is received after the report, the fault subsystem shall request a software system reset through `RTC_CNTL`.
- **Derives from:** SYS-20
- **Allocated to:** SS-FLT
- **Verified by:** VER-SUB-17

### SUB-FLT-04 — Nested faults
- **Type:** Subsystem
- **EARS:** Unwanted behaviour
- **Statement:** If a fault occurs while a fault is being reported, then the fault subsystem shall halt without further output.
- **Derives from:** SYS-19
- **Allocated to:** SS-FLT
- **Verified by:** VER-SUB-17

## SS-LIB — Support library

### SUB-LIB-01 — Freestanding helpers
- **Type:** Subsystem
- **EARS:** Ubiquitous
- **Statement:** The support library shall provide `memset`, `memcpy` and `strlen` with ISO C semantics, for the firmware and for compiler-generated calls.
- **Derives from:** SYS-01
- **Allocated to:** SS-LIB
- **Verified by:** VER-SUB-18

## SS-VEN — Verification environment

### SUB-VEN-01 — Emulated target
- **Type:** Subsystem
- **EARS:** Ubiquitous
- **Statement:** The verification environment shall run the firmware in Espressif's QEMU with the real ESP32 boot ROM, in flash-boot mode from a 4 MB image and in download mode (strap `0x0f`), with the console reachable on stdio or TCP.
- **Derives from:** SYS-24, SYS-04, SYS-05
- **Allocated to:** SS-VEN
- **Verified by:** VER-SUB-19

## SS-DOC — Documentation

### SUB-DOC-01 — Document set
- **Type:** Subsystem
- **EARS:** Ubiquitous
- **Statement:** The documentation subsystem shall consist of `README.md`, the `docs/` set (actors, epics, features, stories, requirements at every level, verification and Gherkin scenarios) and `tools/tracecheck.py`, which generates `docs/traceability.md`. The README shall include a provenance section stating the origin of every source file and naming every externally specified or fetched input.
- **Derives from:** SYS-28, SYS-29, SYS-32
- **Allocated to:** SS-DOC
- **Verified by:** VER-SUB-20

## SS-TGT — Target hardware

### SUB-TGT-01 — Target board
- **Type:** Subsystem
- **EARS:** Ubiquitous
- **Statement:** The target hardware subsystem shall provide:
  - an ESP32 SoC with its boot ROM and internal SRAM;
  - SPI flash;
  - a 40 MHz crystal;
  - UART0 connected to the host through a USB-serial bridge;
  - a BOOT (GPIO0) control and a reset (EN) control.
- **Derives from:** SYS-04, SYS-05, SYS-07, SYS-23, SYS-26, SYS-27
- **Allocated to:** SS-TGT
- **Verified by:** VER-SUB-21

### SUB-TGT-02 — Indicator LED
- **Type:** Subsystem
- **EARS:** Optional feature
- **Statement:** Where blink mode is used, the target hardware subsystem shall provide an LED driven by `LED_GPIO`.
- **Derives from:** SYS-22
- **Allocated to:** SS-TGT
- **Verified by:** VER-SUB-21
