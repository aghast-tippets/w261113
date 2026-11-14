@EP-01 @F-01
Feature: Build from source
  As a developer
  I want to build the firmware with a bare cross-compiler and make
  So that the project depends on no vendor SDK

  Background:
    Given a clean checkout of e32
    And xtensa-esp32-elf-gcc is on the PATH

  @host @SYS-01 @SYS-03 @SUB-BLD-01 @VER-SYS-01 @VER-STK-01
  Scenario: SUB-BLD-01-S01: Clean build produces the ELF and the image
    When I run "make clean all"
    Then the command succeeds
    And the file "e32.elf" exists
    And the file "e32.bin" exists
    And the output of "make" contains "text	   data	    bss"

  @host @SYS-02 @VER-SYS-01
  Scenario: SYS-02-S01: Build is warning-free
    When I run "make clean all 2>&1"
    Then the output does not contain "warning"

  @host @SYS-01 @SUB-BLD-01 @VER-SYS-01 @VER-STK-01
  Scenario: SUB-BLD-01-S02: Only libgcc may be linked
    When I run "make"
    Then the link command contains "-nostdlib"
    And the only library on the link line is libgcc
    And "e32.map" lists no archive member from any library

  @host @SYS-08 @VER-SYS-05 @VER-STK-01
  Scenario: SYS-08-S01: No ROM code is referenced
    When I run "xtensa-esp32-elf-objdump -d e32.elf"
    Then no call or jump instruction targets an address from 0x40000000 to 0x4006ffff
    And the instruction "wsr.vecbase" appears in call_start before "call4 wdt_disable"

  @host @SUB-BLD-02 @IF-08 @VER-SUB-01
  Scenario Outline: IF-08-S01: Linker symbols sit where the memory map says
    When I run "xtensa-esp32-elf-nm e32.elf"
    Then the symbol "<symbol>" has the value <value>

    Examples:
      | symbol        | value      |
      | _vector_table | 0x40080000 |
      | _stack_top    | 0x3ffdc000 |

  @host @SW-FMT-03 @VER-SW-06
  Scenario: SW-FMT-03-S01: printf is an alias of pp_printf
    When I run "xtensa-esp32-elf-nm e32.elf"
    Then the symbols "printf" and "pp_printf" have the same value

  @host @SUB-BLD-03 @SW-BLD-04 @VER-SUB-02
  Scenario: SW-BLD-04-S01: Link fails when the stack margin is too small
    Given a build variant with "char big_buffer[170 * 1024];" added to lib.c
    When I run "make e32.elf"
    Then the command fails with "less than 8kB left for stack"

  @host @SW-BOOT-01 @SW-BOOT-02 @SW-BOOT-03 @SW-BOOT-04 @SW-BOOT-05 @SW-BOOT-06 @CMP-01 @VER-SW-01
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

  @host @IF-05 @HW-13 @CMP-02 @CMP-05 @CMP-06 @VER-IF-05
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

  @host @SUB-LIB-01 @SW-LIB-01 @CMP-30 @VER-CMP-15 @VER-SUB-18 @VER-SW-15
  Scenario: CMP-30-S01: Support library matches ISO C
    Given lib.c compiled for the host with its functions renamed
    When I compare memset for lengths 0 to 64, memcpy for lengths 0 to 32 at an offset, and strlen for 4 strings with the C library
    Then there are 0 failures

  @host @CMP-35 @VER-SUB-04
  Scenario: CMP-35-S01: A header change rebuilds the C objects
    Given the firmware is built
    When I touch "include/regs.h" and run "make"
    Then every C object is compiled again
