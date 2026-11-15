@EP-06 @FEAT-061
Feature: FEAT-061: Timekeeping
  Epic: EP-06 Exception and interrupt handling   ·   Level: subsystem

  Supports: US-17 via STK-16 → SYS-22 → SUB-TIME-03
  Supports: US-20 via STK-09 → SYS-17 → SUB-TIME-01
  Supports: US-24 via SYS-21 → SUB-TIME-03
  Supports: US-29 via STK-09 → SYS-17 → SUB-TIME-01

  @SUB-TIME-01
  Rule: SUB-TIME-01: Periodic tick
    EARS: The timekeeping subsystem shall raise a level-1 interrupt from `CCOMPARE0` at a requested rate and count the ticks in `jiffies`.

  @SUB-TIME-02
  Rule: SUB-TIME-02: Missed-compare recovery
    EARS: If, after a new compare value is written, `CCOUNT` has already reached it, then the timekeeping subsystem shall advance the value by whole periods, counting each one, until the value is ahead of `CCOUNT`.

  @SUB-TIME-03
  Rule: SUB-TIME-03: Busy-wait delay
    EARS: The timekeeping subsystem shall provide a microsecond busy-wait delay based on `CCOUNT` and `CPU_HZ`.
