@EP-05 @FEAT-049
Feature: FEAT-049: Stakeholder acceptance: GPIO control
  Epic: EP-05 GPIO control   ·   Level: acceptance

  User stories delivered:
    US-15  As an operator, I want to set a pin high or low and read a pin from
           the monitor, so that I can test the board's wiring.
    US-16  As an operator, I want the firmware to refuse the flash pins and
           output on input-only pins, so that I can't brick the session or the
           board.

  Actors: Bench operator / tester (ACT-H3, persona "olga")

  @STK-07 @US-15 @US-16
  Rule: STK-07: Drive and read pins safely
    EARS: The operator needs to drive and read GPIO pins and select pin functions from the console, without being able to disturb the flash pins or drive input-only pins.

    @hardware @pending @STK-16 @VER-STK-06
    Scenario: STK-07-S01: Operator drives pins and sees a blink
      When the operator enters "p 2 1" and "p 2 0"
      Then the LED on GPIO2 follows
      When the operator enters "p 7 1"
      Then the command is refused
      When the blink build is flashed
      Then the LED blinks at about 1 Hz
