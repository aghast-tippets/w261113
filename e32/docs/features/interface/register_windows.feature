@EP-06 @FEAT-053
Feature: FEAT-053: Register windows and alloca
  Epic: EP-06 Exception and interrupt handling   ·   Level: interface

  Supports: US-18 via IF-15

  @IF-15
  Rule: IF-15: Windowed-ABI save areas
    EARS: The window handlers and the compiler-generated code shall share these stack conventions:
      - a frame's `a0`–`a3` are saved in the 16 bytes below its callee's stack pointer;
      - a call8 frame's `a4`–`a7` (or a call12 frame's `a4`–`a11`) are saved at the bottom of its caller's frame, whose stack pointer is read from `[sp − 12]`;
      - the 16 bytes below an interrupted stack pointer are left untouched by interrupt entry.

    @qemu @SUB-EXC-01 @SUB-EXC-02 @VER-SUB-09 @VER-SYS-11
    Scenario Outline: IF-15-S01: Stress with an alloca counter
      Given a build variant that counts entries to _alloca_handler and adds a command "S" running 2000 rounds of recurse(200) and vla_after_spill(100 + i % 16)
      And timer_init(<hz>) in main.c
      When the firmware is booted in QEMU from flash
      And I enter "S"
      Then the console shows a line matching /^stress: 0 bad, \d+ ticks, <alloca> alloca exceptions$/

      Examples:
        | hz    | alloca          |
        | 100   | 2000            |
        | 20000 | (20[0-9][0-9])  |
