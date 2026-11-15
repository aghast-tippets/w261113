@EP-01 @FEAT-004
Feature: FEAT-004: Build from source
  Epic: EP-01 Build from source without an SDK   ·   Level: interface

  Supports: US-01 via SYS-08 → SUB-BLD-02 → IF-08
  Supports: US-03 via STK-03 → SYS-05 → SUB-BOOT-01 → IF-08
  Supports: US-05 via STK-03 → SYS-05 → SUB-BOOT-01 → IF-08
  Supports: US-08 via STK-17 → SYS-23 → SUB-BLD-02 → IF-08
  Supports: US-18 via STK-11 → SYS-15 → SUB-BOOT-01 → IF-08
  Supports: US-19 via STK-08 → SYS-16 → SUB-BOOT-01 → IF-08
  Supports: US-21 via STK-08 → SYS-16 → SUB-BOOT-01 → IF-08
  Supports: US-29 via STK-08 → SYS-16 → SUB-BOOT-01 → IF-08

  Background:
    Given a clean checkout of e32
    And xtensa-esp32-elf-gcc is on the PATH

  @IF-08
  Rule: IF-08: Linker symbol contract
    EARS: The linker script shall export the following, and the startup and vector code shall use only these names for the memory layout:
      - `_vector_table`, equal to `0x40080000`;
      - the entry point `call_start`;
      - `__bss_start` and `__bss_end`, both 4-byte aligned;
      - `_stack_top`, equal to `0x3FFDC000` and 16-byte aligned;
      - the alias `printf = pp_printf`.
      `vectors.S` defines `_panic_stack_top`.

    @host @SUB-BLD-02 @VER-SUB-01
    Scenario Outline: IF-08-S01: Linker symbols sit where the memory map says
      When I run "xtensa-esp32-elf-nm e32.elf"
      Then the symbol "<symbol>" has the value <value>

      Examples:
        | symbol        | value      |
        | _vector_table | 0x40080000 |
        | _stack_top    | 0x3ffdc000 |
