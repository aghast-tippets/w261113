@EP-06 @FEAT-060
Feature: FEAT-060: Timekeeping
  Epic: EP-06 Exception and interrupt handling   ·   Level: system

  User stories delivered:
    US-20  As an integrator, I want a 100 Hz tick and microsecond delays, so that
           I can measure and wait for time.
    US-29  As an operator, I want to see the uptime and per-line interrupt
           counts, so that I can tell whether interrupts are firing.

  Actors: Firmware developer (ACT-H1, persona "dana"), Bench operator /
    tester (ACT-H3, persona "olga")

  @SYS-17
  Rule: SYS-17: Tick
    EARS: The e32 firmware shall count ticks at `HZ` (100) per second of CPU time, measured in `CPU_HZ` cycles, and shall keep counting even when a tick interrupt is serviced late.
