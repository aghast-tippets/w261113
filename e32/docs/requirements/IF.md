# Interface requirements (IF)

Level 5. What crosses the *boundary* between two elements? Each interface
names its two sides and derives from the system or subsystem requirements
that need it. Interfaces are verified by contract tests, or by inspection
where the compiler or linker already enforces the contract.

| ID | Interface | Side A | Side B |
|---|---|---|---|
| IF-01 | Boot image format | SS-BLD (`mkimage`) | Boot ROM (HW-11) |
| IF-02 | ROM-to-firmware hand-over | Boot ROM | SS-BOOT (`call_start`) |
| IF-03 | Serial console protocol | Firmware (SS-CON, SS-MON, SS-FLT) | Operator's terminal |
| IF-04 | Host loader transport | SS-BLD (`make ram`/`flash`) | esptool ↔ boot ROM |
| IF-05 | Vector table layout | LX6 core (HW-13) | SS-EXC (`vectors.S`) |
| IF-06 | Interrupt frame layout | `vectors.S` | `irq.c` (C) |
| IF-07 | Panic frame layout | `vectors.S` | `panic.c` (C) |
| IF-08 | Linker symbol contract | `esp32.lds` | `boot.S`, `vectors.S`, `main.c` |
| IF-09 | Interrupt API | SS-EXC | Integrator code, SS-CON, SS-TIME, SS-MON |
| IF-10 | GPIO API | SS-GPIO | SS-MON, integrator code |
| IF-11 | Console API | SS-CON, SS-LIB, SS-TIME | All target software |
| IF-12 | Interrupt matrix registers | SS-EXC | ESP32 interrupt matrix (DPORT) |
| IF-13 | Peripheral register map | Target software | ESP32 peripherals |
| IF-14 | Watchdog write-protect protocol | SS-BOOT | RTC_CNTL and TIMG watchdogs |
| IF-15 | Windowed-ABI stack save areas | SS-EXC window handlers | Compiler-generated code |
| IF-16 | Emulator invocation | SS-VEN (make, test harness) | Espressif QEMU |

---

### IF-01 — Boot image format
- **Type:** Interface
- **EARS:** Ubiquitous
- **Statement:** The image passed from `mkimage` to the boot ROM shall consist of these parts, all little-endian:
  - an 8-byte header: magic `0xE9`, segment count (1–16), SPI mode, a byte with the flash size in the high nibble and the frequency in the low nibble, and a 32-bit entry address;
  - a 16-byte extended header: WP pin, 3 drive-strength bytes, a 16-bit chip ID, a minimum revision byte, 16-bit minimum and maximum full revisions, 4 reserved bytes and a hash-appended flag;
  - for each segment, a 32-bit load address, a 32-bit length that is a multiple of 4, and the data;
  - zero padding to 15 modulo 16, then a checksum byte equal to `0xEF` XORed with all segment data.
- **Derives from:** SYS-04, SYS-05, SUB-BLD-04
- **Verified by:** VER-IF-01

### IF-02 — ROM-to-firmware hand-over
- **Type:** Interface
- **EARS:** Event-driven
- **Statement:** When the boot ROM has loaded every segment, it shall call the entry point, `call_start`. At that moment the firmware shall assume only the following:
  - its segments are in place;
  - UART0 is configured by the ROM;
  - the CPU is running windowed code on a ROM stack, with ROM vectors and possibly ROM-enabled interrupts.

  It shall assume nothing about any other register, and shall never return to the ROM.
- **Derives from:** SUB-BOOT-01, SUB-BOOT-03
- **Verified by:** VER-IF-02

### IF-03 — Serial console protocol
- **Type:** Interface
- **EARS:** Ubiquitous
- **Statement:** The console shall use 115200 baud 8N1, no flow control, ASCII. The firmware sends CR LF for each newline. Input lines end with CR or LF, BS (`0x08`) or DEL (`0x7F`) erases, and accepted characters are echoed. The firmware prompts with `> `, answers malformed commands with `?? (h for help)`, and uses the output formats of SW-MON-02 and SW-FLT-02.
- **Derives from:** SYS-06, SYS-07, SYS-10, SYS-19
- **Verified by:** VER-IF-03

### IF-04 — Host loader transport
- **Type:** Interface
- **EARS:** Event-driven
- **Statement:** When the board is in ROM download mode, the host shall drive the ROM's serial loader through esptool:
  - `load_ram` without the flasher stub, to load and run in RAM;
  - `write_flash` at `0x1000` with flash mode, frequency and size all set to `keep`.

  No other host tool shall be required to load the firmware.
- **Derives from:** SYS-05, SYS-26, SYS-27
- **Verified by:** VER-IF-04

### IF-05 — Vector table layout
- **Type:** Interface
- **EARS:** Ubiquitous
- **Statement:** `VECBASE` shall point to a 1 KB-aligned table with entry points at these offsets:
  - `0x000`/`0x040`: window overflow/underflow 4;
  - `0x080`/`0x0C0`: window overflow/underflow 8;
  - `0x100`/`0x140`: window overflow/underflow 12;
  - `0x180`, `0x1C0`, `0x200`, `0x240`: interrupt levels 2–5;
  - `0x280`: debug (level 6);
  - `0x2C0`: NMI (level 7);
  - `0x300`: kernel exception;
  - `0x340`: user exception;
  - `0x3C0`: double exception.

  Each entry must fit before the next offset.
- **Derives from:** SUB-EXC-01, SUB-EXC-03, SUB-EXC-05
- **Verified by:** VER-IF-05

### IF-06 — Interrupt frame layout
- **Type:** Interface
- **EARS:** Ubiquitous
- **Statement:** The frame passed from `_level1_handler` to `irq_dispatch` shall be 0x60 bytes, laid out as follows:
  - `a0`–`a15` at offsets `0x00`–`0x3C`;
  - `pc` (`EPC1`) at `0x40`, `ps` at `0x44`, `sar` at `0x48`;
  - `lbeg` at `0x4C`, `lend` at `0x50`, `lcount` at `0x54`;
  - padding to `0x60`.

  This layout is defined once, in `include/xtensa.h`, for both languages.
- **Derives from:** SUB-EXC-03
- **Verified by:** VER-IF-06

### IF-07 — Panic frame layout
- **Type:** Interface
- **EARS:** Ubiquitous
- **Statement:** `panic_frame` shall be 0xA0 bytes, laid out as follows:
  - the kind at `0x00`;
  - `a0`–`a15` at `0x04`–`0x40`;
  - `exccause` at `0x44`, `excvaddr` at `0x48`, `ps` at `0x4C`, `sar` at `0x50`, `depc` at `0x54`;
  - `lbeg` at `0x58`, `lend` at `0x5C`, `lcount` at `0x60`;
  - `windowbase` at `0x64`, `windowstart` at `0x68`;
  - `epc1`–`epc7` at `0x6C`–`0x84`;
  - `eps2`–`eps7` at `0x88`–`0x9C`.
- **Derives from:** SUB-FLT-01, SUB-FLT-02
- **Verified by:** VER-IF-06

### IF-08 — Linker symbol contract
- **Type:** Interface
- **EARS:** Ubiquitous
- **Statement:** The linker script shall export the following, and the startup and vector code shall use only these names for the memory layout:
  - `_vector_table`, equal to `0x40080000`;
  - the entry point `call_start`;
  - `__bss_start` and `__bss_end`, both 4-byte aligned;
  - `_stack_top`, equal to `0x3FFDC000` and 16-byte aligned;
  - the alias `printf = pp_printf`.

  `vectors.S` defines `_panic_stack_top`.
- **Derives from:** SUB-BLD-02, SUB-BOOT-01
- **Verified by:** VER-IF-07

### IF-09 — Interrupt API
- **Type:** Interface
- **EARS:** Ubiquitous
- **Statement:** `include/irq.h` shall offer:
  - `irq_init(void)`;
  - `irq_map(int source, int irq)`;
  - `irq_request(int irq, irq_handler_t fn, void *arg)`, which returns 0 or −1;
  - `irq_enable(int)` and `irq_disable(int)`;
  - `irq_count(int)`;
  - `irq_save()` and `irq_restore(u32)`;
  - `timer_init(int hz)`, `jiffies` and `HZ`;
  - `serial_irq_init(int irq)`;
  - `reboot(void)`.

  Handlers have the signature `void fn(int irq, void *arg)`, run with level-1 interrupts masked, and must not use floating point.
- **Derives from:** SYS-16, SYS-17, SUB-EXC-04
- **Verified by:** VER-IF-08

### IF-10 — GPIO API
- **Type:** Interface
- **EARS:** Ubiquitous
- **Statement:** `include/gpio.h` shall offer:
  - `GPIO_NR`, `GPIO_PORT` and `GPIO_BIT`;
  - `gpio_init`;
  - `gpio_dir_af(gpio, output, value, afnum)` and `gpio_dir(gpio, output, value)`, which return 0 or −1;
  - `gpio_get` and `gpio_set` (0 or 1);
  - `__gpio_get` and `__gpio_set` (raw bit).

  This matches the LPC1343 package's API, with AF0 meaning GPIO.
- **Derives from:** SYS-12, SYS-13, SYS-14, SUB-GPIO-01
- **Verified by:** VER-IF-09

### IF-11 — Console API
- **Type:** Interface
- **EARS:** Ubiquitous
- **Statement:** `include/io.h` shall offer:
  - `serial_setup`;
  - `putc`, and `puts` (which adds no newline);
  - `getc`, and `gets(s, size)`, which returns the length;
  - `printf`, `pp_printf` and `pp_sprintf`, with format checking;
  - `memset`, `memcpy` and `strlen`;
  - `udelay(us)`;
  - `wdt_disable`;
  - `mimmo`;
  - the `CPU_HZ` constant.
- **Derives from:** SYS-06, SYS-10, SUB-CON-01, SUB-CON-04
- **Verified by:** VER-IF-10

### IF-12 — Interrupt matrix registers
- **Type:** Interface
- **EARS:** Ubiquitous
- **Statement:** The firmware shall route peripheral source `s` (0–68) to the PRO CPU by writing a CPU line number (0–31) to `0x3FF00104 + 4·s`. UART0 is source 34. Writing an internal line (6, 7, 11, 15, 16 or 29) disconnects the source.
- **Derives from:** SUB-EXC-04, SUB-CON-03
- **Verified by:** VER-IF-11

### IF-13 — Peripheral register map
- **Type:** Interface
- **EARS:** Ubiquitous
- **Statement:** The firmware shall access peripherals only at the addresses defined in `include/regs.h`:
  - UART0 at `0x3FF40000` (FIFO `0x00`, INT_ST `0x08`, INT_ENA `0x0C`, INT_CLR `0x10`, CLKDIV `0x14`, STATUS `0x1C`, CONF0 `0x20`, CONF1 `0x24`);
  - GPIO at `0x3FF44000`;
  - IO_MUX at `0x3FF49000`;
  - RTC_CNTL at `0x3FF48000` (OPTIONS0 `0x00`, WDTCONFIG0 `0x8C`, WDTWPROTECT `0xA4`);
  - TIMG0 and TIMG1 at `0x3FF5F000` and `0x3FF60000` (WDTCONFIG0 `0x48`, WDTWPROTECT `0x64`).
- **Derives from:** SUB-CON-01, SUB-GPIO-01, SUB-BOOT-02, SUB-FLT-03
- **Verified by:** VER-IF-12

### IF-14 — Watchdog write-protect protocol
- **Type:** Interface
- **EARS:** Event-driven
- **Statement:** When software changes a watchdog's configuration, it shall first write `0x50D83AA1` to that watchdog's `WPROTECT` register, then write the configuration, then write any other value (0) to `WPROTECT` to lock it again.
- **Derives from:** SUB-BOOT-02
- **Verified by:** VER-IF-13

### IF-15 — Windowed-ABI save areas
- **Type:** Interface
- **EARS:** Ubiquitous
- **Statement:** The window handlers and the compiler-generated code shall share these stack conventions:
  - a frame's `a0`–`a3` are saved in the 16 bytes below its callee's stack pointer;
  - a call8 frame's `a4`–`a7` (or a call12 frame's `a4`–`a11`) are saved at the bottom of its caller's frame, whose stack pointer is read from `[sp − 12]`;
  - the 16 bytes below an interrupted stack pointer are left untouched by interrupt entry.
- **Derives from:** SUB-EXC-01, SUB-EXC-03
- **Verified by:** VER-IF-14

### IF-16 — Emulator invocation
- **Type:** Interface
- **EARS:** Ubiquitous
- **Statement:** The verification environment shall start QEMU as `qemu-system-xtensa -nographic -machine esp32 -drive file=flash.img,if=mtd,format=raw`. For download mode it shall add `-global driver=esp32.gpio,property=strap_mode,value=0x0f`, and put the console on stdio (`-serial stdio`) or TCP (`-serial tcp::PORT,server,nowait`).
- **Derives from:** SYS-24, SUB-VEN-01
- **Verified by:** VER-IF-15
