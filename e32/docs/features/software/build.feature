@EP-01 @FEAT-003
Feature: FEAT-003: Build from source
  Epic: EP-01 Build from source without an SDK   ·   Level: software

  Supports: US-01 via SYS-08 → SUB-BLD-02 → SW-BLD-04
  Supports: US-02 via STK-01 → SYS-01 → SUB-LIB-01 → SW-LIB-01
  Supports: US-08 via STK-17 → SYS-23 → SUB-BLD-02 → SW-BLD-04
  Supports: US-09 via STK-05 → SYS-06 → SUB-CON-04 → SW-FMT-03
  Supports: US-11 via STK-05 → SYS-06 → SUB-CON-04 → SW-FMT-03
  Supports: US-12 via SYS-10 → SUB-CON-04 → SW-FMT-03
  Supports: US-14 via SYS-10 → SUB-CON-04 → SW-FMT-03
  Supports: US-22 via SYS-19 → SUB-CON-04 → SW-FMT-03
  Supports: US-25 via SUB-BLD-05 → SW-BLD-01

  Background:
    Given a clean checkout of e32
    And xtensa-esp32-elf-gcc is on the PATH

  @SW-BLD-01
  Rule: SW-BLD-01: Variables
    EARS: The Makefile shall default to `CROSS_COMPILE=xtensa-esp32-elf-`, `PORT=/dev/ttyUSB0`, `ESPTOOL=esptool.py`, `QEMU=qemu-system-xtensa` and `HOSTCC=cc`, all overridable on the command line.

  @SW-BLD-04
  Rule: SW-BLD-04: Linker script contents
    EARS: `esp32.lds` shall set the entry to `call_start` and keep `.vectors` and then `.text.boot` first in `.text`. It shall define `__bss_start`, `__bss_end` and `_stack_top`, provide `printf = pp_printf`, and assert both the 8 KB stack margin and that `_vector_table` is at the start of IRAM.

    @host @SUB-BLD-03 @VER-SUB-02
    Scenario: SW-BLD-04-S01: Link fails when the stack margin is too small
      Given a build variant with "char big_buffer[170 * 1024];" added to lib.c
      When I run "make e32.elf"
      Then the command fails with "less than 8kB left for stack"

  @SW-BLD-05
  Rule: SW-BLD-05: Compiler and linker flags
    EARS: The Makefile shall:
      - compile with `-Os -g -Wall -ffreestanding -nostdlib -Iinclude -mtext-section-literals $(EXTRA_CFLAGS)`;
      - link with `-nostdlib -T esp32.lds -Wl,-Map=e32.map`;
      - name libgcc by the path printed by `$(CC) -print-libgcc-file-name`, and no other library.

  @SW-FMT-03
  Rule: SW-FMT-03: printf alias
    EARS: The link shall resolve the symbol `printf` to `pp_printf`.

    @host @VER-SW-06
    Scenario: SW-FMT-03-S01: printf is an alias of pp_printf
      When I run "xtensa-esp32-elf-nm e32.elf"
      Then the symbols "printf" and "pp_printf" have the same value

  @SW-LIB-01
  Rule: SW-LIB-01: Helpers
    EARS: `memset`, `memcpy` (for non-overlapping areas) and `strlen` shall behave as specified by ISO C and return their ISO C results.
