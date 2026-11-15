@EP-06 @FEAT-055
Feature: FEAT-055: Interrupts
  Epic: EP-06 Exception and interrupt handling   ·   Level: system

  User stories delivered:
    US-19  As an integrator, I want to route a peripheral to a CPU interrupt line
           and attach a C handler, so that my code reacts to events.
    US-21  As an integrator, I want `irq_save()`/`irq_restore()`, so that data
           shared with handlers is updated consistently.
    US-29  As an operator, I want to see the uptime and per-line interrupt
           counts, so that I can tell whether interrupts are firing.

  Actors: Firmware developer (ACT-H1, persona "dana"), Bench operator /
    tester (ACT-H3, persona "olga")

  @SYS-16
  Rule: SYS-16: Interrupt handling
    EARS: When an enabled level-1 interrupt occurs, the e32 firmware shall run the C handler registered for its line and then resume the interrupted code with its registers and processor state unchanged.
