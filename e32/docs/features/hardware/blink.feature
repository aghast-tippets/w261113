@EP-05 @FEAT-046
Feature: FEAT-046: Blink mode
  Epic: EP-05 GPIO control   ·   Level: hardware

  Supports: US-17 via HW-06

  Background:
    Given a build variant with "if (1)" changed to "if (0)" in main.c

  @HW-06
  Rule: HW-06: Indicator LED
    EARS: Where blink mode is used, an LED shall be connected to `LED_GPIO` (GPIO2 by default) such that it is visibly lit at one level and off at the other.

    @hardware @pending @SYS-22 @SUB-TGT-02 @VER-SYS-18 @VER-STK-06
    Scenario: HW-06-S01: The LED blinks on a board
      When the blink build is flashed to a board with an LED on GPIO2
      And I watch for 10 seconds
      Then the LED changes state 18 to 22 times
