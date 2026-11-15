@EP-05 @FEAT-042
Feature: FEAT-042: GPIO control
  Epic: EP-05 GPIO control   ·   Level: software

  Supports: US-15 via STK-07 → SYS-14 → SUB-GPIO-02 → SW-GPIO-02
  Supports: US-16 via SW-GPIO-01

  @SW-GPIO-01
  Rule: SW-GPIO-01: Valid pins
    EARS: If a GPIO number is below 0, 40 or above, has no IO_MUX entry (24 and 28–31), or is in 6–11, then `gpio_valid` shall return false.

    @qemu @SYS-14 @SUB-GPIO-02 @SW-GPIO-02 @HW-07 @HW-08 @VER-SYS-10 @VER-STK-06
    Scenario Outline: SW-GPIO-01-S01: Refused pins
      Given the firmware is booted in QEMU from flash
      When I enter "<command>"
      Then the console shows "<message>"

      Examples:
        | command | message                                                 |
        | p 7 1   | invalid gpio (6..11 are flash, 34..39 are input only)   |
        | p 6     | invalid gpio (6..11 are flash, 34..39 are input only)   |
        | p 36 1  | invalid gpio (6..11 are flash, 34..39 are input only)   |
        | p 24    | invalid gpio (6..11 are flash, 34..39 are input only)   |
        | p 40    | invalid gpio (6..11 are flash, 34..39 are input only)   |
        | a 2 6   | invalid gpio or function                                |
        | a 9 0   | invalid gpio or function                                |

  @SW-GPIO-02
  Rule: SW-GPIO-02: Argument checks first
    EARS: If the pin is invalid, `afnum` is outside 0–5, or output is requested on GPIO 34 or above, then `gpio_dir_af` shall return −1 before writing any register.

  @SW-GPIO-03
  Rule: SW-GPIO-03: Function select
    EARS: When `gpio_dir_af` accepts a request, it shall:
      1. write the IO_MUX `MCU_SEL` field with the hardware function, with 0 and 2 swapped;
      2. set `FUN_IE`;
      3. for AF0 only, write `GPIO_PINn` = 0 and `GPIO_FUNCn_OUT_SEL` = `256 | OEN_SEL`, then call `gpio_dir`.

    @hardware @pending @SYS-12 @SUB-GPIO-01 @SW-GPIO-04 @VER-SYS-09 @VER-STK-06
    Scenario Outline: SW-GPIO-03-S01: Drive a GPIO output
      Given the firmware is running on a board
      When I enter "p <gpio> <level>"
      Then the console shows "gpio <gpio> <- <level>"
      And pin <gpio> measures <voltage>

      Examples:
        | gpio | level | voltage  |
        | 2    | 1     | ≥ 2.6 V  |
        | 2    | 0     | ≤ 0.3 V  |
        | 33   | 1     | ≥ 2.6 V  |
        | 33   | 0     | ≤ 0.3 V  |

    @hardware @pending @SW-GPIO-04 @VER-SW-12
    Scenario: SW-GPIO-03-S02: Registers after driving GPIO2 high
      Given the firmware is running on a board
      When I enter "p 2 1"
      And I enter "r 3ff49040"
      Then bits 14..12 of the value are 2 and bit 9 is 1
      When I enter "r 3ff44538"
      Then the value is 00000500
      When I enter "r 3ff44020"
      Then bit 2 of the value is 1

  @SW-GPIO-04
  Rule: SW-GPIO-04: Direction
    EARS: When `gpio_dir` is called for output, it shall first set the level through the `OUT(1)_W1TS` or `OUT(1)_W1TC` register, then set the enable bit through `ENABLE(1)_W1TS`. For input, it shall clear the enable bit through `ENABLE(1)_W1TC`.

  @SW-GPIO-05
  Rule: SW-GPIO-05: Level access
    EARS: `__gpio_get` shall return the pin's bit of `IN` or `IN1` (0 or the bit value), `gpio_get` shall return 0 or 1, and `__gpio_set`/`gpio_set` shall write the pin's bit to the W1TS register for non-zero values and to W1TC for zero.

    @hardware @pending @SYS-13 @VER-SYS-09
    Scenario Outline: SW-GPIO-05-S01: Read a GPIO input
      Given the firmware is running on a board
      And GPIO <gpio> is tied to <tie>
      When I enter "p <gpio>"
      Then the console shows "gpio <gpio> = <value>"

      Examples:
        | gpio | tie | value |
        | 4    | GND | 0     |
        | 4    | 3V3 | 1     |
        | 36   | GND | 0     |
        | 36   | 3V3 | 1     |
