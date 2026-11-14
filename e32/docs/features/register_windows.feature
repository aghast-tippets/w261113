@EP-06 @F-11
Feature: Register windows and alloca
  As a developer
  I want deep recursion and variable-length arrays to work
  So that I can write ordinary C without knowing about register windows

  @qemu @SYS-15 @SUB-EXC-01 @SW-EXC-01 @CMP-03 @VER-SYS-11 @VER-STK-09
  Scenario: CMP-03-S01: Recursion 200 frames deep
    Given the firmware is booted in QEMU from flash
    When I enter "s"
    Then the console shows "recursion 200 deep: 20100 (ok)"

  @qemu @SYS-15 @SUB-EXC-02 @SW-EXC-04 @CMP-07 @VER-SYS-11 @VER-STK-09
  Scenario: CMP-07-S01: A variable-length array with its caller spilled
    Given the firmware is booted in QEMU from flash
    When I enter "s"
    Then the console shows "VLA after spill:   919 (ok)"

  @qemu @SUB-EXC-01 @SUB-EXC-02 @IF-15 @VER-SUB-09 @VER-SYS-11
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

  @qemu @pending @CMP-04 @VER-CMP-02
  Scenario: CMP-04-S01: call12 frames are spilled and filled
    Given a build variant with an assembly routine that calls recurse(100) with call12 from a frame reserving the 32-byte extra save area
    When the routine runs
    Then it returns 5050
