@EP-03 @FEAT-034
Feature: FEAT-034: Stakeholder acceptance: Console input and output
  Epic: EP-03 Console input and output   ·   Level: acceptance

  User stories delivered:
    US-09  As an operator, I want a banner and a prompt at 115200 8N1 when the
           board starts, so that I know it is alive and ready.
    US-11  As an integrator, I want a `printf` with the common integer, string
           and pointer conversions, so that application output is easy to write.

  Actors: Firmware developer (ACT-H1, persona "dana"), Bench operator /
    tester (ACT-H3, persona "olga")

  @STK-05 @US-09 @US-11
  Rule: STK-05: Serial console
    EARS: The operator needs a serial console at 115200 8N1 that shows a start-up banner and a prompt.

    @qemu @STK-19 @VER-STK-04
    Scenario: STK-05-S01: Operator gets a console that keeps pasted input
      When the operator opens a terminal at 115200 8N1 and resets the board
      Then the banner and "> " are shown
      When the operator pastes 20 commands while the self test runs
      Then all 20 are answered
