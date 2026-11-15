@EP-03 @FEAT-031
Feature: FEAT-031: Formatted output
  Epic: EP-03 Console input and output   ·   Level: subsystem

  Supports: US-09 via STK-05 → SYS-06 → SUB-CON-04
  Supports: US-11 via STK-05 → SYS-06 → SUB-CON-04
  Supports: US-12 via SYS-10 → SUB-CON-04
  Supports: US-14 via SYS-10 → SUB-CON-04
  Supports: US-22 via SYS-19 → SUB-CON-04

  @SUB-CON-04
  Rule: SUB-CON-04: Formatted output
    EARS: The console subsystem shall provide `printf` and `sprintf` supporting `%d %i %u %x %X %p %s %c %%`, the `-` and `0` flags, and a decimal field width.
