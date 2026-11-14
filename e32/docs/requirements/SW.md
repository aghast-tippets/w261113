# Software requirements (SW)

Level 5. What must the *software* do? These requirements are allocated from
the software subsystems, and are detailed enough to implement and test
directly. The middle part of each ID names the subsystem: BOOT, WDT (in
SS-BOOT), CON and FMT (SS-CON), EXC, TIME, GPIO, MON, FLT, LIB, and IMG,
BLD and TC (SS-BLD).

There are three software configuration items: **SWCI-1**, the e32 firmware;
**SWCI-2**, `tools/mkimage`; and **SWCI-3**, the build scripts (`Makefile`,
`esp32.lds`, `tools/build-toolchain.sh`).

---

## Startup (SWCI-1, SS-BOOT)

### SW-BOOT-01 — Mask interrupts first
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When entered at `call_start`, the startup code shall write 0 to `INTENABLE` before any other action.
- **Derives from:** SUB-BOOT-01
- **Verified by:** VER-SW-01

### SW-BOOT-02 — Reset the register window
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** The startup code shall set `WINDOWSTART` to 1 and `WINDOWBASE` to 0, then execute `rsync`, using no address register other than `a2` until the `rsync` completes.
- **Derives from:** SUB-BOOT-01
- **Verified by:** VER-SW-01

### SW-BOOT-03 — Install vectors before the first call
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** The startup code shall write `_vector_table` to `VECBASE` before its first call instruction.
- **Derives from:** SUB-BOOT-01, SUB-EXC-01
- **Verified by:** VER-SW-01

### SW-BOOT-04 — Stack and processor state
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** The startup code shall set `a0` = 0, `a1` = `_stack_top`, and `PS` = `WOE | UM | INTLEVEL(0)` (`0x00040020`).
- **Derives from:** SUB-BOOT-01
- **Verified by:** VER-SW-01

### SW-BOOT-05 — Clear BSS
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** The startup code shall write zero to every 32-bit word from `__bss_start` up to, but not including, `__bss_end`.
- **Derives from:** SUB-BOOT-01
- **Verified by:** VER-SW-01

### SW-BOOT-06 — Call sequence
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** The startup code shall call `wdt_disable`, `serial_setup` and `main`, in that order, using `call4`, and shall loop forever if `main` returns.
- **Derives from:** SUB-BOOT-01, SUB-BOOT-02, SUB-BOOT-03
- **Verified by:** VER-SW-01

### SW-WDT-01 — Disable each watchdog
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** For each of the RTC watchdog, the timer group 0 watchdog and the timer group 1 watchdog, `wdt_disable` shall:
  - write the key `0x50D83AA1` to the block's `WPROTECT` register;
  - write 0 to its `CONFIG0` register;
  - write 0 to `WPROTECT`.
- **Derives from:** SUB-BOOT-02
- **Verified by:** VER-SW-02

## Console (SWCI-1, SS-CON)

### SW-CON-01 — Keep the ROM's UART set-up
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** `serial_setup` shall not write `UART_CLKDIV` or `UART_CONF0`, and shall return once the transmit FIFO count is 0.
- **Derives from:** SUB-BOOT-03
- **Verified by:** VER-SW-03

### SW-CON-02 — putc
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** `putc` shall wait while the transmit FIFO holds 126 or more bytes, emit CR before every LF, and write each byte to the FIFO register only after reading the status register.
- **Derives from:** SUB-CON-01
- **Verified by:** VER-SW-03

### SW-CON-03 — gets
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** `gets(s, size)` shall handle each received character as follows:
  - On CR or LF, echo a newline and end the line.
  - On BS (`0x08`) or DEL (`0x7F`), remove the last stored character, if any, and echo `"\b \b"`.
  - Ignore any other character below `0x20`, and any character beyond `size − 1`.
  - Store and echo every other character.

  It shall NUL-terminate the result and return its length.
- **Derives from:** SUB-CON-02
- **Verified by:** VER-SW-04

### SW-CON-04 — Enable interrupt receive
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `serial_irq_init(irq)` is called, it shall:
  1. set the RX-FIFO-full threshold to 1, preserving the other `UART_CONF1` bits;
  2. clear all UART0 interrupt status;
  3. enable only `RXFIFO_FULL`;
  4. map interrupt source 34 (UART0) to `irq`;
  5. register the receive handler on `irq`.
- **Derives from:** SUB-CON-03, SUB-EXC-04
- **Verified by:** VER-SW-05

### SW-CON-05 — Receive handler
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When the UART0 interrupt runs, the handler shall drain the RX FIFO into the 256-byte ring buffer, count each byte dropped because the buffer is full as an overrun, and then clear `RXFIFO_FULL`.
- **Derives from:** SUB-CON-03
- **Verified by:** VER-SW-05

### SW-CON-06 — Sleeping getc
- **Type:** Software
- **EARS:** State-driven
- **Statement:** While interrupt receive is enabled, `getc` shall check the ring buffer with interrupts masked by `irq_save`. If the buffer holds data, it shall return the oldest byte; otherwise it shall execute `waiti 0` and check again. It shall restore the caller's `PS` before returning.
- **Derives from:** SUB-CON-03
- **Verified by:** VER-SW-05

### SW-CON-07 — Polled getc
- **Type:** Software
- **EARS:** State-driven
- **Statement:** While interrupt receive is not enabled, `getc` shall poll the RX FIFO count and return the first byte read.
- **Derives from:** SUB-CON-02
- **Verified by:** VER-SW-04

### SW-FMT-01 — Conversion semantics
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** The formatter shall render `%d %i %u %x %X %s %c %%`, the `-` and `0` flags and the field width as ISO C does, and handle these cases as follows:
  - accept and ignore the length modifiers `l`, `h` and `z`;
  - print `%p` as `0x` followed by 8 hex digits;
  - print a NULL `%s` argument as `(null)`;
  - print an unknown conversion character verbatim;
  - return the number of characters produced.
- **Derives from:** SUB-CON-04
- **Verified by:** VER-SW-06

### SW-FMT-02 — Unbuffered printf, terminated sprintf
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** `pp_printf` shall pass each character to `putc` without an intermediate buffer, and `pp_sprintf` shall NUL-terminate its output.
- **Derives from:** SUB-CON-04
- **Verified by:** VER-SW-06

### SW-FMT-03 — printf alias
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** The link shall resolve the symbol `printf` to `pp_printf`.
- **Derives from:** SUB-CON-04
- **Verified by:** VER-SW-06

## Exceptions and interrupts (SWCI-1, SS-EXC)

### SW-EXC-01 — Window handler sequences
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When a window overflow or underflow exception is taken, its handler shall store or reload:
  - `a0`–`a3` at callee-SP −16 to −4;
  - for call8 frames, also `a4`–`a7` at caller-SP −32 to −20;
  - for call12 frames, also `a4`–`a11` at caller-SP −48 to −20.

  It shall then return with `rfwo` or `rfwu`.
- **Derives from:** SUB-EXC-01
- **Verified by:** VER-SW-07

### SW-EXC-02 — User-vector dispatch
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When the user exception vector is entered, it shall save `a0` in `EXCSAVE1`, then branch on `EXCCAUSE`:
  - 4 goes to the level-1 handler;
  - 5 goes to the alloca handler;
  - anything else goes to `_panic` with kind `KIND_USER`.
- **Derives from:** SUB-EXC-03, SUB-EXC-02, SUB-EXC-05
- **Verified by:** VER-SW-08

### SW-EXC-03 — Level-1 handler sequence
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When a level-1 interrupt is dispatched, the handler shall:
  1. build a frame at SP − 16 − 96;
  2. save `a0`–`a15`, `EPC1`, `PS`, `SAR`, `LBEG`, `LEND` and `LCOUNT`;
  3. set `LCOUNT` to 0;
  4. set `PS` to `WOE | UM | INTLEVEL(1)`;
  5. spill all other register windows;
  6. set SP to the frame and call `irq_dispatch(frame)`;
  7. restore `PS` (`EXCM` = 1) and every saved register;
  8. execute `rfe`.
- **Derives from:** SUB-EXC-03
- **Verified by:** VER-SW-08

### SW-EXC-04 — Alloca handler sequence
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When the alloca exception is dispatched, the handler shall:
  1. set `PS.OWB` to the faulting window;
  2. restore the faulting function's `a0` from `EXCSAVE1`;
  3. rotate to the caller's window according to `a0` bits 31–30 (01: call4, 10: call8, 11: call12);
  4. jump to the matching underflow handler.
- **Derives from:** SUB-EXC-02
- **Verified by:** VER-SW-07

### SW-EXC-05 — irq_init
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `irq_init` is called, it shall write 6 (an internal line, which ignores the matrix) to all 69 `PRO_INTR_MAP` registers, write 0 to `INTENABLE`, and write `0xFFFFFFFF` to `INTCLEAR`.
- **Derives from:** SUB-EXC-04
- **Verified by:** VER-SW-09

### SW-EXC-06 — irq_request
- **Type:** Software
- **EARS:** Unwanted behaviour
- **Statement:** If `irq_request` is given a line outside 0–31 or a line that is not level 1, then it shall return −1 and change nothing. Otherwise it shall store the handler and argument, enable the line, and return 0.
- **Derives from:** SUB-EXC-04
- **Verified by:** VER-SW-09

### SW-EXC-07 — irq_dispatch
- **Type:** Software
- **EARS:** State-driven
- **Statement:** While `INTERRUPT & INTENABLE & 0x000637FF` is non-zero, `irq_dispatch` shall take the lowest-numbered line. If that line is 7 or 10, it shall clear the line through `INTCLEAR` first. It shall then increment the line's count and call its handler.
- **Derives from:** SUB-EXC-04
- **Verified by:** VER-SW-09

### SW-EXC-08 — Unhandled line
- **Type:** Software
- **EARS:** Unwanted behaviour
- **Statement:** If a pending, enabled level-1 line has no registered handler, then `irq_dispatch` shall disable the line and print `irq N: no handler, disabled`.
- **Derives from:** SUB-EXC-04
- **Verified by:** VER-SW-09

### SW-EXC-09 — Critical sections
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** `irq_save` shall raise `PS.INTLEVEL` to 3 (`rsil 3`) and return the previous `PS`. `irq_restore` shall write the given `PS` back and execute `rsync`.
- **Derives from:** SUB-EXC-04, SUB-CON-03
- **Verified by:** VER-SW-09

### SW-EXC-10 — Enable and disable
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** `irq_enable` and `irq_disable` shall read, modify and write `INTENABLE` inside a critical section.
- **Derives from:** SUB-EXC-04
- **Verified by:** VER-SW-09

### SW-EXC-11 — Fatal vectors
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When the vectors at offsets `0x180`, `0x1C0`, `0x200`, `0x240`, `0x280`, `0x2C0`, `0x300` or `0x3C0` are entered, each shall save `a0` in `EXCSAVE1`, load its fault kind (`KIND_LEVEL(2…7)`, `KIND_KERNEL`, `KIND_DOUBLE`) and jump to `_panic`.
- **Derives from:** SUB-EXC-05
- **Verified by:** VER-SW-10

## Timekeeping (SWCI-1, SS-TIME)

### SW-TIME-01 — timer_init
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `timer_init(hz)` is called, it shall set the period to `CPU_HZ / hz` cycles, set `CCOMPARE0` to `CCOUNT` plus one period, and register the tick handler on line 6.
- **Derives from:** SUB-TIME-01
- **Verified by:** VER-SW-11

### SW-TIME-02 — Tick handler
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When the tick interrupt runs, the handler shall repeat the following until `(s32)(next − CCOUNT) > 0`, starting from `next` = `CCOMPARE0`:
  1. add one period to `next`;
  2. increment `jiffies`;
  3. write `next` to `CCOMPARE0`.
- **Derives from:** SUB-TIME-01, SUB-TIME-02
- **Verified by:** VER-SW-11

### SW-TIME-03 — udelay
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** `udelay(us)` shall busy-wait until `CCOUNT` has advanced by `us × (CPU_HZ / 1000000)` cycles, with unsigned arithmetic that stays correct across a `CCOUNT` wrap.
- **Derives from:** SUB-TIME-03
- **Verified by:** VER-SW-11

### SW-TIME-04 — Constants
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** The software shall define `HZ` = 100 and `CPU_HZ` = 40000000 by default, with `CPU_HZ` overridable at compile time.
- **Derives from:** SUB-TIME-01, SUB-TIME-03
- **Verified by:** VER-SW-11

## GPIO (SWCI-1, SS-GPIO)

### SW-GPIO-01 — Valid pins
- **Type:** Software
- **EARS:** Unwanted behaviour
- **Statement:** If a GPIO number is below 0, 40 or above, has no IO_MUX entry (24 and 28–31), or is in 6–11, then `gpio_valid` shall return false.
- **Derives from:** SUB-GPIO-02
- **Verified by:** VER-SW-12

### SW-GPIO-02 — Argument checks first
- **Type:** Software
- **EARS:** Unwanted behaviour
- **Statement:** If the pin is invalid, `afnum` is outside 0–5, or output is requested on GPIO 34 or above, then `gpio_dir_af` shall return −1 before writing any register.
- **Derives from:** SUB-GPIO-02
- **Verified by:** VER-SW-12

### SW-GPIO-03 — Function select
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `gpio_dir_af` accepts a request, it shall:
  1. write the IO_MUX `MCU_SEL` field with the hardware function, with 0 and 2 swapped;
  2. set `FUN_IE`;
  3. for AF0 only, write `GPIO_PINn` = 0 and `GPIO_FUNCn_OUT_SEL` = `256 | OEN_SEL`, then call `gpio_dir`.
- **Derives from:** SUB-GPIO-01
- **Verified by:** VER-SW-12

### SW-GPIO-04 — Direction
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `gpio_dir` is called for output, it shall first set the level through the `OUT(1)_W1TS` or `OUT(1)_W1TC` register, then set the enable bit through `ENABLE(1)_W1TS`. For input, it shall clear the enable bit through `ENABLE(1)_W1TC`.
- **Derives from:** SUB-GPIO-01
- **Verified by:** VER-SW-12

### SW-GPIO-05 — Level access
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** `__gpio_get` shall return the pin's bit of `IN` or `IN1` (0 or the bit value), `gpio_get` shall return 0 or 1, and `__gpio_set`/`gpio_set` shall write the pin's bit to the W1TS register for non-zero values and to W1TC for zero.
- **Derives from:** SUB-GPIO-01
- **Verified by:** VER-SW-12

## Monitor (SWCI-1, SS-MON)

### SW-MON-01 — Number parsing
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** The monitor shall parse addresses and values as hex with an optional `0x`/`0X` prefix, and GPIO and function numbers as decimal. Each number token must be followed by a blank or the end of the line.
- **Derives from:** SUB-MON-01, SUB-MON-02
- **Verified by:** VER-SW-13

### SW-MON-02 — Output formats
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** The monitor shall print results in these formats:
  - `read AAAAAAAA` followed by `VVVVVVVV` on the next line;
  - `write AAAAAAAA = VVVVVVVV`;
  - dump lines as `AAAAAAAA: w w w w`;
  - `gpio N <- v`, `gpio N = v` and `gpio N: function F`;
  - `go AAAAAAAA`.

  All addresses and values are 8 lower-case hex digits.
- **Derives from:** SUB-MON-01
- **Verified by:** VER-SW-13

### SW-MON-03 — Dump default
- **Type:** Software
- **EARS:** Optional feature
- **Statement:** Where `d` is given no count, the monitor shall dump 16 words.
- **Derives from:** SUB-MON-01
- **Verified by:** VER-SW-13

### SW-MON-04 — Self-test checks
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `s` is entered, the monitor shall check that:
  - `recurse(200)` returns 20100;
  - `vla_after_spill(100)` returns 919;
  - one software interrupt on line 7 causes exactly one handler call;
  - the ticks counted during `udelay(100000)` are within `HZ/10 ± 1`.

  It shall print a line per check and `all ok` or `FAILED`.
- **Derives from:** SUB-MON-01
- **Verified by:** VER-SW-13

### SW-MON-05 — Fault demos
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `f n` is entered, the monitor shall act on n as follows:
  - 0: load from address 0;
  - 1: execute `ill`;
  - 2: divide 100 by a volatile zero with `quos`;
  - 3: execute `break 1, 15`;
  - 4: set `a1` = `0x100` and spin;
  - 5: enable line 29 and set it pending;
  - any other value: do nothing.
- **Derives from:** SUB-MON-01
- **Verified by:** VER-SW-13

### SW-MON-06 — Statistics format
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `i` is entered, the monitor shall print `uptime S.CC s (N ticks)`, then `irq NN: count` for every line with a non-zero count, in ascending order.
- **Derives from:** SUB-MON-01
- **Verified by:** VER-SW-13

### SW-MON-07 — main
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `main` runs, it shall:
  1. print the banner and the memory line;
  2. call `irq_init`, `timer_init(HZ)` and `serial_irq_init(17)`;
  3. run `mimmo`, or, in blink mode, configure `LED_GPIO` as an output and toggle it every 500 ms, printing `led N`.
- **Derives from:** SUB-MON-03
- **Verified by:** VER-SW-13

## Faults (SWCI-1, SS-FLT)

### SW-FLT-01 — _panic capture
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `_panic` is entered with the kind in `a0`, it shall:
  1. keep the kind in `MISC0` and the incoming `PS` in `MISC1`;
  2. set `PS` = `EXCM | UM | WOE | INTLEVEL(15)`;
  3. store into `panic_frame`: `a0`–`a15`, the kind, `PS`, `EXCCAUSE`, `EXCVADDR`, `SAR`, `DEPC`, `LBEG`, `LEND`, `LCOUNT`, `WINDOWBASE`, `WINDOWSTART`, `EPC1`–`EPC7` and `EPS2`–`EPS7`;
  4. reset the register window;
  5. set SP to the top of a 2 KB private stack;
  6. set `PS` = `UM | WOE | INTLEVEL(15)`;
  7. call `panic_handler(&panic_frame)`.
- **Derives from:** SUB-FLT-01
- **Verified by:** VER-SW-14

### SW-FLT-02 — Report format
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `panic_handler` runs, it shall print a first line that depends on the kind:
  - user or kernel: `*** Fatal|Kernel exception N: Name`;
  - double: `*** Double exception (cause N while handling an exception at EPC1)`;
  - level 6: `*** Debug exception (break?)`;
  - level 7: `*** NMI`;
  - levels 2–5: `*** Unexpected high-level interrupt`.

  For levels 2–7 it shall add `level L, pending X`. It shall then print the `pc`/`ps` line (with `excvaddr` for memory faults), the registers 4 per line, the `sar`/loop line, the window line, `called from ~X` and `Press any key to reboot`.
- **Derives from:** SUB-FLT-02
- **Verified by:** VER-SW-14

### SW-FLT-03 — Cause names
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** `panic_handler` shall name the causes 0–3, 5, 6, 8, 9, 12–18, 20, 24–26, 28, 29 and 32 using the Xtensa exception names, and print `?` for any other cause.
- **Derives from:** SUB-FLT-02
- **Verified by:** VER-SW-14

### SW-FLT-04 — Nested fault
- **Type:** Software
- **EARS:** Unwanted behaviour
- **Statement:** If `panic_handler` is entered a second time, then it shall spin without printing.
- **Derives from:** SUB-FLT-04
- **Verified by:** VER-SW-14

### SW-FLT-05 — Reboot
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When the report has been printed, the fault subsystem shall poll the UART0 RX FIFO for one byte and then write `SW_SYS_RST` to `RTC_CNTL_OPTIONS0`.
- **Derives from:** SUB-FLT-03
- **Verified by:** VER-SW-14

## Support library (SWCI-1, SS-LIB)

### SW-LIB-01 — Helpers
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** `memset`, `memcpy` (for non-overlapping areas) and `strlen` shall behave as specified by ISO C and return their ISO C results.
- **Derives from:** SUB-LIB-01
- **Verified by:** VER-SW-15

## Image tool (SWCI-2, SS-BLD)

### SW-IMG-01 — Usage
- **Type:** Software
- **EARS:** Unwanted behaviour
- **Statement:** If `mkimage` is not given exactly two arguments, then it shall print `use: <prog> <in.elf> <out.bin>` and exit with status 1.
- **Derives from:** SUB-BLD-04
- **Verified by:** VER-SW-16

### SW-IMG-02 — Input validation
- **Type:** Software
- **EARS:** Unwanted behaviour
- **Statement:** If the input cannot be read, is shorter than 52 bytes, lacks the ELF magic, or is not ELFCLASS32, little-endian and `EM_XTENSA` (94), then `mkimage` shall print a diagnostic naming the file and exit with status 1.
- **Derives from:** SUB-BLD-04
- **Verified by:** VER-SW-16

### SW-IMG-03 — Segments
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** `mkimage` shall emit one segment per `PT_LOAD` program header with `p_filesz` > 0, in program-header order, at `p_paddr`, zero-padded to a multiple of 4 bytes. It shall fail if there are more than 16 such segments, none at all, or a segment that extends past the end of the file.
- **Derives from:** SUB-BLD-04
- **Verified by:** VER-SW-16

### SW-IMG-04 — Header values
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** `mkimage` shall write the header bytes `E9`, the segment count, `02` (DIO), `20` (4 MB, 40 MHz) and the entry point. It shall write the extended header as: WP pin `EE`, drive strengths 0, chip ID 0, minimum revision 0, maximum revision `FFFF`, reserved 0, and hash-appended 0.
- **Derives from:** SUB-BLD-04
- **Verified by:** VER-SW-16

### SW-IMG-05 — Checksum
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** `mkimage` shall append zero bytes until the file length is 15 modulo 16, then one checksum byte equal to `0xEF` XORed with every segment data byte.
- **Derives from:** SUB-BLD-04
- **Verified by:** VER-SW-16

### SW-IMG-06 — Summary
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `mkimage` succeeds, it shall print one line per segment (address and length), then the output name, entry point, total size and checksum.
- **Derives from:** SUB-BLD-04
- **Verified by:** VER-SW-16

## Documentation tooling (SWCI-3, SS-DOC)

### SW-DOC-01 — Trace checker
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `tools/tracecheck.py` runs, it shall parse `docs/requirements/*.md` and the tags in `docs/features/*.feature`.
  - It shall report as errors: duplicate IDs; unknown parents or verified IDs; parents of the wrong level; requirements without verification; `VER` entries without exactly one TAID method; and feature tags naming unknown IDs.
  - It shall report as warnings: non-leaf requirements without children, and `VER` evidence tags that no scenario carries.
  - Unless `--check` is given, it shall write `docs/traceability.md`.
  - It shall exit with status 1 if there are errors.
- **Derives from:** SUB-DOC-01
- **Verified by:** VER-SW-19

## Build scripts (SWCI-3, SS-BLD)

### SW-BLD-01 — Variables
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** The Makefile shall default to `CROSS_COMPILE=xtensa-esp32-elf-`, `PORT=/dev/ttyUSB0`, `ESPTOOL=esptool.py`, `QEMU=qemu-system-xtensa` and `HOSTCC=cc`, all overridable on the command line.
- **Derives from:** SUB-BLD-05
- **Verified by:** VER-SW-17

### SW-BLD-02 — Flash image for QEMU
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `flash.img` is built, it shall be 4 MiB of `0xFF` with `e32.bin` written at offset `0x1000`.
- **Derives from:** SUB-BLD-05, SUB-VEN-01
- **Verified by:** VER-SW-17

### SW-BLD-03 — Serial targets
- **Type:** Software
- **EARS:** Event-driven
- **Statement:** When `make ram` is run, it shall invoke `ESPTOOL --chip esp32 -p PORT --no-stub load_ram e32.bin`. When `make flash` is run, it shall invoke `ESPTOOL --chip esp32 -p PORT -b 460800 write_flash -fm keep -ff keep -fs keep 0x1000 e32.bin`.
- **Derives from:** SUB-BLD-05
- **Verified by:** VER-SW-17

### SW-BLD-04 — Linker script contents
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** `esp32.lds` shall set the entry to `call_start` and keep `.vectors` and then `.text.boot` first in `.text`. It shall define `__bss_start`, `__bss_end` and `_stack_top`, provide `printf = pp_printf`, and assert both the 8 KB stack margin and that `_vector_table` is at the start of IRAM.
- **Derives from:** SUB-BLD-02, SUB-BLD-03
- **Verified by:** VER-SW-17

### SW-BLD-05 — Compiler and linker flags
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** The Makefile shall:
  - compile with `-Os -g -Wall -ffreestanding -nostdlib -Iinclude -mtext-section-literals $(EXTRA_CFLAGS)`;
  - link with `-nostdlib -T esp32.lds -Wl,-Map=e32.map`;
  - name libgcc by the path printed by `$(CC) -print-libgcc-file-name`, and no other library.
- **Derives from:** SUB-BLD-01
- **Verified by:** VER-SW-17

### SW-TC-01 — Toolchain script
- **Type:** Software
- **EARS:** Ubiquitous
- **Statement:** `tools/build-toolchain.sh` shall:
  - honour `PREFIX`, `WORK` and `J`;
  - clone `espressif/binutils-gdb` at `esp-2.47.0_20261109` and `espressif/gcc` at `esp-14.4.0_20261030`, and the `xtensa-overlays` repository;
  - copy the `xtensa_esp32` overlay into both trees;
  - configure, build and install binutils (no gdb or sim) and a C-only GCC with libgcc;
  - stop at the first failing command.
- **Derives from:** SUB-BLD-06
- **Verified by:** VER-SW-18
