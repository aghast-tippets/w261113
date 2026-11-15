@EP-02 @FEAT-021
Feature: FEAT-021: Watchdog control
  Epic: EP-02 Boot and run on the ESP32   ·   Level: subsystem

  Supports: US-07 via SYS-09 → SUB-BOOT-02

  @SUB-BOOT-02
  Rule: SUB-BOOT-02: Watchdogs off
    EARS: When startup runs, the boot subsystem shall disable the RTC watchdog and the watchdogs of timer groups 0 and 1 before `main` is called.
