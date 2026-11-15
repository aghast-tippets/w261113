@EP-01 @FEAT-002
Feature: FEAT-002: Build from source
  Epic: EP-01 Build from source without an SDK   ·   Level: subsystem

  Supports: US-01 via SUB-BLD-01
  Supports: US-02 via STK-01 → SYS-01 → SUB-LIB-01
  Supports: US-08 via STK-17 → SYS-23 → SUB-BLD-03

  Background:
    Given a clean checkout of e32
    And xtensa-esp32-elf-gcc is on the PATH

  @SUB-BLD-01
  Rule: SUB-BLD-01: Compilation rules
    EARS: The build subsystem shall compile every firmware source with `-Os -g -Wall -ffreestanding -nostdlib -mtext-section-literals`, and link with `-nostdlib` against libgcc only.

    @host @SYS-01 @SYS-03 @VER-SYS-01 @VER-STK-01
    Scenario: SUB-BLD-01-S01: Clean build produces the ELF and the image
      When I run "make clean all"
      Then the command succeeds
      And the file "e32.elf" exists
      And the file "e32.bin" exists
      And the output of "make" contains "text	   data	    bss"

    @host @SYS-01 @VER-SYS-01 @VER-STK-01
    Scenario: SUB-BLD-01-S02: Only libgcc may be linked
      When I run "make"
      Then the link command contains "-nostdlib"
      And the only library on the link line is libgcc
      And "e32.map" lists no archive member from any library

  @SUB-BLD-03
  Rule: SUB-BLD-03: Layout guards
    EARS: If fewer than 8 KB remain between the end of BSS and the stack top, or the vector table is not at the start of IRAM, then the build subsystem shall fail the link with a message.

  @SUB-LIB-01
  Rule: SUB-LIB-01: Freestanding helpers
    EARS: The support library shall provide `memset`, `memcpy` and `strlen` with ISO C semantics, for the firmware and for compiler-generated calls.
