@EP-02 @FEAT-024
Feature: FEAT-024: Watchdog control
  Epic: EP-02 Boot and run on the ESP32   ·   Level: unit

  Supports: US-07 via CMP-14

  # QEMU only arms the boot watchdog after a reset, not at power-on.
  # These scenarios therefore arm timer group 0's watchdog explicitly,
  # with the same key protocol, before startup continues.

  @CMP-14
  Rule: CMP-14: wdt.c
    EARS: When `wdt_disable()` is called, it shall perform the sequence `writel(KEY, WPROTECT)`, `writel(0, CONFIG0)`, `writel(0, WPROTECT)` for RTC (`0xA4`/`0x8C`), TIMG0 and TIMG1 (`0x64`/`0x48`), in that order.

    @qemu @SYS-09 @SUB-BOOT-02 @SW-WDT-01 @IF-14 @VER-SYS-07
    Scenario: CMP-14-S01: An armed watchdog is disabled at startup
      Given a build variant that arms the TG0 watchdog (stage 0 = reset, 26,000,000 APB cycles) before "wdt_disable"
      When the firmware is booted in QEMU from flash
      And I wait 6 seconds
      Then the chip resets 1 times within 6 seconds

    @host @gtest @VER-CMP-09
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
