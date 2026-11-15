@EP-01 @FEAT-005
Feature: FEAT-005: Build from source
  Epic: EP-01 Build from source without an SDK   ·   Level: unit

  Supports: US-01 via SYS-08 → SUB-BOOT-01 → SW-BOOT-01 → CMP-01
  Supports: US-02 via STK-01 → SYS-01 → SUB-LIB-01 → SW-LIB-01 → CMP-30
  Supports: US-03 via HW-11 → CMP-01
  Supports: US-05 via STK-03 → SYS-05 → SUB-BOOT-01 → SW-BOOT-01 → CMP-01
  Supports: US-06 via HW-11 → CMP-01
  Supports: US-07 via SYS-09 → SUB-BOOT-02 → SW-BOOT-06 → CMP-01
  Supports: US-09 via STK-05 → SYS-07 → SUB-BOOT-03 → SW-BOOT-06 → CMP-01
  Supports: US-11 via STK-05 → SYS-07 → SUB-BOOT-03 → SW-BOOT-06 → CMP-01
  Supports: US-18 via STK-11 → SYS-15 → SUB-BOOT-01 → SW-BOOT-01 → CMP-01
  Supports: US-19 via STK-08 → SYS-16 → SUB-BOOT-01 → SW-BOOT-01 → CMP-01
  Supports: US-20 via STK-09 → SYS-17 → SUB-TIME-01 → HW-13 → CMP-02
  Supports: US-21 via STK-08 → SYS-16 → SUB-BOOT-01 → SW-BOOT-01 → CMP-01
  Supports: US-22 via SYS-19 → SUB-EXC-05 → HW-13 → CMP-02
  Supports: US-25 via SW-BLD-02 → CMP-35
  Supports: US-29 via STK-08 → SYS-16 → SUB-BOOT-01 → SW-BOOT-01 → CMP-01

  Background:
    Given a clean checkout of e32
    And xtensa-esp32-elf-gcc is on the PATH

  @CMP-01
  Rule: CMP-01: boot.S: call_start
    EARS: When entered from the boot ROM, `call_start` shall perform, in this order:
      1. `INTENABLE` = 0;
      2. `WINDOWSTART` = 1, `WINDOWBASE` = 0, `rsync`;
      3. `VECBASE` = `_vector_table`;
      4. `a0` = 0, `a1` = `_stack_top`, `PS` = `0x00040020`;
      5. clear BSS one word at a time;
      6. `call4 wdt_disable`, `call4 serial_setup`, `call4 main`;
      7. loop forever.
      Precondition: segments loaded by the ROM. It never returns.

    @host @SW-BOOT-01 @SW-BOOT-02 @SW-BOOT-03 @SW-BOOT-04 @SW-BOOT-05 @SW-BOOT-06 @VER-SW-01
    Scenario: CMP-01-S01: Startup code runs its steps in the required order
      When I disassemble "call_start"
      Then the instructions appear in this order:
        | step                                         |
        | wsr.intenable with 0                         |
        | wsr.windowstart with 1                       |
        | wsr.windowbase with 0, then rsync            |
        | wsr.vecbase with 0x40080000, then rsync      |
        | a1 loaded with 0x3ffdc000                    |
        | wsr.ps with 0x00040020, then rsync           |
        | a loop storing zero from __bss_start to __bss_end |
        | call4 wdt_disable                            |
        | call4 serial_setup                           |
        | call4 main                                   |
        | a jump to itself                             |

  @CMP-02
  Rule: CMP-02: vectors.S: window overflow/underflow 4
    EARS: When entered at `VECBASE+0x000`, the overflow-4 handler shall store `a0`–`a3` at `[a5−16..a5−4]` and execute `rfwo`. When entered at `+0x040`, the underflow-4 handler shall load `a0`–`a3` from the same addresses and execute `rfwu`.

    @host @IF-05 @HW-13 @CMP-05 @CMP-06 @VER-IF-05
    Scenario Outline: CMP-02-S01: Vector entry points are at their architectural offsets
      When I run "xtensa-esp32-elf-objdump -d e32.elf"
      Then the code for "<vector>" starts at 0x40080000 + <offset>
      And it ends before 0x40080000 + <next>

      Examples:
        | vector                | offset | next  |
        | _WindowOverflow4      | 0x000  | 0x040 |
        | _WindowUnderflow4     | 0x040  | 0x080 |
        | _WindowOverflow8      | 0x080  | 0x0c0 |
        | _WindowUnderflow8     | 0x0c0  | 0x100 |
        | _WindowOverflow12     | 0x100  | 0x140 |
        | _WindowUnderflow12    | 0x140  | 0x180 |
        | level 2 stub          | 0x180  | 0x1c0 |
        | level 3 stub          | 0x1c0  | 0x200 |
        | level 4 stub          | 0x200  | 0x240 |
        | level 5 stub          | 0x240  | 0x280 |
        | debug stub            | 0x280  | 0x2c0 |
        | NMI stub              | 0x2c0  | 0x300 |
        | kernel stub           | 0x300  | 0x340 |
        | _UserExceptionVector  | 0x340  | 0x3c0 |
        | double exception stub | 0x3c0  | 0x400 |

  @CMP-05
  Rule: CMP-05: vectors.S: user exception vector
    EARS: When entered at `+0x340`, the vector shall save `a0` in `EXCSAVE1`, read `EXCCAUSE`, and jump to `_level1_handler` (cause 4), to `_alloca_handler` (cause 5), or to `_panic` with `a0` = 1 (any other cause), all within the 128-byte slot.

  @CMP-06
  Rule: CMP-06: vectors.S: fatal vector stubs
    EARS: When any of the slots at `+0x180`, `+0x1C0`, `+0x200`, `+0x240`, `+0x280`, `+0x2C0`, `+0x300` or `+0x3C0` is entered, it shall save `a0` in `EXCSAVE1` and jump to `_panic`, with `a0` set respectively to `0x12`–`0x17` (`KIND_LEVEL(2…7)`), 2 (`KIND_KERNEL`) or 3 (`KIND_DOUBLE`).

  @CMP-30
  Rule: CMP-30: lib.c: memset, memcpy, strlen
    EARS: `memset(s, c, n)` shall store `(u8)c` in `n` bytes and return `s`. `memcpy(d, s, n)` shall copy `n` bytes forwards and return `d`. `strlen(s)` shall return the number of bytes before the first NUL.

    @host @SUB-LIB-01 @SW-LIB-01 @VER-CMP-15 @VER-SUB-18 @VER-SW-15
    Scenario: CMP-30-S01: Support library matches ISO C
      Given lib.c compiled for the host with its functions renamed
      When I compare memset for lengths 0 to 64, memcpy for lengths 0 to 32 at an offset, and strlen for 4 strings with the C library
      Then there are 0 failures

  @CMP-35
  Rule: CMP-35: Makefile
    EARS: The Makefile shall:
      - build each object from its `.c` or `.S` source, rebuilding C objects when any header in `include/` changes;
      - link `e32.elf` and print its size;
      - build `tools/mkimage` with `HOSTCC`;
      - produce `e32.bin`;
      - implement the SW-BLD-01 to SW-BLD-03 variables and targets.

    @host @VER-SUB-04
    Scenario: CMP-35-S01: A header change rebuilds the C objects
      Given the firmware is built
      When I touch "include/regs.h" and run "make"
      Then every C object is compiled again
