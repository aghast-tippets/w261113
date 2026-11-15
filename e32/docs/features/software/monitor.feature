@EP-04 @FEAT-037
Feature: FEAT-037: Memory monitor
  Epic: EP-04 Interactive memory monitor (mimmo)   ·   Level: software

  Supports: US-12 via SYS-10 → SUB-MON-01 → SW-MON-01
  Supports: US-13 via SUB-MON-02 → SW-MON-01
  Supports: US-14 via SYS-10 → SUB-MON-01 → SW-MON-01
  Supports: US-19 via STK-08 → SYS-31 → SUB-MON-01 → SW-MON-01
  Supports: US-20 via STK-09 → SYS-31 → SUB-MON-01 → SW-MON-01
  Supports: US-21 via STK-08 → SYS-31 → SUB-MON-01 → SW-MON-01
  Supports: US-22 via STK-10 → SYS-30 → SUB-MON-01 → SW-MON-01
  Supports: US-23 via STK-10 → SYS-30 → SUB-MON-01 → SW-MON-01
  Supports: US-24 via SYS-21 → SUB-MON-01 → SW-MON-01
  Supports: US-26 via STK-14 → SYS-10 → SUB-MON-01 → SW-MON-01
  Supports: US-29 via STK-08 → SYS-31 → SUB-MON-01 → SW-MON-01

  Background:
    Given the firmware is booted in QEMU from flash
    And the monitor prompt is shown

  @SW-MON-01
  Rule: SW-MON-01: Number parsing
    EARS: The monitor shall parse addresses and values as hex with an optional `0x`/`0X` prefix, and GPIO and function numbers as decimal. Each number token must be followed by a blank or the end of the line.

  @SW-MON-02
  Rule: SW-MON-02: Output formats
    EARS: The monitor shall print results in these formats:
      - `read AAAAAAAA` followed by `VVVVVVVV` on the next line;
      - `write AAAAAAAA = VVVVVVVV`;
      - dump lines as `AAAAAAAA: w w w w`;
      - `gpio N <- v`, `gpio N = v` and `gpio N: function F`;
      - `go AAAAAAAA`.
      All addresses and values are 8 lower-case hex digits.

    @qemu @SYS-10 @VER-SYS-08 @VER-STK-05
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

  @SW-MON-03
  Rule: SW-MON-03: Dump default
    EARS: Where `d` is given no count, the monitor shall dump 16 words.

    @qemu @SYS-10 @VER-SYS-08
    Scenario: SW-MON-03-S01: Dump defaults to 16 words, 4 per line
      When I enter "d 3ffb0000"
      Then the console shows 4 lines matching /^3ffb00[0-3]0:( [0-9a-f]{8}){4}$/

  @SW-MON-06
  Rule: SW-MON-06: Statistics format
    EARS: When `i` is entered, the monitor shall print `uptime S.CC s (N ticks)`, then `irq NN: count` for every line with a non-zero count, in ascending order.

    @qemu @SYS-31 @VER-SYS-08 @VER-STK-07
    Scenario: SW-MON-06-S01: Interrupt statistics
      When I wait 2 seconds
      And I enter "i"
      Then the console shows a line matching /^uptime \d+\.\d\d s \(\d+ ticks\)$/
      And the console shows a line matching /^irq  6: \d+$/
      And the console shows a line matching /^irq 17: \d+$/
