@EP-04 @FEAT-038
Feature: FEAT-038: Memory monitor
  Epic: EP-04 Interactive memory monitor (mimmo)   ·   Level: unit

  Supports: US-12 via CMP-24
  Supports: US-14 via SYS-10 → SUB-MON-01 → SW-MON-02 → CMP-25
  Supports: US-19 via STK-08 → SYS-31 → SUB-MON-01 → SW-MON-02 → CMP-25
  Supports: US-20 via STK-09 → SYS-31 → SUB-MON-01 → SW-MON-02 → CMP-25
  Supports: US-21 via STK-08 → SYS-31 → SUB-MON-01 → SW-MON-02 → CMP-25
  Supports: US-22 via STK-10 → SYS-30 → SUB-MON-01 → SW-MON-02 → CMP-25
  Supports: US-23 via STK-10 → SYS-30 → SUB-MON-01 → SW-MON-02 → CMP-25
  Supports: US-24 via SYS-21 → SUB-MON-01 → SW-MON-02 → CMP-25
  Supports: US-26 via STK-14 → SYS-10 → SUB-MON-01 → SW-MON-02 → CMP-25
  Supports: US-29 via SW-MON-06 → CMP-25

  @CMP-24
  Rule: CMP-24: mimmo.c: get_num
    EARS: `get_num(&s, base, &v)` shall skip blanks and accept an optional `0x` prefix only in base 16. It shall accumulate the digits valid in `base`, and fail with −1, leaving `s` and `v` untouched, on: no digits; a digit not valid in `base`; or a following character that is not a blank or NUL. On success it shall advance `s` and return 0.

    @qemu @SYS-10 @SW-MON-01 @SW-MON-02 @CMP-25 @VER-SYS-08 @VER-STK-05
    Scenario: CMP-24-S01: Write then read a word of RAM
      Given the firmware is booted in QEMU from flash
      And the monitor prompt is shown
      When I enter "w 3ffb1000 cafe"
      Then the console shows "write 3ffb1000 = 0000cafe"
      When I enter "r 0x3ffb1000"
      Then the console shows "read 3ffb1000"
      And the console shows "0000cafe"

    @host @gtest @VER-CMP-13
    Scenario Outline: CMP-24-S02: Numbers are parsed strictly
      Given memory word 3ffb1000 holds 0000cafe
      When the operator enters "<line>"
      Then the console shows "<reply>"

      Examples:
        | line            | reply         |
        | r 3ffb1000      | read 3ffb1000 |
        | r 0x3ffb1000    | read 3ffb1000 |
        | r 0X3FFB1000    | read 3ffb1000 |
        | r   3ffb1000    | read 3ffb1000 |
        | r 3ffb100g      | ?? (h for help) |
        | r 0x            | ?? (h for help) |
        | r 3ffb1000x     | ?? (h for help) |
        | p 1a            | ?? (h for help) |
        | p 0x2           | ?? (h for help) |

  @CMP-25
  Rule: CMP-25: mimmo.c: command loop
    EARS: When a line is read, `mimmo()` shall dispatch on its first non-blank character, produce the SW-MON-02, SW-MON-03 and SW-MON-06 outputs, print `?? (h for help)` for any error, and print `> ` before each read. It never returns.

    @host @gtest @VER-CMP-13
    Scenario: CMP-25-S01: Read, write and dump answer in their documented formats
      Given memory words 3ffb2000 to 3ffb201c hold 00000000 to 00000007
      When the operator enters "w 3ffb2000 cafe", "r 3ffb2000" and "d 3ffb2000 8"
      Then the console shows exactly:
        """
        write 3ffb2000 = 0000cafe
        read 3ffb2000
        0000cafe
        3ffb2000: 0000cafe 00000001 00000002 00000003
        3ffb2010: 00000004 00000005 00000006 00000007
        """

    @host @gtest @VER-CMP-13
    Scenario Outline: CMP-25-S02: GPIO commands report their outcome
      Given GPIO_IN reads 00000010
      When the operator enters "<line>"
      Then the console shows "<reply>"

      Examples:
        | line   | reply                                                 |
        | p 2 1  | gpio 2 <- 1                                           |
        | p 2 5  | gpio 2 <- 1                                           |
        | p 4    | gpio 4 = 1                                            |
        | p 5    | gpio 5 = 0                                            |
        | p 7 1  | invalid gpio (6..11 are flash, 34..39 are input only) |
        | a 2 3  | gpio 2: function 3                                    |
        | a 2 6  | invalid gpio or function                              |

    @host @gtest @VER-CMP-13
    Scenario: CMP-25-S03: The prompt is printed before every read and blank lines are ignored
      When the operator enters "", "   " and "h"
      Then the console shows the prompt "> " 4 times
      And the console does not show "??"
      And the console shows "h                     this help"
