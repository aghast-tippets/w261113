@EP-06 @FEAT-063
Feature: FEAT-063: Timekeeping
  Epic: EP-06 Exception and interrupt handling   ·   Level: software

  Supports: US-17 via STK-16 → SYS-22 → SUB-TIME-03 → SW-TIME-03
  Supports: US-20 via STK-09 → SYS-17 → SUB-TIME-01 → SW-TIME-01
  Supports: US-24 via SYS-21 → SUB-TIME-03 → SW-TIME-03
  Supports: US-29 via STK-09 → SYS-17 → SUB-TIME-01 → SW-TIME-01

  @SW-TIME-01
  Rule: SW-TIME-01: timer_init
    EARS: When `timer_init(hz)` is called, it shall set the period to `CPU_HZ / hz` cycles, set `CCOMPARE0` to `CCOUNT` plus one period, and register the tick handler on line 6.

  @SW-TIME-02
  Rule: SW-TIME-02: Tick handler
    EARS: When the tick interrupt runs, the handler shall repeat the following until `(s32)(next − CCOUNT) > 0`, starting from `next` = `CCOMPARE0`:
      1. add one period to `next`;
      2. increment `jiffies`;
      3. write `next` to `CCOMPARE0`.

  @SW-TIME-03
  Rule: SW-TIME-03: udelay
    EARS: `udelay(us)` shall busy-wait until `CCOUNT` has advanced by `us × (CPU_HZ / 1000000)` cycles, with unsigned arithmetic that stays correct across a `CCOUNT` wrap.

  @SW-TIME-04
  Rule: SW-TIME-04: Constants
    EARS: The software shall define `HZ` = 100 and `CPU_HZ` = 40000000 by default, with `CPU_HZ` overridable at compile time.
