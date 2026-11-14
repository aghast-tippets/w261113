@EP-05 @F-09
Feature: GPIO control
  As an operator
  I want to drive and read pins and pick pin functions
  So that I can exercise the board's wiring safely

  @hardware @pending @SYS-12 @SUB-GPIO-01 @SW-GPIO-03 @SW-GPIO-04 @VER-SYS-09 @VER-STK-06
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

  @hardware @pending @SYS-13 @SW-GPIO-05 @VER-SYS-09
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

  @hardware @pending @SW-GPIO-03 @SW-GPIO-04 @VER-SW-12
  Scenario: SW-GPIO-03-S02: Registers after driving GPIO2 high
    Given the firmware is running on a board
    When I enter "p 2 1"
    And I enter "r 3ff49040"
    Then bits 14..12 of the value are 2 and bit 9 is 1
    When I enter "r 3ff44538"
    Then the value is 00000500
    When I enter "r 3ff44020"
    Then bit 2 of the value is 1

  @qemu @SYS-12 @SYS-13 @SUB-GPIO-01 @VER-SYS-09
  Scenario: SUB-GPIO-01-S01: GPIO command paths in the emulator
    Given the firmware is booted in QEMU from flash
    When I enter "p 2 1"
    Then the console shows "gpio 2 <- 1"
    When I enter "p 34"
    Then the console shows a line matching /^gpio 34 = [01]$/
    When I enter "a 2 3"
    Then the console shows "gpio 2: function 3"

  @qemu @SYS-14 @SUB-GPIO-02 @SW-GPIO-01 @SW-GPIO-02 @HW-07 @HW-08 @VER-SYS-10 @VER-STK-06
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

  @host @pending @CMP-21 @CMP-22 @CMP-23 @VER-CMP-12
  Scenario: CMP-21-S01: GPIO unit test against a fake register file
    Given gpio.c compiled for the host with readl and writel recording into an array
    When I call gpio_dir_af(7, 1, 1, 0)
    Then it returns -1
    And no register was written
    When I call gpio_dir_af(2, 1, 1, 0)
    Then it returns 0
    And the writes are, in order: IO_MUX 0x3ff49040 (MCU_SEL 2, FUN_IE), GPIO_PIN2 = 0, FUNC2_OUT_SEL = 0x500, OUT_W1TS = 0x4, ENABLE_W1TS = 0x4
