@EP-01 @F-03
Feature: Toolchain from source
  As a maintainer
  I want a script that builds the cross-compiler from pinned sources
  So that the exact toolchain can be reproduced anywhere

  @host @pending @SYS-25 @SUB-BLD-06 @SW-TC-01 @CMP-36 @VER-SYS-21 @VER-STK-02
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

  @host @pending @CMP-36 @VER-SYS-21
  Scenario: CMP-36-S02: A second run does not clone again
    Given the script has completed once in "/tmp/w"
    When I run "PREFIX=/tmp/tc WORK=/tmp/w tools/build-toolchain.sh"
    Then the output does not contain "Cloning into"
