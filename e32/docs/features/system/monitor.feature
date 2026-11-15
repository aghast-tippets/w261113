@EP-04 @FEAT-035
Feature: FEAT-035: Memory monitor
  Epic: EP-04 Interactive memory monitor (mimmo)   ·   Level: system

  User stories delivered:
    US-10  As an operator, I want to correct typing with backspace and to paste
           lines while the firmware is busy, so that no input is lost or mangled.
    US-12  As an operator, I want to read, write and dump 32-bit words at any
           address, so that I can inspect and poke registers and RAM.
    US-13  As an operator, I want malformed or unaligned commands rejected with a
           short hint, so that a typo never pokes memory.
    US-14  As an operator, I want to call a function at a given address, so that
           I can run code I loaded or try out a routine.
    US-19  As an integrator, I want to route a peripheral to a CPU interrupt line
           and attach a C handler, so that my code reacts to events.
    US-20  As an integrator, I want a 100 Hz tick and microsecond delays, so that
           I can measure and wait for time.
    US-21  As an integrator, I want `irq_save()`/`irq_restore()`, so that data
           shared with handlers is updated consistently.
    US-29  As an operator, I want to see the uptime and per-line interrupt
           counts, so that I can tell whether interrupts are firing.

  Actors: Firmware developer (ACT-H1, persona "dana"), Bench operator /
    tester (ACT-H3, persona "olga")

  Background:
    Given the firmware is booted in QEMU from flash
    And the monitor prompt is shown

  @SYS-10 @US-12 @US-14
  Rule: SYS-10: Execute monitor commands
    EARS: When the operator enters a command line terminated by CR or LF, the e32 firmware shall execute the monitor command it names (`r`, `w`, `d`, `p`, `a`, `g`, `i`, `s`, `f`, `h` or `?`) and print its result, then a new prompt.

    @qemu @VER-SYS-08
    Scenario: SYS-10-S01: Dump with a count
      When I enter "d 3ffb0000 8"
      Then the console shows 2 lines matching /^3ffb00[01]0:( [0-9a-f]{8}){4}$/

    @qemu @VER-SYS-08 @VER-STK-05
    Scenario: SYS-10-S02: Call a function by address
      Given the address of "gpio_init" from "xtensa-esp32-elf-nm e32.elf"
      When I enter "g <that address>"
      Then the console shows "go <that address>"
      And the monitor prompt is shown

    @qemu @VER-SYS-08
    Scenario: SYS-10-S03: Empty lines just prompt again
      When I enter ""
      Then the monitor prompt is shown
      And the console does not show "??"

  @SYS-11
  Rule: SYS-11: Reject malformed commands
    EARS: If a command line names an unknown command, lacks a required argument, contains an invalid number, or gives an address that is not 4-byte aligned to `r`, `w` or `d`, then the e32 firmware shall print `?? (h for help)`, perform no memory access for that line, and print a new prompt.

  @SYS-31
  Rule: SYS-31: Interrupt statistics
    EARS: When the operator enters `i`, the e32 firmware shall print the uptime in seconds with two decimals, the tick count, and the count of every interrupt line that has fired at least once.
