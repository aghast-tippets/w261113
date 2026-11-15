@EP-06 @FEAT-064
Feature: FEAT-064: Timekeeping
  Epic: EP-06 Exception and interrupt handling   ·   Level: unit

  Supports: US-20 via CMP-13

  @CMP-13
  Rule: CMP-13: timer.c
    EARS: When `timer_init(hz)` is called, it shall set `tick_cycles` = `CPU_HZ/hz` and `CCOMPARE0` = `CCOUNT + tick_cycles`, and request line 6. When `timer_tick` runs, it shall execute the SW-TIME-02 loop. Postcondition: `(s32)(CCOMPARE0 − CCOUNT) > 0` at the moment of the final check.

    @qemu @SYS-17 @SUB-TIME-02 @SW-TIME-02 @VER-SYS-13
    Scenario: CMP-13-S01: The tick never stalls under load (regression)
      # Before the fix, a compare value written behind CCOUNT stopped
      # the tick for 2^32 cycles; at 20 kHz in QEMU it stalled after 2860 ticks.
      Given a build variant with timer_init(20000)
      When the firmware is booted in QEMU from flash
      And I enter "i" at 3 s and again at 13 s
      Then the second tick count exceeds the first by at least 100000

    @host @gtest @VER-CMP-08
    Scenario: CMP-13-S02: timer_init programs the first compare one period ahead
      Given CCOUNT is 1000
      When the firmware calls timer_init with 100
      Then CCOMPARE0 is 401000 plus the cycles that elapsed while reading CCOUNT
      And CPU line 6 is enabled

    @host @gtest @VER-CMP-08
    Scenario: CMP-13-S03: The tick catches up when CCOUNT has passed the next compare value
      Given timer_init was called with 100 and jiffies is 0
      And CCOUNT has advanced 3 periods and 10 cycles past the last compare value
      When the CPU takes the timer interrupt
      Then jiffies is 4
      And CCOMPARE0 is ahead of CCOUNT

    @host @gtest @CMP-31 @VER-CMP-08 @VER-CMP-15
    Scenario: CMP-13-S04: About ten ticks elapse during a 100 ms delay
      Given timer_init was called with 100 and jiffies is 0
      When the firmware calls udelay with 100000
      Then jiffies is between 9 and 11

  @CMP-31
  Rule: CMP-31: lib.c: udelay
    EARS: `udelay(us)` shall return once `get_ccount() − start` ≥ `us · (CPU_HZ/1000000)`, computed in `u32` arithmetic. Precondition: `us · 40` < 2³².

    @qemu @SYS-17 @SUB-TIME-01 @SUB-TIME-03 @SW-TIME-01 @SW-TIME-03 @VER-SYS-13
    Scenario: CMP-31-S01: About ten ticks per 100 ms delay
      Given the firmware is booted in QEMU from flash
      When I enter "s"
      Then the console shows a line matching /^ticks in 100ms:    (9|10|11) \(ok\)$/

    @host @gtest @VER-CMP-15
    Scenario: CMP-31-S02: udelay waits at least 40 cycles per microsecond
      Given CCOUNT advances by 7 cycles on every read and starts at fffffff0
      When the firmware calls udelay with 25
      Then CCOUNT has advanced by at least 1000 cycles and less than 1014
