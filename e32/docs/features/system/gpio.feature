@EP-05 @FEAT-040
Feature: FEAT-040: GPIO control
  Epic: EP-05 GPIO control   ·   Level: system

  User stories delivered:
    US-15  As an operator, I want to set a pin high or low and read a pin from
           the monitor, so that I can test the board's wiring.
    US-16  As an operator, I want the firmware to refuse the flash pins and
           output on input-only pins, so that I can't brick the session or the
           board.

  Actors: Bench operator / tester (ACT-H3, persona "olga")

  @SYS-12
  Rule: SYS-12: Drive a GPIO output
    EARS: When the operator requests a level on a GPIO that exists and is output-capable, the e32 firmware shall configure the pin as a push-pull GPIO output and drive the requested level.

  @SYS-13
  Rule: SYS-13: Read a GPIO input
    EARS: When the operator requests a reading of a GPIO that exists, the e32 firmware shall configure the pin as a GPIO input and print its level as 0 or 1.

  @SYS-14
  Rule: SYS-14: Refuse dangerous pins
    EARS: If a GPIO request names a pin that does not exist, one of GPIO 6–11, an output on GPIO 34–39, or an alternate function outside 0–5, then the e32 firmware shall refuse it, write no pad or GPIO register, and print the reason.
