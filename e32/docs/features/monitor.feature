@EP-04 @F-08
Feature: Memory monitor
  As an operator
  I want to read, write, dump and call memory from the console
  So that I can inspect and poke a running board

  Background:
    Given the firmware is booted in QEMU from flash
    And the monitor prompt is shown

  @qemu @SYS-10 @SW-MON-02 @VER-SYS-08 @VER-STK-05
  Scenario: SW-MON-02-S01: Help lists every command
    When I enter "h"
    Then the console shows each of:
      | text            |
      | r <addr>        |
      | w <addr> <value>|
      | d <addr> [<count>] |
      | p <gpio> [0\|1] |
      | a <gpio> <af>   |
      | g <addr>        |
      | i               |
      | s               |
      | f <n>           |
      | h               |

  @qemu @SYS-10 @SW-MON-01 @SW-MON-02 @CMP-24 @CMP-25 @VER-SYS-08 @VER-STK-05
  Scenario: CMP-24-S01: Write then read a word of RAM
    When I enter "w 3ffb1000 cafe"
    Then the console shows "write 3ffb1000 = 0000cafe"
    When I enter "r 0x3ffb1000"
    Then the console shows "read 3ffb1000"
    And the console shows "0000cafe"

  @qemu @SYS-10 @SW-MON-03 @VER-SYS-08
  Scenario: SW-MON-03-S01: Dump defaults to 16 words, 4 per line
    When I enter "d 3ffb0000"
    Then the console shows 4 lines matching /^3ffb00[0-3]0:( [0-9a-f]{8}){4}$/

  @qemu @SYS-10 @VER-SYS-08
  Scenario: SYS-10-S01: Dump with a count
    When I enter "d 3ffb0000 8"
    Then the console shows 2 lines matching /^3ffb00[01]0:( [0-9a-f]{8}){4}$/

  @qemu @SYS-10 @VER-SYS-08 @VER-STK-05
  Scenario: SYS-10-S02: Call a function by address
    Given the address of "gpio_init" from "xtensa-esp32-elf-nm e32.elf"
    When I enter "g <that address>"
    Then the console shows "go <that address>"
    And the monitor prompt is shown

  @qemu @SYS-11 @SUB-MON-02 @VER-SYS-08 @VER-STK-05
  Scenario Outline: SUB-MON-02-S01: Malformed commands are rejected
    When I enter "<line>"
    Then the console shows "?? (h for help)"
    And the monitor prompt is shown

    Examples:
      | line          | why                       |
      | bogus         | unknown command           |
      | r             | missing address           |
      | w 3ffb1000    | missing value             |
      | r 3ffb000g    | not a hex number          |
      | r 3ffb0002    | unaligned address         |
      | w 3ffb0001 1  | unaligned address         |
      | d 3ffb0003    | unaligned address         |
      | p x           | not a decimal number      |
      | f             | missing argument          |

  @qemu @SYS-31 @SW-MON-06 @VER-SYS-08 @VER-STK-07
  Scenario: SW-MON-06-S01: Interrupt statistics
    When I wait 2 seconds
    And I enter "i"
    Then the console shows a line matching /^uptime \d+\.\d\d s \(\d+ ticks\)$/
    And the console shows a line matching /^irq  6: \d+$/
    And the console shows a line matching /^irq 17: \d+$/

  @qemu @SYS-10 @VER-SYS-08
  Scenario: SYS-10-S03: Empty lines just prompt again
    When I enter ""
    Then the monitor prompt is shown
    And the console does not show "??"
