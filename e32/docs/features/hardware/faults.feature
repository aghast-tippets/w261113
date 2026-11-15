@EP-07 @FEAT-068
Feature: FEAT-068: Faults and recovery
  Epic: EP-07 Fault reporting and recovery   ·   Level: hardware

  Supports: US-22 via STK-10 → SYS-20 → SUB-FLT-03 → HW-12
  Supports: US-23 via STK-10 → SYS-20 → SUB-FLT-03 → HW-12
  Supports: US-26 via STK-10 → SYS-20 → SUB-FLT-03 → HW-12

  @HW-12
  Rule: HW-12: Software system reset
    EARS: When bit 31 (`SW_SYS_RST`) of `RTC_CNTL_OPTIONS0` is written as 1, the chip shall perform a full system reset and boot through the ROM, which reports `rst:0x3 (SW_RESET)`.
