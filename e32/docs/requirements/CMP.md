# Component / unit requirements (CMP)

Level 6. What must each individual *building block* do? A component is a
source file or a function group within one. Each entry states the unit's
contract (inputs, outputs, preconditions and side effects), derives from the
software or hardware requirements it realises, and is verified by a unit
test.

---

## Startup and vectors

### CMP-01 — boot.S: call_start
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When entered from the boot ROM, `call_start` shall perform, in this order:
  1. `INTENABLE` = 0;
  2. `WINDOWSTART` = 1, `WINDOWBASE` = 0, `rsync`;
  3. `VECBASE` = `_vector_table`;
  4. `a0` = 0, `a1` = `_stack_top`, `PS` = `0x00040020`;
  5. clear BSS one word at a time;
  6. `call4 wdt_disable`, `call4 serial_setup`, `call4 main`;
  7. loop forever.

  Precondition: segments loaded by the ROM. It never returns.
- **Derives from:** SW-BOOT-01, SW-BOOT-02, SW-BOOT-03, SW-BOOT-04, SW-BOOT-05, SW-BOOT-06, HW-11
- **Component:** `boot.S`
- **Rationale:** Needed to meet SW-BOOT-01 (Mask interrupts first); SW-BOOT-02 (Reset the register window); SW-BOOT-03 (Install vectors before the first call); SW-BOOT-04 (Stack and processor state); SW-BOOT-05 (Clear BSS); SW-BOOT-06 (Call sequence); HW-11 (Boot ROM behaviour relied on).
- **Verified by:** VER-CMP-01

### CMP-02 — vectors.S: window overflow/underflow 4
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When entered at `VECBASE+0x000`, the overflow-4 handler shall store `a0`–`a3` at `[a5−16..a5−4]` and execute `rfwo`. When entered at `+0x040`, the underflow-4 handler shall load `a0`–`a3` from the same addresses and execute `rfwu`.
- **Derives from:** SW-EXC-01, HW-13
- **Component:** `vectors.S`
- **Rationale:** Needed to meet SW-EXC-01 (Window handler sequences); HW-13 (CPU core configuration).
- **Verified by:** VER-CMP-02

### CMP-03 — vectors.S: window overflow/underflow 8
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When entered at `+0x080`, the overflow-8 handler shall store `a0`–`a3` at `[a9−16..a9−4]`, and `a4`–`a7` at `[[a1−12]−32..−20]`. When entered at `+0x0C0`, the underflow-8 handler shall reload them from the same addresses. Each handler fits in 64 bytes.
- **Derives from:** SW-EXC-01, HW-13
- **Component:** `vectors.S`
- **Rationale:** Needed to meet SW-EXC-01 (Window handler sequences); HW-13 (CPU core configuration).
- **Verified by:** VER-CMP-02

### CMP-04 — vectors.S: window overflow/underflow 12
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When entered at `+0x100`, the overflow-12 handler shall store `a0`–`a3` at `[a13−16..a13−4]`, and `a4`–`a11` at `[[a1−12]−48..−20]`. When entered at `+0x140`, the underflow-12 handler shall reload them from the same addresses. Each handler fits in 64 bytes.
- **Derives from:** SW-EXC-01, HW-13
- **Component:** `vectors.S`
- **Rationale:** Needed to meet SW-EXC-01 (Window handler sequences); HW-13 (CPU core configuration).
- **Verified by:** VER-CMP-02

### CMP-05 — vectors.S: user exception vector
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When entered at `+0x340`, the vector shall save `a0` in `EXCSAVE1`, read `EXCCAUSE`, and jump to `_level1_handler` (cause 4), to `_alloca_handler` (cause 5), or to `_panic` with `a0` = 1 (any other cause), all within the 128-byte slot.
- **Derives from:** SW-EXC-02
- **Component:** `vectors.S`
- **Rationale:** Needed to meet SW-EXC-02 (User-vector dispatch).
- **Verified by:** VER-CMP-03

### CMP-06 — vectors.S: fatal vector stubs
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When any of the slots at `+0x180`, `+0x1C0`, `+0x200`, `+0x240`, `+0x280`, `+0x2C0`, `+0x300` or `+0x3C0` is entered, it shall save `a0` in `EXCSAVE1` and jump to `_panic`, with `a0` set respectively to `0x12`–`0x17` (`KIND_LEVEL(2…7)`), 2 (`KIND_KERNEL`) or 3 (`KIND_DOUBLE`).
- **Derives from:** SW-EXC-11
- **Component:** `vectors.S`
- **Rationale:** Needed to meet SW-EXC-11 (Fatal vectors).
- **Verified by:** VER-CMP-03

### CMP-07 — vectors.S: _alloca_handler
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When entered with `EXCCAUSE` = 5, the handler shall:
  1. rotate the window back by one;
  2. copy the faulting `WINDOWBASE` into `PS.OWB`;
  3. restore the faulting function's `a0` from `EXCSAVE1`;
  4. jump to `_WindowUnderflow4` if `a0[31]` = 0, to `_WindowUnderflow8` if `a0[31:30]` = 10, or to `_WindowUnderflow12` if they are 11, rotating one more window before each of the last two choices.
- **Derives from:** SW-EXC-04
- **Component:** `vectors.S`
- **Rationale:** Needed to meet SW-EXC-04 (Alloca handler sequence).
- **Verified by:** VER-CMP-04

### CMP-08 — vectors.S: _level1_handler
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When entered with `EXCCAUSE` = 4, the handler shall carry out the SW-EXC-03 sequence using the IF-06 frame, and return with `rfe` with every saved register, `EPC1`, `PS`, `SAR`, `LBEG`, `LEND` and `LCOUNT` restored to its value at entry.
- **Derives from:** SW-EXC-03
- **Component:** `vectors.S`
- **Rationale:** Needed to meet SW-EXC-03 (Level-1 handler sequence).
- **Verified by:** VER-CMP-05

### CMP-09 — vectors.S: _panic
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When entered with the kind in `a0` and the original `a0` in `EXCSAVE1`, `_panic` shall fill `panic_frame` (IF-07), then call `panic_handler(&panic_frame)` on the private 2 KB stack with `PS.INTLEVEL` = 15. It never returns.
- **Derives from:** SW-FLT-01
- **Component:** `vectors.S`
- **Rationale:** Needed to meet SW-FLT-01 (_panic capture).
- **Verified by:** VER-CMP-06

## Interrupt core and time

### CMP-10 — irq.c: irq_init, irq_map
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When `irq_init()` is called, it shall write 6 to every `PRO_INTR_MAP(0..68)`, set `INTENABLE` = 0 and `INTCLEAR` = `0xFFFFFFFF`. `irq_map(s, n)` shall write n to `PRO_INTR_MAP(s)`.
- **Derives from:** SW-EXC-05
- **Component:** `irq.c`
- **Rationale:** Needed to meet SW-EXC-05 (irq_init).
- **Verified by:** VER-CMP-07

### CMP-11 — irq.c: irq_request, irq_enable, irq_disable, irq_count
- **Type:** Component
- **EARS:** Unwanted behaviour
- **Priority:** Must
- **Statement:** If `irq_request` is called with `irq` ∉ [0, 31] or with `(1<<irq) & 0x000637FF` = 0, then it shall return −1 and change nothing. Otherwise it shall store `fn` and `arg` in the line's descriptor, set `INTENABLE` bit `irq` under `irq_save`, and return 0. `irq_count(n)` shall return the dispatch count of line `n & 31`.
- **Derives from:** SW-EXC-06, SW-EXC-10
- **Component:** `irq.c`
- **Rationale:** Needed to meet SW-EXC-06 (irq_request); SW-EXC-10 (Enable and disable).
- **Verified by:** VER-CMP-07

### CMP-12 — irq.c: irq_dispatch
- **Type:** Component
- **EARS:** State-driven
- **Priority:** Must
- **Statement:** While `INTERRUPT & INTENABLE & 0x000637FF` is non-zero, `irq_dispatch` shall pick n = ctz(pending). If bit n is in `0x480`, it shall write it to `INTCLEAR`. It shall then increment `count[n]` and call `fn(n, arg)`, or, if there is no `fn`, clear `INTENABLE` bit n and print `irq n: no handler, disabled`.
- **Derives from:** SW-EXC-07, SW-EXC-08
- **Component:** `irq.c`
- **Rationale:** Needed to meet SW-EXC-07 (irq_dispatch); SW-EXC-08 (Unhandled line).
- **Verified by:** VER-CMP-07

### CMP-13 — timer.c
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When `timer_init(hz)` is called, it shall set `tick_cycles` = `CPU_HZ/hz` and `CCOMPARE0` = `CCOUNT + tick_cycles`, and request line 6. When `timer_tick` runs, it shall execute the SW-TIME-02 loop. Postcondition: `(s32)(CCOMPARE0 − CCOUNT) > 0` at the moment of the final check.
- **Derives from:** SW-TIME-01, SW-TIME-02, HW-13
- **Component:** `timer.c`
- **Rationale:** Needed to meet SW-TIME-01 (timer_init); SW-TIME-02 (Tick handler); HW-13 (CPU core configuration).
- **Verified by:** VER-CMP-08

### CMP-14 — wdt.c
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When `wdt_disable()` is called, it shall perform the sequence `writel(KEY, WPROTECT)`, `writel(0, CONFIG0)`, `writel(0, WPROTECT)` for RTC (`0xA4`/`0x8C`), TIMG0 and TIMG1 (`0x64`/`0x48`), in that order.
- **Derives from:** SW-WDT-01
- **Component:** `wdt.c`
- **Rationale:** Needed to meet SW-WDT-01 (Disable each watchdog).
- **Verified by:** VER-CMP-09

## Console

### CMP-15 — io.c: putc, puts
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When `putc(c)` is called with `c` = `'\n'`, it shall call `putc('\r')` first. It shall then spin while `TXCNT(STATUS)` ≥ 126 and write `c & 0xFF` to the FIFO. `puts(s)` shall call `putc` for each character of `s`, without adding a newline.
- **Derives from:** SW-CON-02
- **Component:** `io.c`
- **Rationale:** Needed to meet SW-CON-02 (putc).
- **Verified by:** VER-CMP-10

### CMP-16 — io.c: getc, gets
- **Type:** Component
- **EARS:** State-driven
- **Priority:** Must
- **Statement:** While `rx_irq_mode` is 0, `getc` shall poll the FIFO. While it is 1, `getc` shall apply the SW-CON-06 loop. `gets(s, size)` shall implement SW-CON-03. Precondition: `size` ≥ 1. Postcondition: `s` is NUL-terminated, and its length is at most `size − 1`.
- **Derives from:** SW-CON-03, SW-CON-06, SW-CON-07
- **Component:** `io.c`
- **Rationale:** Needed to meet SW-CON-03 (gets); SW-CON-06 (Sleeping getc); SW-CON-07 (Polled getc).
- **Verified by:** VER-CMP-10

### CMP-17 — io.c: serial_irq_init, uart_rx_irq
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When `serial_irq_init(irq)` is called, it shall perform the SW-CON-04 steps and set `rx_irq_mode` = 1 before enabling the line. When `uart_rx_irq` runs, it shall store bytes while `rx_head − rx_tail` < 256, otherwise increment `rx_overruns`, and finally write `RXFIFO_FULL` to `INT_CLR`.
- **Derives from:** SW-CON-04, SW-CON-05
- **Component:** `io.c`
- **Rationale:** Needed to meet SW-CON-04 (Enable interrupt receive); SW-CON-05 (Receive handler).
- **Verified by:** VER-CMP-10

### CMP-18 — io.c: serial_setup
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When `serial_setup()` is called, it shall spin until `TXCNT(STATUS)` = 0, and shall write no UART register.
- **Derives from:** SW-CON-01, HW-11
- **Component:** `io.c`
- **Rationale:** Needed to meet SW-CON-01 (Keep the ROM's UART set-up); HW-11 (Boot ROM behaviour relied on).
- **Verified by:** VER-CMP-10

### CMP-19 — pp_printf.c: formatter core
- **Type:** Component
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** `pp_format(out, arg, fmt, ap)` shall emit, through `out`, the same characters that ISO C `printf` produces for the SW-FMT-01 subset, and return their count. `emit_padded` shall place the sign before zero padding and after space padding.
- **Derives from:** SW-FMT-01
- **Component:** `pp_printf.c`
- **Rationale:** Needed to meet SW-FMT-01 (Conversion semantics).
- **Verified by:** VER-CMP-11

### CMP-20 — pp_printf.c: pp_printf, pp_sprintf
- **Type:** Component
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** `pp_printf` shall call `pp_format` with a `putc` sink. `pp_sprintf(buf, …)` shall write into `buf` and NUL-terminate it. Precondition: `buf` is large enough. Both shall return the character count, excluding the NUL.
- **Derives from:** SW-FMT-02
- **Component:** `pp_printf.c`
- **Rationale:** Needed to meet SW-FMT-02 (Unbuffered printf, terminated sprintf).
- **Verified by:** VER-CMP-11

## GPIO

### CMP-21 — gpio.c: pad table and validity
- **Type:** Component
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** `gpio_mux[40]` shall hold `(IO_MUX address − 0x3FF49000)/4` for each existing pad, and 0 for 24 and 28–31. `gpio_valid(n)` shall return 1 only for 0 ≤ n < 40, with a non-zero entry and n ∉ [6, 11]. `af_to_hw` shall map 0→2, 2→0, and any other value to itself.
- **Derives from:** SW-GPIO-01, SW-GPIO-03, HW-07, HW-08
- **Component:** `gpio.c`
- **Rationale:** Needed to meet SW-GPIO-01 (Valid pins); SW-GPIO-03 (Function select); HW-07 (Flash pins); HW-08 (Input-only pins).
- **Verified by:** VER-CMP-12

### CMP-22 — gpio.c: gpio_dir_af, gpio_dir
- **Type:** Component
- **EARS:** Unwanted behaviour
- **Priority:** Must
- **Statement:** If the arguments fail SW-GPIO-02, then `gpio_dir_af` shall return −1 with no register written. Otherwise it shall perform SW-GPIO-03 and return 0, or return the result of `gpio_dir` for AF0. `gpio_dir` shall perform SW-GPIO-04 and return 0.
- **Derives from:** SW-GPIO-02, SW-GPIO-03, SW-GPIO-04
- **Component:** `gpio.c`
- **Rationale:** Needed to meet SW-GPIO-02 (Argument checks first); SW-GPIO-03 (Function select); SW-GPIO-04 (Direction).
- **Verified by:** VER-CMP-12

### CMP-23 — gpio.c and gpio.h: level access
- **Type:** Component
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** `__gpio_get(n)` shall return `IN[port] & (1<<bit)`. `__gpio_set(n, v)` shall write `1<<bit` to `OUT_W1TS[port]` if `v` ≠ 0, or to `OUT_W1TC[port]` otherwise. The inline `gpio_get` and `gpio_set` shall wrap them.
- **Derives from:** SW-GPIO-05
- **Component:** `gpio.c`, `include/gpio.h`
- **Rationale:** Needed to meet SW-GPIO-05 (Level access).
- **Verified by:** VER-CMP-12

## Monitor and main

### CMP-24 — mimmo.c: get_num
- **Type:** Component
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** `get_num(&s, base, &v)` shall skip blanks and accept an optional `0x` prefix only in base 16. It shall accumulate the digits valid in `base`, and fail with −1, leaving `s` and `v` untouched, on: no digits; a digit not valid in `base`; or a following character that is not a blank or NUL. On success it shall advance `s` and return 0.
- **Derives from:** SW-MON-01
- **Component:** `mimmo.c`
- **Rationale:** Needed to meet SW-MON-01 (Number parsing).
- **Verified by:** VER-CMP-13

### CMP-25 — mimmo.c: command loop
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When a line is read, `mimmo()` shall dispatch on its first non-blank character, produce the SW-MON-02, SW-MON-03 and SW-MON-06 outputs, print `?? (h for help)` for any error, and print `> ` before each read. It never returns.
- **Derives from:** SW-MON-02, SW-MON-03, SW-MON-06
- **Component:** `mimmo.c`
- **Rationale:** Needed to meet SW-MON-02 (Output formats); SW-MON-03 (Dump default); SW-MON-06 (Statistics format).
- **Verified by:** VER-CMP-13

### CMP-26 — mimmo.c: self_test
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When `self_test()` is called, it shall evaluate the four SW-MON-04 checks. `recurse(n)` shall be a genuinely recursive, non-inlined function that returns n(n+1)/2. `vla_after_spill(n)` shall call `recurse(40)` before declaring `char buf[n]`, and return 820 + (n−1) mod 256. It shall leave line 7 disabled afterwards.
- **Derives from:** SW-MON-04
- **Component:** `mimmo.c`
- **Rationale:** Needed to meet SW-MON-04 (Self-test checks).
- **Verified by:** VER-CMP-13

### CMP-27 — mimmo.c: fault
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When `fault(n)` is called, it shall execute the SW-MON-05 action for n ∈ 0–5, using volatile operands so that the compiler cannot remove or rewrite the faulting operation.
- **Derives from:** SW-MON-05
- **Component:** `mimmo.c`
- **Rationale:** Needed to meet SW-MON-05 (Fault demos).
- **Verified by:** VER-CMP-13

### CMP-28 — panic.c: panic_handler
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When `panic_handler(f)` is called, it shall select the PC and PS for `f->kind` as follows:
  - user or kernel: `EPC1` and `f->ps`;
  - double: `DEPC` and `f->ps`;
  - level L: `EPC[L]` and `EPS[L]`.

  It shall then print the SW-FLT-02 report, with names from SW-FLT-03. A second call shall spin silently. Compile-time assertions shall check the IF-06 and IF-07 offsets.
- **Derives from:** SW-FLT-02, SW-FLT-03, SW-FLT-04
- **Component:** `panic.c`
- **Rationale:** Needed to meet SW-FLT-02 (Report format); SW-FLT-03 (Cause names); SW-FLT-04 (Nested fault).
- **Verified by:** VER-CMP-14

### CMP-29 — panic.c: panic_getc, reboot
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When called, `panic_getc()` shall poll the UART0 RX FIFO and return one byte. When called, `reboot()` shall write `0x80000000` to `RTC_CNTL_OPTIONS0` and spin.
- **Derives from:** SW-FLT-05, HW-12
- **Component:** `panic.c`
- **Rationale:** Needed to meet SW-FLT-05 (Reboot); HW-12 (Software system reset).
- **Verified by:** VER-CMP-14

## Support library

### CMP-30 — lib.c: memset, memcpy, strlen
- **Type:** Component
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** `memset(s, c, n)` shall store `(u8)c` in `n` bytes and return `s`. `memcpy(d, s, n)` shall copy `n` bytes forwards and return `d`. `strlen(s)` shall return the number of bytes before the first NUL.
- **Derives from:** SW-LIB-01
- **Component:** `lib.c`
- **Rationale:** Needed to meet SW-LIB-01 (Helpers).
- **Verified by:** VER-CMP-15

### CMP-31 — lib.c: udelay
- **Type:** Component
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** `udelay(us)` shall return once `get_ccount() − start` ≥ `us · (CPU_HZ/1000000)`, computed in `u32` arithmetic. Precondition: `us · 40` < 2³².
- **Derives from:** SW-TIME-03, SW-TIME-04, HW-02
- **Component:** `lib.c`
- **Rationale:** Needed to meet SW-TIME-03 (udelay); SW-TIME-04 (Constants); HW-02 (Crystal).
- **Verified by:** VER-CMP-15

### CMP-32 — main.c: main
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When `main()` is called, it shall print the banner and memory lines, call `irq_init`, `timer_init(HZ)` and `serial_irq_init(17)`, then run `mimmo()`. In blink mode it shall instead run the `LED_GPIO` toggle loop (500 ms, printing `led N`). It never returns.
- **Derives from:** SW-MON-07
- **Component:** `main.c`
- **Rationale:** Needed to meet SW-MON-07 (main).
- **Verified by:** VER-CMP-16

## Headers

### CMP-37 — include/xtensa.h
- **Type:** Component
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** `xtensa.h` shall define the `PS` bits, `EXCCAUSE` codes, line masks, fault kinds (`KIND_LEVEL` without spaces, for use as a gas macro argument) and the `IF_*`/`PF_*` offsets for both assembly and C. It shall define `struct irq_frame` and `struct panic_frame`. `RSR` and `WSR` shall access special registers, with `WSR` followed by `rsync`. `irq_save` shall be `rsil 3`, and `irq_restore` shall be `wsr ps; rsync`.
- **Derives from:** SW-EXC-09, HW-13
- **Component:** `include/xtensa.h`
- **Rationale:** Needed to meet SW-EXC-09 (Critical sections); HW-13 (CPU core configuration).
- **Verified by:** VER-CMP-17

### CMP-38 — include/types.h
- **Type:** Component
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** `types.h` shall define `u8`, `u16`, `u32` and `s32` with exactly 8, 16, 32 and 32 bits. `readl` and `writel(val, addr)` shall perform a single volatile 32-bit access. `get_ccount` shall return `rsr.ccount`.
- **Derives from:** SW-CON-02, SW-TIME-03
- **Component:** `include/types.h`
- **Rationale:** Needed to meet SW-CON-02 (putc); SW-TIME-03 (udelay).
- **Verified by:** VER-CMP-17

### CMP-39 — include/regs.h
- **Type:** Component
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** `regs.h` shall define every peripheral address and field used by the firmware, with the values of IF-12 and IF-13 written as full hex constants, and nothing else.
- **Derives from:** SW-CON-02, SW-CON-04, SW-WDT-01, SW-GPIO-03, SW-FLT-05
- **Component:** `include/regs.h`
- **Rationale:** Needed to meet SW-CON-02 (putc); SW-CON-04 (Enable interrupt receive); SW-WDT-01 (Disable each watchdog); SW-GPIO-03 (Function select); SW-FLT-05 (Reboot).
- **Verified by:** VER-CMP-17

## Host tools and build files

### CMP-33 — tools/mkimage.c
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When invoked as `mkimage in.elf out.bin`, the tool shall implement SW-IMG-01 to SW-IMG-06 in portable C99 with no dependency beyond the C standard library, and exit with 0 on success or 1 on any error.
- **Derives from:** SW-IMG-01, SW-IMG-02, SW-IMG-03, SW-IMG-04, SW-IMG-05, SW-IMG-06, HW-03, HW-11
- **Component:** `tools/mkimage.c`
- **Rationale:** Needed to meet SW-IMG-01 (Usage); SW-IMG-02 (Input validation); SW-IMG-03 (Segments); SW-IMG-04 (Header values); SW-IMG-05 (Checksum); SW-IMG-06 (Summary); HW-03 (SPI flash); HW-11 (Boot ROM behaviour relied on).
- **Verified by:** VER-CMP-18

### CMP-34 — esp32.lds
- **Type:** Component
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** `esp32.lds` shall define the `iram` region (`0x40080000`, 128 KB) and the `dram` region (`0x3FFB0000`, 176 KB), and the output sections `.text` (`.vectors`, `.text.boot`, then all literals and text), `.data` (`.rodata*`, `.data*`) and `.bss` (`NOLOAD`), with the symbols and assertions of SW-BLD-04.
- **Derives from:** SW-BLD-04, SW-FMT-03, HW-09, HW-10
- **Component:** `esp32.lds`
- **Rationale:** Needed to meet SW-BLD-04 (Linker script contents); SW-FMT-03 (printf alias); HW-09 (Free SRAM after hand-over); HW-10 (IRAM access width).
- **Verified by:** VER-CMP-19

### CMP-35 — Makefile
- **Type:** Component
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The Makefile shall:
  - build each object from its `.c` or `.S` source, rebuilding C objects when any header in `include/` changes;
  - link `e32.elf` and print its size;
  - build `tools/mkimage` with `HOSTCC`;
  - produce `e32.bin`;
  - implement the SW-BLD-01 to SW-BLD-03 variables and targets.
- **Derives from:** SW-BLD-01, SW-BLD-02, SW-BLD-03, SW-BLD-05
- **Component:** `Makefile`
- **Rationale:** Needed to meet SW-BLD-01 (Variables); SW-BLD-02 (Flash image for QEMU); SW-BLD-03 (Serial targets); SW-BLD-05 (Compiler and linker flags).
- **Verified by:** VER-CMP-19

### CMP-36 — tools/build-toolchain.sh
- **Type:** Component
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** `build-toolchain.sh` shall be a POSIX `sh` script with `set -e` that implements SW-TC-01. It shall be idempotent with respect to already-cloned trees, which it does not clone again.
- **Derives from:** SW-TC-01
- **Component:** `tools/build-toolchain.sh`
- **Rationale:** Needed to meet SW-TC-01 (Toolchain script).
- **Verified by:** VER-CMP-20

### CMP-40 — tools/tracecheck.py
- **Type:** Component
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When run with Python 3 and no third-party modules, `tracecheck.py` shall implement SW-DOC-01. The level rules it enforces are:
  - `STK` derives from `BR`;
  - `SYS` from `STK`;
  - `SUB` from `SYS`;
  - `HW` and `SW` from `SUB`;
  - `IF` from `SYS` or `SUB`;
  - `CMP` from `HW` or `SW`.
- **Derives from:** SW-DOC-01
- **Component:** `tools/tracecheck.py`
- **Rationale:** Needed to meet SW-DOC-01 (Trace checker).
- **Verified by:** VER-CMP-21
