@EP-05 @FEAT-044
Feature: FEAT-044: GPIO control
  Epic: EP-05 GPIO control   ·   Level: unit

  Supports: US-15 via SW-GPIO-03 → CMP-21
  Supports: US-16 via SW-GPIO-01 → CMP-21

  @CMP-21
  Rule: CMP-21: gpio.c: pad table and validity
    EARS: `gpio_mux[40]` shall hold `(IO_MUX address − 0x3FF49000)/4` for each existing pad, and 0 for 24 and 28–31. `gpio_valid(n)` shall return 1 only for 0 ≤ n < 40, with a non-zero entry and n ∉ [6, 11]. `af_to_hw` shall map 0→2, 2→0, and any other value to itself.

    @host @pending @CMP-22 @CMP-23 @VER-CMP-12
    Scenario: CMP-21-S01: GPIO unit test against a fake register file
      Given gpio.c compiled for the host with readl and writel recording into an array
      When I call gpio_dir_af(7, 1, 1, 0)
      Then it returns -1
      And no register was written
      When I call gpio_dir_af(2, 1, 1, 0)
      Then it returns 0
      And the writes are, in order: IO_MUX 0x3ff49040 (MCU_SEL 2, FUN_IE), GPIO_PIN2 = 0, FUNC2_OUT_SEL = 0x500, OUT_W1TS = 0x4, ENABLE_W1TS = 0x4

    @host @gtest @VER-CMP-12
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

    @host @gtest @CMP-22 @VER-CMP-12
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

    @host @gtest @CMP-22 @VER-CMP-12
    Scenario Outline: CMP-21-S04: Alternate functions 0 and 2 are swapped
      Given IO_MUX register 3ff49040 holds 00002b00
      When the firmware calls gpio_dir_af with gpio 2, input, alternate function <af>
      Then IO_MUX register 3ff49040 is written with <value>

      Examples:
        | af | value    |
        | 0  | 00002b00 |
        | 2  | 00000b00 |
        | 3  | 00003b00 |

  @CMP-22
  Rule: CMP-22: gpio.c: gpio_dir_af, gpio_dir
    EARS: If the arguments fail SW-GPIO-02, then `gpio_dir_af` shall return −1 with no register written. Otherwise it shall perform SW-GPIO-03 and return 0, or return the result of `gpio_dir` for AF0. `gpio_dir` shall perform SW-GPIO-04 and return 0.

    @host @gtest @VER-CMP-12
    Scenario: CMP-22-S01: An input pin on the upper port is released from output
      When the firmware calls gpio_dir_af with gpio 35, input, alternate function 0
      Then 00000008 is written to GPIO_ENABLE1_W1TC at 3ff44034

  @CMP-23
  Rule: CMP-23: gpio.c and gpio.h: level access
    EARS: `__gpio_get(n)` shall return `IN[port] & (1<<bit)`. `__gpio_set(n, v)` shall write `1<<bit` to `OUT_W1TS[port]` if `v` ≠ 0, or to `OUT_W1TC[port]` otherwise. The inline `gpio_get` and `gpio_set` shall wrap them.

    @host @gtest @VER-CMP-12
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
