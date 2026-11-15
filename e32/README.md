# e32: bare-metal ESP32, from scratch

This follows the plan of Alessandro Rubini's *cortex-m3* notes (LPC1343,
2014) on a plain ESP32 (Xtensa LX6, e.g. ESP32-WROOM-32 DevKit). No
ESP-IDF, no Arduino, no SDK, no libc, and no ROM code at run time. The
startup code, exception vectors, interrupt dispatch, fault handler, linker
script, image builder, serial I/O, GPIO, printf and memory monitor are all
here, about 2,000 lines with comments.

The result is ~8 kB. It runs a memory monitor (`mimmo`) on UART0 at 115200
baud, with a 100 Hz timer tick and interrupt-driven serial input.

## Files

| File | What it does | LPC1343 equivalent |
|---|---|---|
| `boot.S` | Resets the register window, installs our vectors, sets the stack, clears BSS, calls C | `boot.S` |
| `vectors.S` | Vector table, register-window handlers, alloca fix-up, level-1 interrupt entry/exit, fault entry | `vectors.S` (filled in) |
| `irq.c`, `include/irq.h` | Interrupt matrix routing and level-1 dispatch to C handlers | — |
| `timer.c` | 100 Hz tick from the CPU's CCOMPARE0 | — |
| `panic.c` | Fault report (cause, pc, all registers) and software reboot | — |
| `include/xtensa.h` | PS bits and frame layouts shared by the assembly and C | — |
| `esp32.lds` | Vectors at the start of IRAM, code in IRAM, data in DRAM; aliases `printf` to `pp_printf` | `ram.lds` / `rom.lds` |
| `tools/mkimage.c` | Turns the ELF into an image the ROM accepts (header and checksum) | `fix-checksum` |
| `wdt.c` | Turns off the watchdogs the ROM armed | — |
| `io.c` | `putc`/`puts`, plus `getc`/`gets` fed by the UART interrupt | `io.c` |
| `gpio.c`, `include/gpio.h` | Same GPIO API, with the IO_MUX table built from hex addresses | `gpio.c` |
| `pp_printf.c` | Small `printf`/`sprintf`, written fresh for this package | `pp_printf` |
| `mimmo.c` | The memory monitor, now with a self test and fault demos | `mimmo.c` |
| `main.c` | Sets up interrupts, then runs mimmo (or blinks GPIO2 with `if (0)`) | `main.c` |
| `lib.c` | `memset`, `memcpy`, `strlen` and `udelay` | — |
| `docs/`, `tools/tracecheck.py`, `tests/` | Actors, epics, stories, requirements (BR → CMP, VER), Gherkin features and rules, ledger and backlog; the traceability checker; GoogleTest and pytest-bdd suites | — |

## Prerequisites

* A bare `xtensa-esp32-elf-gcc`. Any build works, including the one Espressif
  ships. `tools/build-toolchain.sh` builds one from source in about 30 minutes.
  The only Espressif input it needs is the file that describes the LX6 core
  configuration.
* `esptool.py` (`pip install esptool`), used only to move bytes over the
  serial port. Rubini used `mtools` the same way.
* Set `CROSS_COMPILE` if your compiler prefix differs.

## Building and running

    make                 # e32.elf, e32.bin
    make ram             # load into RAM over serial and run
    make flash           # write to flash at 0x1000; it runs at every reset
    make qemu            # boot in Espressif's QEMU fork

With `make ram`, the board must be in download mode: hold BOOT (GPIO0 low)
while you press EN. This is the equivalent of the P0-1 jumper on the LPC
board. After `make flash`, just reset the board. Then use `minicom -D
/dev/ttyUSB0 -b 115200` or similar.

Unlike the LPC1343, the same binary serves both paths. The ESP32 ROM always
copies the image into internal RAM before jumping to it, whether the image
comes from flash or from the UART. So there is one linker script and no
`.data` copy loop.

## How it boots

1. The ROM reads the image header at flash `0x1000` (or receives the image
   over the UART). It copies each segment to its load address, checks the
   XOR checksum, and calls the entry point.
2. `call_start` (`boot.S`) disables interrupts and drops the ROM's register
   windows, leaving only window 0 live. It then points `VECBASE` at our
   `vectors.S`, sets the stack and `PS`, clears BSS, and calls `wdt_disable`,
   `serial_setup` and `main`. From here on, no ROM code runs.
3. `main` disconnects everything the ROM routed in the interrupt matrix. It
   then starts the tick on CPU interrupt 6, routes UART0 to CPU interrupt
   17, and enters mimmo.

Memory map: vectors at `0x40080000` (VECBASE must be 1 kB aligned), code after
them in IRAM, data at `0x3ffb0000`, and the stack growing down from
`0x3ffdc000`. IRAM only allows 32-bit accesses, so strings and `.rodata` live
in DRAM. Literal pools sit in IRAM next to their code
(`-mtext-section-literals`); that works because they are only read with
`l32r`.

## Interrupts and faults

The Xtensa core has no single "interrupt vector" like Cortex-M. Instead it
has a table of entry points at fixed offsets from `VECBASE`:

| Offset | Vector | Handled by |
|---|---|---|
| `0x000`–`0x17f` | Window overflow/underflow (call4/8/12) | Spill/fill a register frame to/from the stack |
| `0x180`–`0x2bf` | Interrupt levels 2–5, debug (6), NMI (7) | `_panic`: we never enable these |
| `0x300` | Kernel exception | `_panic`: we always run with `PS.UM` = 1 |
| `0x340` | User exception | Level-1 interrupt, alloca, or `_panic` |
| `0x3c0` | Double exception | `_panic` |

**Register windows.** The CPU has 64 address registers arranged as a ring.
Each call rotates the visible 16 by 4, 8 or 12. When a call needs
registers an older frame still holds, the CPU jumps to an overflow vector,
which stores that frame below its callee's stack pointer. Returning into a
spilled frame triggers the matching underflow. Without these handlers, C
code dies about eight calls deep.

**Level-1 interrupts** (`_level1_handler` → `irq_dispatch`):

1. Save `a0`–`a15`, `EPC1`, `PS`, `SAR` and the loop registers in a frame
   built 16 bytes below the interrupted stack pointer. Those 16 bytes may
   hold the caller's spilled registers, so they stay untouched.
2. Leave exception mode with level-1 interrupts masked. Then spill every
   other register window to memory. This step is essential: an older frame
   spilled later, after the stack pointer has moved, would be written
   relative to the wrong stack pointer.
3. Move `sp` to the frame and call `irq_dispatch()` as a normal windowed C
   function. It runs every pending, enabled level-1 handler, and clears
   latched (edge and software) interrupts with `INTCLEAR`.
4. Restore everything and return with `rfe`.

**Alloca.** A variable-length array or `alloca()` moves the stack pointer
with `movsp`. If the caller's registers are spilled at that moment, the CPU
raises an exception. The handler reloads the caller with the matching
underflow sequence, then retries the `movsp`.

**Faults.** Any other exception, an unexpected high-level interrupt, or a
double exception goes to `_panic`. It saves every register to a static
frame, because the stack may be the problem. It then resets the register
window, switches to a private 2 kB stack and calls `panic_handler()`:

    *** Fatal exception 28: LoadProhibited
    pc  400815db  ps  00060530  excvaddr 00000000
    a0  80081658  a1  3ffdbf60  a2  00000001  a3  00000001
    ...
    called from ~40081658

    Press any key to reboot

To find the source line, use `xtensa-esp32-elf-addr2line -e e32.elf <pc>`.
The reboot is a real software reset (`RTC_CNTL_OPTIONS0.SW_SYS_RST`).

**Interrupt API** (`include/irq.h`):

    irq_init();                          // disconnect all 69 matrix sources
    irq_map(INTR_SRC_UART0, 17);         // peripheral source -> CPU line
    irq_request(17, handler, arg);       // install and enable (level-1 lines)
    irq_enable(n); irq_disable(n);
    flags = irq_save(); ... irq_restore(flags);   // critical section

Level-1 CPU lines are 0–10, 12, 13, 17 and 18. Lines 6 (CCOMPARE0) and 7
(software) are internal and ignore the matrix. `getc()` sleeps with
`waiti 0` until the UART interrupt brings a byte. The buffer check and the
sleep happen with interrupts masked, and `waiti` unmasks them in the same
instruction, so no wake-up can be lost.

## mimmo commands

    r <addr>              read a 32-bit word
    w <addr> <value>      write a 32-bit word
    d <addr> [<count>]    dump words (default 16)
    p <gpio> [0|1]        set an output, or read the pin as input
    a <gpio> <af>         set the alternate function (0 = GPIO)
    g <addr>              call an address
    i                     interrupt counts and uptime
    s                     self test: windows, alloca, software irq, tick
    f <n>                 fault on purpose: 0 NULL load, 1 illegal insn,
                          2 divide by zero, 3 break, 4 bad sp (double
                          exception on the next tick), 5 level-3 interrupt
    h                     help

Addresses and values are hex. GPIO numbers are decimal, matching the board
silkscreen. A bad address now ends in our own fault handler.

## GPIO notes

* GPIO numbers are flat (0–39). `GPIO_NR(port, bit)` exists only for API
  compatibility.
* In the IO_MUX, GPIO is hardware function 2, not 0. As on the LPC13, the
  code swaps function 0 and 2, so that AF0 always means GPIO.
* GPIO 6–11 drive the flash chip and are refused. GPIO 34–39 are input only.
* Outputs are routed through the GPIO matrix as "simple GPIO output" (signal
  256), with output enable taken from `GPIO_ENABLE`.

## What was tested

Everything was run in Espressif's QEMU fork using the real ESP32 ROM (rev 3,
"ets Jul 29 2019"):

* Booting from flash at `0x1000`, and `esptool load_ram` through ROM
  download mode. In both cases the self test passes.
* The `s` self test: 200-deep recursion, a VLA with its caller spilled (the
  alloca path), a software interrupt and the tick rate.
* A stress build with a 20 kHz tick interrupting 2,000 rounds of deep
  recursion and VLAs: 0 wrong results over 260,000 interrupts and 2,048
  alloca fix-ups. This also caught a real bug: a tick could be lost forever
  if CCOMPARE was set behind CCOUNT, and `timer.c` now guards against it.
* `f 0`–`f 5`: LoadProhibited, IllegalInstruction, IntegerDivideByZero,
  break, a double exception and an unexpected level-3 interrupt each produce
  a correct report, and a key press reboots (`rst:0x3 (SW_RESET)`).
* UART receive by interrupt, every mimmo command path, and the image
  format (`esptool image-info` reports the checksum as valid).
* `wdt_disable()`: with the timer-group-0 watchdog armed, the emulated chip
  resets every second; with `wdt_disable()` it stays up.
* `pp_printf`: its output matches glibc's on a set of format strings.
* The full requirement set, with each item's verification status, is in
  `docs/`. Run `python3 tools/tracecheck.py --check` to validate it.

QEMU cannot test the following, so check them on hardware:

* Real pin levels on GPIO, since QEMU does not model the pads.
* The RTC watchdog, which QEMU does not model.
* The absolute clock. The tick and `udelay()` both assume the ROM left the
  CPU on the 40 MHz crystal. If uptime runs twice as fast as a wall clock,
  change `CPU_HZ` in `io.h`.

## Rules for interrupt handlers

* They run with level-1 interrupts masked, on the interrupted task's stack.
  Keep them short and their stack use small.
* No floating point: the FPU is disabled (`CPENABLE` = 0), and its registers
  are not saved.
* Share data with the main code through `volatile` variables, and use
  `irq_save()`/`irq_restore()` for anything wider than one word.

## Documentation and requirements

[`docs/`](docs/README.md) specifies the project at every level, from
business requirements down to unit contracts, following the gated BDD
framework v2.0 in [`docs/bdd-framework.md`](docs/bdd-framework.md). It
holds the actors, epics and user stories, EARS requirements with a TAID
verification entry each, and Gherkin features in which every requirement
is a `Rule:` illustrated by scenarios. `tests/run_all.sh` runs both test
suites and updates the ledger (`docs/traceability.md`), the story and epic
status, and the open work (`docs/backlog.md`); `python3 tools/tracecheck.py
--check` checks every link.

## Provenance

* **The firmware, host tools and build files** were all written for this
  package. Nothing is copied from ESP-IDF, Arduino, newlib or any other
  firmware.
* **Externally specified sequences:**
  * The register-window overflow and underflow handlers in `vectors.S` are
    the forms defined by the Xtensa ISA for the windowed ABI. There is
    essentially one correct way to write them.
  * The register addresses in `include/regs.h` and the core constants in
    `include/xtensa.h` come from the ESP32 Technical Reference Manual and
    the core configuration.
* **Fetched at build time, never compiled into the firmware:**
  * `tools/build-toolchain.sh` clones Espressif's binutils, GCC and
    `xtensa-overlays` repositories. The overlay describes the LX6 core
    configuration to the compiler.
  * esptool and QEMU are separate host tools.

## Coding further

* GPIO interrupts (matrix source 22): a button handler.
* Medium-priority (level 2–3) interrupts with their own vectors.
* Turning on the PLL (80/160/240 MHz) and setting the UART divisor from the
  known APB clock.
* A backtrace in `panic.c`: spill the windows first, then walk the
  `a0`/`a1` chain on the stack.
* Starting the second core (APP CPU) with its own stack and VECBASE.
