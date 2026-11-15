@EP-03 @FEAT-029
Feature: FEAT-029: Console I/O
  Epic: EP-03 Console input and output   ·   Level: interface

  Supports: US-09 via IF-03
  Supports: US-11 via STK-05 → SYS-06 → IF-11
  Supports: US-12 via SYS-10 → IF-11
  Supports: US-14 via SYS-10 → IF-11
  Supports: US-22 via SYS-19 → SUB-CON-04 → IF-11

  @IF-03
  Rule: IF-03: Serial console protocol
    EARS: The console shall use 115200 baud 8N1, no flow control, ASCII. The firmware sends CR LF for each newline. Input lines end with CR or LF, BS (`0x08`) or DEL (`0x7F`) erases, and accepted characters are echoed. The firmware prompts with `> `, answers malformed commands with `?? (h for help)`, and uses the output formats of SW-MON-02 and SW-FLT-02.

    @qemu @SYS-06 @VER-SYS-06 @VER-STK-04
    Scenario: IF-03-S01: Banner and prompt after boot
      When the firmware is booted in QEMU from flash
      Then the console shows a line matching /^e32: bare-metal ESP32, built \w{3} [ \d]\d \d{4} \d\d:\d\d:\d\d$/
      And the console shows a line matching /^bss 0x3ffb[0-9a-f]{4}-0x3ffb[0-9a-f]{4}, stack top 0x3ffdc000$/
      And the console shows "mimmo.c: Ready to get input (h for help)"
      And the console shows "> "

  @IF-11
  Rule: IF-11: Console API
    EARS: `include/io.h` shall offer:
      - `serial_setup`;
      - `putc`, and `puts` (which adds no newline);
      - `getc`, and `gets(s, size)`, which returns the length;
      - `printf`, `pp_printf` and `pp_sprintf`, with format checking;
      - `memset`, `memcpy` and `strlen`;
      - `udelay(us)`;
      - `wdt_disable`;
      - `mimmo`;
      - the `CPU_HZ` constant.
