@EP-01 @FEAT-012
Feature: FEAT-012: Toolchain from source
  Epic: EP-01 Build from source without an SDK   ·   Level: unit

  Supports: US-04 via CMP-36

  @CMP-36
  Rule: CMP-36: tools/build-toolchain.sh
    EARS: `build-toolchain.sh` shall be a POSIX `sh` script with `set -e` that implements SW-TC-01. It shall be idempotent with respect to already-cloned trees, which it does not clone again.

    @host @pending @SYS-25 @SUB-BLD-06 @SW-TC-01 @VER-SYS-21 @VER-STK-02
    Scenario: CMP-36-S01: The script builds a working C toolchain
      Given a Linux host with git, gcc, g++, make, flex, bison, texinfo and the GMP, MPFR and MPC headers
      And an empty directory "/tmp/w"
      When I run "PREFIX=/tmp/tc WORK=/tmp/w tools/build-toolchain.sh"
      Then the command succeeds
      And the file "/tmp/tc/bin/xtensa-esp32-elf-gcc" exists
      And the output of "/tmp/tc/bin/xtensa-esp32-elf-gcc -v" contains "--enable-languages=c"
      When I run "make clean all CROSS_COMPILE=/tmp/tc/bin/xtensa-esp32-elf-"
      Then the command succeeds
      And the output does not contain "warning"

    @host @pending @VER-SYS-21
    Scenario: CMP-36-S02: A second run does not clone again
      Given the script has completed once in "/tmp/w"
      When I run "PREFIX=/tmp/tc WORK=/tmp/w tools/build-toolchain.sh"
      Then the output does not contain "Cloning into"
