@EP-07 @FEAT-071
Feature: FEAT-071: Stakeholder acceptance: Fault reporting and recovery
  Epic: EP-07 Fault reporting and recovery   ·   Level: acceptance

  User stories delivered:
    US-22  As a developer, I want a crash to print the cause, PC and all
           registers, so that I can find the bug with `addr2line`.
    US-23  As a developer, I want to reboot with a key press after a crash, so
           that I don't need to reach for the reset button.
    US-26  As a tester, I want commands that raise each fault type, so that the
           fault handler can be verified on demand.

  Actors: Firmware developer (ACT-H1, persona "dana"), Bench operator /
    tester (ACT-H3, persona "olga")

  @STK-10 @US-22 @US-23 @US-26
  Rule: STK-10: Understand and recover from crashes
    EARS: If the firmware crashes, then the developer needs a report giving the cause, the location and the registers, and a way to reboot without touching the board.

    @qemu @VER-STK-08
    Scenario: STK-10-S01: Developer reads a crash report and reboots
      When the developer enters "f 0"
      Then the report names "LoadProhibited" and the PC maps to fault() in mimmo.c
      When the developer presses a key
      Then the board reboots with "rst:0x3 (SW_RESET)"

    @qemu @VER-STK-08
    Scenario: STK-10-S02: The PC maps to a source line
      Given the firmware is booted in QEMU from flash
      And the monitor prompt is shown
      When I enter "f 0"
      And I run "xtensa-esp32-elf-addr2line -f -e e32.elf <pc>"
      Then the output contains "fault"
      And the output contains "mimmo.c"
