@EP-08 @FEAT-072
Feature: FEAT-072: Self test
  Epic: EP-08 Verification and emulation   ·   Level: system

  User stories delivered:
    US-24  As an operator, I want one command that checks the core mechanisms, so
           that I can confirm a board and a build in seconds.

  Actors: Bench operator / tester (ACT-H3, persona "olga")

  @SYS-21 @US-24
  Rule: SYS-21: Self test
    EARS: When the operator enters `s`, the e32 firmware shall check deep recursion, a variable-length array with its caller spilled, a software interrupt and the tick rate, print `ok` or `BAD` for each, and finish with `all ok` or `FAILED`.

    @qemu @VER-SYS-17 @VER-SUB-19
    Scenario: SYS-21-S01: Self test passes after a RAM boot
      Given the firmware is loaded into RAM in QEMU download mode
      When I enter "s"
      Then the console shows "all ok"

    @hardware @pending @STK-17 @VER-SYS-17 @VER-STK-13
    Scenario: SYS-21-S02: Self test passes on a basic board
      Given the firmware is flashed to an ESP32-WROOM-32 DevKit without PSRAM
      When I enter "s"
      Then the console shows "all ok"
