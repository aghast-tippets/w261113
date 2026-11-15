@EP-05 @FEAT-045
Feature: FEAT-045: Blink mode
  Epic: EP-05 GPIO control   ·   Level: system

  User stories delivered:
    US-17  As an operator without a serial connection, I want a build mode that
           blinks the LED, so that I can see the firmware running.

  Actors: Bench operator / tester (ACT-H3, persona "olga")

  @SYS-22
  Rule: SYS-22: Blink mode
    EARS: Where blink mode is selected at build time, the e32 firmware shall toggle `LED_GPIO` (GPIO2 by default) every 500 ms and print each new state on UART0.
