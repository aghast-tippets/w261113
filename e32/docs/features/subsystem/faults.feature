@EP-07 @FEAT-067
Feature: FEAT-067: Faults and recovery
  Epic: EP-07 Fault reporting and recovery   ·   Level: subsystem

  Supports: US-22 via SYS-19 → SUB-EXC-05
  Supports: US-23 via STK-10 → SYS-20 → SUB-FLT-03
  Supports: US-26 via STK-10 → SYS-20 → SUB-FLT-03

  @SUB-EXC-05
  Rule: SUB-EXC-05: Route faults
    EARS: If a user exception other than a level-1 interrupt or alloca, a kernel exception, a double exception, or an interrupt of level 2–7 occurs, then the exception subsystem shall transfer control to the fault subsystem, identifying which kind of fault it is.

  @SUB-FLT-01
  Rule: SUB-FLT-01: Capture state
    EARS: When entered, the fault subsystem shall capture all address registers and the relevant special registers into a static frame, and continue on a private stack, independent of the faulting stack.

  @SUB-FLT-02
  Rule: SUB-FLT-02: Report
    EARS: When the state is captured, the fault subsystem shall print the fault report on UART0 using polled I/O with all maskable interrupts masked.

  @SUB-FLT-03
  Rule: SUB-FLT-03: Reboot
    EARS: When a character is received after the report, the fault subsystem shall request a software system reset through `RTC_CNTL`.

  @SUB-FLT-04
  Rule: SUB-FLT-04: Nested faults
    EARS: If a fault occurs while a fault is being reported, then the fault subsystem shall halt without further output.
