@EP-02 @FEAT-020
Feature: FEAT-020: Watchdog control
  Epic: EP-02 Boot and run on the ESP32   ·   Level: system

  User stories delivered:
    US-07  As an operator, I want the board to stay up indefinitely, so that my
           monitor session is not interrupted by watchdogs the ROM armed.

  Actors: Bench operator / tester (ACT-H3, persona "olga")

  # QEMU only arms the boot watchdog after a reset, not at power-on.
  # These scenarios therefore arm timer group 0's watchdog explicitly,
  # with the same key protocol, before startup continues.

  @SYS-09 @US-07
  Rule: SYS-09: No watchdog resets
    EARS: While the e32 firmware is running, the system shall not be reset by the RTC watchdog or by either timer-group watchdog.

    @qemu @VER-SYS-07
    Scenario: SYS-09-S01: Negative control: without wdt_disable the chip keeps resetting
      Given a build variant that arms the TG0 watchdog and does not call "wdt_disable"
      When the firmware is booted in QEMU from flash
      And I wait 6 seconds
      Then the chip resets 6 times within 6 seconds

    @hardware @pending @VER-SYS-07 @VER-STK-10
    Scenario: SYS-09-S02: A board stays up
      Given the firmware is running on a board after a flash boot
      When I wait 600 seconds
      Then the console does not show "rst:"
