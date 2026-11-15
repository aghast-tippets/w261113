@EP-08 @FEAT-073
Feature: FEAT-073: Self test
  Epic: EP-08 Verification and emulation   ·   Level: software

  Supports: US-12 via SYS-10 → SUB-MON-01 → SW-MON-04
  Supports: US-14 via SYS-10 → SUB-MON-01 → SW-MON-04
  Supports: US-19 via STK-08 → SYS-31 → SUB-MON-01 → SW-MON-04
  Supports: US-20 via STK-09 → SYS-31 → SUB-MON-01 → SW-MON-04
  Supports: US-21 via STK-08 → SYS-31 → SUB-MON-01 → SW-MON-04
  Supports: US-22 via STK-10 → SYS-30 → SUB-MON-01 → SW-MON-04
  Supports: US-23 via STK-10 → SYS-30 → SUB-MON-01 → SW-MON-04
  Supports: US-24 via SYS-21 → SUB-MON-01 → SW-MON-04
  Supports: US-26 via STK-14 → SYS-10 → SUB-MON-01 → SW-MON-04
  Supports: US-29 via STK-08 → SYS-31 → SUB-MON-01 → SW-MON-04

  @SW-MON-04
  Rule: SW-MON-04: Self-test checks
    EARS: When `s` is entered, the monitor shall check that:
      - `recurse(200)` returns 20100;
      - `vla_after_spill(100)` returns 919;
      - one software interrupt on line 7 causes exactly one handler call;
      - the ticks counted during `udelay(100000)` are within `HZ/10 ± 1`.
      It shall print a line per check and `all ok` or `FAILED`.
