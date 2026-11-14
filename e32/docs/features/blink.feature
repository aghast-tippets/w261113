@EP-05 @F-10
Feature: Blink mode
  As an operator without a serial connection
  I want a build that blinks the LED
  So that I can see the firmware is running

  Background:
    Given a build variant with "if (1)" changed to "if (0)" in main.c

  @qemu @SYS-22 @SW-MON-07 @CMP-32 @VER-SYS-18
  Scenario: The LED state alternates every half second
    When the firmware is booted in QEMU from flash
    And I wait 4 seconds
    Then the console shows at least 6 lines alternating "led 0" and "led 1"

  @hardware @pending @SYS-22 @HW-06 @SUB-TGT-02 @VER-SYS-18 @VER-STK-06
  Scenario: The LED blinks on a board
    When the blink build is flashed to a board with an LED on GPIO2
    And I watch for 10 seconds
    Then the LED changes state 18 to 22 times
