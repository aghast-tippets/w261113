@EP-04 @FEAT-036
Feature: FEAT-036: Memory monitor
  Epic: EP-04 Interactive memory monitor (mimmo)   ·   Level: subsystem

  Supports: US-09 via STK-05 → SYS-06 → SUB-MON-03
  Supports: US-10 via STK-19 → SYS-18 → SUB-MON-03
  Supports: US-11 via STK-05 → SYS-06 → SUB-MON-03
  Supports: US-12 via SYS-10 → SUB-MON-01
  Supports: US-13 via SUB-MON-02
  Supports: US-14 via SYS-10 → SUB-MON-01
  Supports: US-17 via STK-16 → SYS-22 → SUB-MON-03
  Supports: US-19 via STK-08 → SYS-31 → SUB-MON-01
  Supports: US-20 via STK-09 → SYS-31 → SUB-MON-01
  Supports: US-21 via STK-08 → SYS-31 → SUB-MON-01
  Supports: US-22 via STK-10 → SYS-30 → SUB-MON-01
  Supports: US-23 via STK-10 → SYS-30 → SUB-MON-01
  Supports: US-24 via SYS-21 → SUB-MON-01
  Supports: US-26 via STK-14 → SYS-10 → SUB-MON-01
  Supports: US-29 via STK-08 → SYS-31 → SUB-MON-01

  Background:
    Given the firmware is booted in QEMU from flash
    And the monitor prompt is shown

  @SUB-MON-01
  Rule: SUB-MON-01: Command set
    EARS: When a command line is read, the monitor subsystem shall execute `r`, `w`, `d`, `p`, `a`, `g`, `i`, `s`, `f`, `h` or `?`. Addresses and values are taken in hex, and GPIO and function numbers in decimal.

  @SUB-MON-02
  Rule: SUB-MON-02: Input validation
    EARS: If a command is unknown, has a missing or invalid argument, or has an unaligned address (`r`, `w`, `d`), then the monitor subsystem shall print `?? (h for help)` without accessing memory.

    @qemu @SYS-11 @VER-SYS-08 @VER-STK-05
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

  @SUB-MON-03
  Rule: SUB-MON-03: Start-up sequence
    EARS: When `main` runs, the monitor subsystem shall:
      - print the banner;
      - initialise interrupts, the `HZ` tick and console receive interrupts;
      - then enter the command loop, or the blink loop when blink mode is selected.
