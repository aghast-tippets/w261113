@EP-05 @F-09
Feature: gpio.c, lib.c and pp_printf.c unit behaviour
  Unit level (CMP). The sources are compiled for the host and run against
  a mocked register bus; the GoogleTest suite implements these scenarios.

  @host @CMP-21 @VER-CMP-12
  Scenario Outline: CMP-21-S02: Every usable pad maps to its IO_MUX register
    When the firmware calls gpio_dir_af with gpio <gpio>, input, alternate function 0
    Then IO_MUX register <mux> is written with function 2 and input enabled

    Examples:
      | gpio | mux      |
      | 0    | 3ff49044 |
      | 2    | 3ff49040 |
      | 4    | 3ff49048 |
      | 12   | 3ff49034 |
      | 23   | 3ff4908c |
      | 25   | 3ff49024 |
      | 33   | 3ff49020 |
      | 36   | 3ff49004 |
      | 39   | 3ff49010 |

  @host @CMP-21 @CMP-22 @VER-CMP-12
  Scenario Outline: CMP-21-S03: Invalid pins and functions are refused without touching a register
    When the firmware calls gpio_dir_af with gpio <gpio>, <direction>, alternate function <af>
    Then it returns -1
    And no register was written

    Examples:
      | gpio | direction | af |
      | -1   | input     | 0  |
      | 6    | input     | 0  |
      | 11   | output    | 0  |
      | 24   | input     | 0  |
      | 28   | input     | 0  |
      | 40   | input     | 0  |
      | 34   | output    | 0  |
      | 2    | input     | 6  |
      | 2    | input     | -1 |

  @host @CMP-21 @CMP-22 @VER-CMP-12
  Scenario Outline: CMP-21-S04: Alternate functions 0 and 2 are swapped
    Given IO_MUX register 3ff49040 holds 00002b00
    When the firmware calls gpio_dir_af with gpio 2, input, alternate function <af>
    Then IO_MUX register 3ff49040 is written with <value>

    Examples:
      | af | value    |
      | 0  | 00002b00 |
      | 2  | 00000b00 |
      | 3  | 00003b00 |

  @host @CMP-22 @VER-CMP-12
  Scenario: CMP-22-S01: An input pin on the upper port is released from output
    When the firmware calls gpio_dir_af with gpio 35, input, alternate function 0
    Then 00000008 is written to GPIO_ENABLE1_W1TC at 3ff44034

  @host @CMP-23 @VER-CMP-12
  Scenario Outline: CMP-23-S01: Levels are set, cleared and read on both ports
    Given GPIO_IN reads 00000010 and GPIO_IN1 reads 00000002
    When the firmware sets gpio <gpio> to <value>
    Then <bit> is written to <register>
    And gpio_get(<gpio>) reads <level>

    Examples:
      | gpio | value | bit      | register | level |
      | 4    | 1     | 00000010 | 3ff44008 | 1     |
      | 4    | 0     | 00000010 | 3ff4400c | 1     |
      | 5    | 1     | 00000020 | 3ff44008 | 0     |
      | 33   | 1     | 00000002 | 3ff44014 | 1     |
      | 33   | 0     | 00000002 | 3ff44018 | 1     |

  @host @CMP-31 @VER-CMP-15
  Scenario: CMP-31-S02: udelay waits at least 40 cycles per microsecond
    Given CCOUNT advances by 7 cycles on every read and starts at fffffff0
    When the firmware calls udelay with 25
    Then CCOUNT has advanced by at least 1000 cycles and less than 1014

  @host @CMP-20 @VER-CMP-11
  Scenario: CMP-20-S01: pp_printf sends its output through putc and returns its length
    When the firmware calls pp_printf with "x=%d\n" and 42
    Then it returns 5
    And the UART transmits the bytes "x=42" 0d 0a
