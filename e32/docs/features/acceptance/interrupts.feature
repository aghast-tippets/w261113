@EP-06 @FEAT-065
Feature: FEAT-065: Stakeholder acceptance: Exception and interrupt handling
  Epic: EP-06 Exception and interrupt handling   ·   Level: acceptance

  User stories delivered:
    US-18  As a developer, I want deep recursion and variable-length arrays to
           work as in hosted C, so that I don't have to know about register
           windows.
    US-19  As an integrator, I want to route a peripheral to a CPU interrupt line
           and attach a C handler, so that my code reacts to events.
    US-21  As an integrator, I want `irq_save()`/`irq_restore()`, so that data
           shared with handlers is updated consistently.
    US-29  As an operator, I want to see the uptime and per-line interrupt
           counts, so that I can tell whether interrupts are firing.

  Actors: Firmware developer (ACT-H1, persona "dana"), Bench operator /
    tester (ACT-H3, persona "olga")

  @STK-08 @US-19 @US-21 @US-29
  Rule: STK-08: Attach code to interrupts
    EARS: The integrator needs to route peripheral interrupts to the CPU and attach C handlers to them, and to protect shared data with critical sections.

    @qemu @STK-09 @VER-STK-07
    Scenario: STK-08-S01: Integrator attaches handlers and uses the tick
      When the operator enters "s" and then "i"
      Then the software interrupt handler ran once
      And lines 6 and 17 are counting

  @STK-11 @US-18
  Rule: STK-11: Ordinary C semantics
    EARS: The developer needs deep call chains and variable-length arrays to work as in ordinary hosted C, without knowing the CPU's register-window scheme.

    @qemu @VER-STK-09
    Scenario: STK-11-S01: Developer relies on ordinary C semantics
      When the developer enters "s"
      Then deep recursion and the variable-length array both report "ok"
