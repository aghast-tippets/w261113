@EP-06 @FEAT-056
Feature: FEAT-056: Interrupts
  Epic: EP-06 Exception and interrupt handling   ·   Level: subsystem

  Supports: US-10 via STK-19 → SYS-18 → SUB-EXC-04
  Supports: US-19 via STK-08 → SYS-16 → SUB-EXC-03
  Supports: US-20 via STK-09 → SYS-31 → SUB-EXC-04
  Supports: US-21 via STK-08 → SYS-16 → SUB-EXC-03
  Supports: US-29 via STK-08 → SYS-16 → SUB-EXC-03

  @SUB-EXC-03
  Rule: SUB-EXC-03: Interrupt context
    EARS: When a level-1 interrupt is taken, the exception subsystem shall preserve the complete interrupted context, call the dispatcher as an ordinary windowed C function, and restore the context exactly before returning.

  @SUB-EXC-04
  Rule: SUB-EXC-04: Routing and dispatch
    EARS: The exception subsystem shall route peripheral sources to CPU interrupt lines through the interrupt matrix, and dispatch every pending, enabled level-1 line to its registered handler.
