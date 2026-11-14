@EP-06 @F-12
Feature: irq.c, timer.c and wdt.c unit behaviour
  Unit level (CMP). The sources are compiled for the host and run against
  a simulated CPU (special registers, PS.INTLEVEL, CCOUNT) and a mocked
  register bus; the GoogleTest suite implements these scenarios.

  @host @CMP-10 @VER-CMP-07
  Scenario: CMP-10-S02: irq_init disconnects every interrupt matrix source
    Given interrupt matrix source 34 is routed to line 17 and INTENABLE is 00020040
    When the firmware calls irq_init
    Then all 69 sources from 3ff00104 to 3ff00214 are routed to line 6
    And INTENABLE is 00000000
    And INTCLEAR was written with ffffffff

  @host @CMP-10 @VER-CMP-07
  Scenario: CMP-10-S03: irq_map writes one matrix register
    When the firmware calls irq_map with source 34 and line 17
    Then 00000011 is written to 3ff0018c and nothing else is written

  @host @CMP-11 @VER-CMP-07
  Scenario Outline: CMP-11-S02: Only level-1 lines can be requested
    Given INTENABLE is 00000000
    When the firmware calls irq_request with line <line>
    Then it returns <result>
    And INTENABLE is <intenable>

    Examples:
      | line | result | intenable |
      | 0    | 0      | 00000001  |
      | 13   | 0      | 00002000  |
      | 17   | 0      | 00020000  |
      | 11   | -1     | 00000000  |
      | 19   | -1     | 00000000  |
      | 29   | -1     | 00000000  |
      | 32   | -1     | 00000000  |
      | -1   | -1     | 00000000  |

  @host @CMP-12 @VER-CMP-07
  Scenario: CMP-12-S02: Pending handlers run lowest line first and latched lines are cleared
    Given handlers are installed on lines 7 and 17
    And lines 7 and 17 are both pending
    When the CPU takes a level-1 interrupt
    Then the handler for line 7 runs before the handler for line 17
    And INTCLEAR was written with 00000080 and never with 00020000
    And irq_count reports one more interrupt on each line

  @host @CMP-12 @VER-CMP-07
  Scenario: CMP-12-S03: A pending line without a handler is disabled
    Given line 9 is enabled without a handler and pending
    When the CPU takes a level-1 interrupt
    Then the console shows "irq 9: no handler, disabled"
    And INTENABLE bit 9 is 0

  @host @CMP-13 @VER-CMP-08
  Scenario: CMP-13-S02: timer_init programs the first compare one period ahead
    Given CCOUNT is 1000
    When the firmware calls timer_init with 100
    Then CCOMPARE0 is 401000 plus the cycles that elapsed while reading CCOUNT
    And CPU line 6 is enabled

  @host @CMP-13 @VER-CMP-08
  Scenario: CMP-13-S03: The tick catches up when CCOUNT has passed the next compare value
    Given timer_init was called with 100 and jiffies is 0
    And CCOUNT has advanced 3 periods and 10 cycles past the last compare value
    When the CPU takes the timer interrupt
    Then jiffies is 4
    And CCOMPARE0 is ahead of CCOUNT

  @host @CMP-13 @CMP-31 @VER-CMP-08 @VER-CMP-15
  Scenario: CMP-13-S04: About ten ticks elapse during a 100 ms delay
    Given timer_init was called with 100 and jiffies is 0
    When the firmware calls udelay with 100000
    Then jiffies is between 9 and 11

  @host @CMP-14 @VER-CMP-09
  Scenario: CMP-14-S02: wdt_disable stops the three watchdogs
    When the firmware calls wdt_disable
    Then the register writes are, in order:
      | value    | address  | meaning               |
      | 50d83aa1 | 3ff480a4 | unlock RTC watchdog   |
      | 00000000 | 3ff4808c | RTC watchdog off      |
      | 00000000 | 3ff480a4 | lock RTC watchdog     |
      | 50d83aa1 | 3ff5f064 | unlock TIMG0 watchdog |
      | 00000000 | 3ff5f048 | TIMG0 watchdog off    |
      | 00000000 | 3ff5f064 | lock TIMG0 watchdog   |
      | 50d83aa1 | 3ff60064 | unlock TIMG1 watchdog |
      | 00000000 | 3ff60048 | TIMG1 watchdog off    |
      | 00000000 | 3ff60064 | lock TIMG1 watchdog   |
