@EP-01 @FEAT-001
Feature: FEAT-001: Build from source
  Epic: EP-01 Build from source without an SDK   ·   Level: system

  User stories delivered:
    US-01  As a developer, I want to build the firmware with a single `make`
           using only a bare cross-compiler, so that I depend on no vendor SDK or
           C library.
    US-02  As a developer, I want a warning-free build that reports the section
           sizes, so that I notice regressions immediately.
    US-03  As a developer, I want the ELF converted into a boot-ROM image as part
           of the build, so that I can load or flash it directly.
    US-05  As a developer, I want to load and start the firmware in RAM over the
           serial port, so that I iterate without writing flash.
    US-06  As a developer, I want to store the firmware in flash at `0x1000`, so
           that it starts on its own after every reset.

  Actors: Firmware developer (ACT-H1, persona "dana")

  Background:
    Given a clean checkout of e32
    And xtensa-esp32-elf-gcc is on the PATH

  @SYS-01
  Rule: SYS-01: Bare-toolchain build
    EARS: The e32 build shall produce the firmware from source using only an xtensa-esp32-elf GCC toolchain (compiler, binutils, libgcc), GNU make and a host C compiler.

  @SYS-02 @US-02
  Rule: SYS-02: Warning-free build
    EARS: The e32 build shall complete with no compiler or linker warnings with `-Wall` enabled.

    @host @VER-SYS-01
    Scenario: SYS-02-S01: Build is warning-free
      When I run "make clean all 2>&1"
      Then the output does not contain "warning"

  @SYS-03
  Rule: SYS-03: Build outputs
    EARS: When `make` is run, the e32 build shall produce `e32.elf` and a boot-ROM image `e32.bin`, and print the section sizes.

  @SYS-08 @US-01
  Rule: SYS-08: No boot-ROM code at run time
    EARS: While the e32 firmware is running, it shall execute no code in the boot ROM: no ROM functions, and no ROM exception vectors after the vector base is installed.

    @host @VER-SYS-05 @VER-STK-01
    Scenario: SYS-08-S01: No ROM code is referenced
      When I run "xtensa-esp32-elf-objdump -d e32.elf"
      Then no call or jump instruction targets an address from 0x40000000 to 0x4006ffff
      And the instruction "wsr.vecbase" appears in call_start before "call4 wdt_disable"
