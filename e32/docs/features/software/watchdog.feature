@EP-02 @FEAT-022
Feature: FEAT-022: Watchdog control
  Epic: EP-02 Boot and run on the ESP32   ·   Level: software

  Supports: US-07 via SYS-09 → SUB-BOOT-02 → SW-WDT-01

  @SW-WDT-01
  Rule: SW-WDT-01: Disable each watchdog
    EARS: For each of the RTC watchdog, the timer group 0 watchdog and the timer group 1 watchdog, `wdt_disable` shall:
      - write the key `0x50D83AA1` to the block's `WPROTECT` register;
      - write 0 to its `CONFIG0` register;
      - write 0 to `WPROTECT`.
