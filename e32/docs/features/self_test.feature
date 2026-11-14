@EP-08 @F-15
Feature: Self test
  As an operator
  I want one command that checks the core mechanisms
  So that I can confirm a board and a build in seconds

  @qemu @SYS-21 @SW-MON-04 @CMP-26 @VER-SYS-17 @VER-STK-11
  Scenario: Self test passes after a flash boot
    Given the firmware is booted in QEMU from flash
    When I enter "s"
    Then the console shows each of:
      | text                           |
      | recursion 200 deep: 20100 (ok) |
      | VLA after spill:   919 (ok)    |
      | software irq:      1 hit (ok)  |
      | (ok)                           |
      | all ok                         |
    And the console does not show "BAD"

  @qemu @SYS-21 @VER-SYS-17 @VER-SUB-19
  Scenario: Self test passes after a RAM boot
    Given the firmware is loaded into RAM in QEMU download mode
    When I enter "s"
    Then the console shows "all ok"

  @hardware @pending @SYS-21 @STK-17 @VER-SYS-17 @VER-STK-13
  Scenario: Self test passes on a basic board
    Given the firmware is flashed to an ESP32-WROOM-32 DevKit without PSRAM
    When I enter "s"
    Then the console shows "all ok"
