@EP-07 @FEAT-066
Feature: FEAT-066: Faults and recovery
  Epic: EP-07 Fault reporting and recovery   ·   Level: system

  User stories delivered:
    US-22  As a developer, I want a crash to print the cause, PC and all
           registers, so that I can find the bug with `addr2line`.
    US-23  As a developer, I want to reboot with a key press after a crash, so
           that I don't need to reach for the reset button.
    US-24  As an operator, I want one command that checks the core mechanisms, so
           that I can confirm a board and a build in seconds.
    US-26  As a tester, I want commands that raise each fault type, so that the
           fault handler can be verified on demand.

  Actors: Firmware developer (ACT-H1, persona "dana"), Bench operator /
    tester (ACT-H3, persona "olga")

  Background:
    Given the firmware is booted in QEMU from flash
    And the monitor prompt is shown

  @SYS-19 @US-22
  Rule: SYS-19: Fault report
    EARS: If a fatal exception, a kernel exception, a double exception, or an interrupt of level 2–7 occurs, then the e32 firmware shall print on UART0 a report containing:
      - the fault kind;
      - the cause number and name, where one applies;
      - PC and PS;
      - EXCVADDR, for memory faults;
      - registers a0–a15;
      - SAR, LBEG, LEND and LCOUNT;
      - WINDOWBASE and WINDOWSTART;
      - the caller address.

    @qemu @VER-SYS-15
    Scenario: SYS-19-S01: Memory faults show the faulting address
      When I enter "f 0"
      Then the console shows a line matching /^pc  [0-9a-f]{8}  ps  [0-9a-f]{8}  excvaddr 00000000$/

    @qemu @VER-SYS-15
    Scenario: SYS-19-S02: High-level interrupts show their level
      When I enter "f 5"
      Then the console shows "level 3, pending 20000000"

  @SYS-20
  Rule: SYS-20: Reboot after a fault
    EARS: When a character is received after a fault report, the e32 firmware shall perform a software system reset.

    @hardware @pending @VER-SYS-16 @VER-STK-08
    Scenario: SYS-20-S01: Reboot on a board
      Given the firmware is running on a board
      When I enter "f 0"
      And I press any key
      Then the console shows "rst:0x3 (SW_RESET)"

  @SYS-30
  Rule: SYS-30: Deliberate faults
    EARS: When the operator enters `f <n>` with n from 0 to 5, the e32 firmware shall raise a fault on purpose:
      - 0: a load from address 0;
      - 1: an illegal instruction;
      - 2: an integer divide by zero;
      - 3: a `break` instruction;
      - 4: a stack pointer corrupted so that the next interrupt causes a double exception;
      - 5: a level-3 software interrupt.
