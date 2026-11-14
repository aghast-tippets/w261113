@EP-02 @F-05
Feature: Watchdog control
  As an operator
  I want the watchdogs the ROM armed to be stopped at startup
  So that the board never resets on its own

  # QEMU only arms the boot watchdog after a reset, not at power-on.
  # These scenarios therefore arm timer group 0's watchdog explicitly,
  # with the same key protocol, before startup continues.

  @qemu @SYS-09 @SUB-BOOT-02 @SW-WDT-01 @IF-14 @CMP-14 @VER-SYS-07
  Scenario: An armed watchdog is disabled at startup
    Given a build variant that arms the TG0 watchdog (stage 0 = reset, 26,000,000 APB cycles) before "wdt_disable"
    When the firmware is booted in QEMU from flash
    And I wait 6 seconds
    Then the chip resets 1 times within 6 seconds

  @qemu @SYS-09 @VER-SYS-07
  Scenario: Negative control: without wdt_disable the chip keeps resetting
    Given a build variant that arms the TG0 watchdog and does not call "wdt_disable"
    When the firmware is booted in QEMU from flash
    And I wait 6 seconds
    Then the chip resets 6 times within 6 seconds

  @hardware @pending @SYS-09 @VER-SYS-07 @VER-STK-10
  Scenario: A board stays up
    Given the firmware is running on a board after a flash boot
    When I wait 600 seconds
    Then the console does not show "rst:"
