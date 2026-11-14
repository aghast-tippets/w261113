@EP-06 @F-13
Feature: Timekeeping
  As an integrator
  I want a 100 Hz tick and microsecond delays
  So that I can measure and wait for time

  @qemu @SYS-17 @SUB-TIME-01 @SUB-TIME-03 @SW-TIME-01 @SW-TIME-03 @CMP-31 @VER-SYS-13
  Scenario: CMP-31-S01: About ten ticks per 100 ms delay
    Given the firmware is booted in QEMU from flash
    When I enter "s"
    Then the console shows a line matching /^ticks in 100ms:    (9|10|11) \(ok\)$/

  @qemu @SYS-17 @SUB-TIME-02 @SW-TIME-02 @CMP-13 @VER-SYS-13
  Scenario: CMP-13-S01: The tick never stalls under load (regression)
    # Before the fix, a compare value written behind CCOUNT stopped
    # the tick for 2^32 cycles; at 20 kHz in QEMU it stalled after 2860 ticks.
    Given a build variant with timer_init(20000)
    When the firmware is booted in QEMU from flash
    And I enter "i" at 3 s and again at 13 s
    Then the second tick count exceeds the first by at least 100000

  @hardware @pending @SYS-17 @HW-02 @VER-SYS-13
  Scenario: HW-02-S01: Uptime follows wall-clock time on a board
    Given the firmware is running on a board
    When I enter "i" and start a stopwatch
    And I enter "i" again after 60 stopwatch seconds
    Then the uptime difference is between 59.4 and 60.6 seconds
