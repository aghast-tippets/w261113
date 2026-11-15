@EP-04 @FEAT-039
Feature: FEAT-039: Stakeholder acceptance: Interactive memory monitor (mimmo)
  Epic: EP-04 Interactive memory monitor (mimmo)   ·   Level: acceptance

  User stories delivered:
    US-10  As an operator, I want to correct typing with backspace and to paste
           lines while the firmware is busy, so that no input is lost or mangled.
    US-12  As an operator, I want to read, write and dump 32-bit words at any
           address, so that I can inspect and poke registers and RAM.
    US-13  As an operator, I want malformed or unaligned commands rejected with a
           short hint, so that a typo never pokes memory.
    US-14  As an operator, I want to call a function at a given address, so that
           I can run code I loaded or try out a routine.

  Actors: Bench operator / tester (ACT-H3, persona "olga")

  @STK-06 @US-10 @US-12 @US-13 @US-14
  Rule: STK-06: Inspect and modify memory interactively
    EARS: The operator needs to read, write and dump memory and registers, and to call code, from the console, with typing errors rejected harmlessly.

    @qemu @VER-STK-05
    Scenario: STK-06-S01: Operator inspects and modifies memory
      When the operator enters "h", "w 3ffb1000 cafe", "r 3ffb1000", "d 3ffb0000" and "g <gpio_init>"
      Then each command answers in its documented format
      When the operator enters "r 3ffb0002"
      Then the console shows "?? (h for help)"
