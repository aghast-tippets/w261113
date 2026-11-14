@EP-07 @F-14
Feature: Faults and recovery
  As a developer
  I want every crash reported with its cause and registers
  So that I can find bugs and reboot without touching the board

  Background:
    Given the firmware is booted in QEMU from flash
    And the monitor prompt is shown

  @qemu @SYS-19 @SYS-30 @SUB-EXC-05 @SW-EXC-11 @SW-MON-05 @SW-FLT-02 @SW-FLT-03 @CMP-27 @CMP-28 @VER-SYS-15 @VER-STK-11
  Scenario Outline: Deliberate faults
    When I enter "f <n>"
    Then the console shows "<heading>"
    And the console shows a line matching /^pc  [0-9a-f]{8}  ps  [0-9a-f]{8}/
    And the console shows a line matching /^a12 [0-9a-f]{8}  a13 [0-9a-f]{8}  a14 [0-9a-f]{8}  a15 [0-9a-f]{8}$/
    And the console shows a line matching /^sar [0-9a-f]{8}  lbeg [0-9a-f]{8}  lend [0-9a-f]{8}  lcount [0-9a-f]{8}$/
    And the console shows a line matching /^windowbase \d+  windowstart [0-9a-f]{4}$/
    And the console shows a line matching /^called from ~4[0-9a-f]{7}$/
    And the console shows "Press any key to reboot"

    Examples:
      | n | heading                                       |
      | 0 | *** Fatal exception 28: LoadProhibited        |
      | 1 | *** Fatal exception 0: IllegalInstruction     |
      | 2 | *** Fatal exception 6: IntegerDivideByZero    |
      | 3 | *** Debug exception (break?)                  |
      | 4 | *** Double exception (cause 29                |
      | 5 | *** Unexpected high-level interrupt           |

  @qemu @SYS-19 @VER-SYS-15
  Scenario: Memory faults show the faulting address
    When I enter "f 0"
    Then the console shows a line matching /^pc  [0-9a-f]{8}  ps  [0-9a-f]{8}  excvaddr 00000000$/

  @qemu @SYS-19 @VER-SYS-15
  Scenario: High-level interrupts show their level
    When I enter "f 5"
    Then the console shows "level 3, pending 20000000"

  @qemu @SYS-20 @SUB-FLT-03 @SW-FLT-05 @HW-12 @CMP-29 @VER-SYS-16
  Scenario Outline: A key press reboots after a fault
    When I enter "f <n>"
    And I press any key
    Then the console shows "rst:0x3 (SW_RESET),boot:0x12 (SPI_FAST_FLASH_BOOT)"
    And the monitor prompt is shown

    Examples:
      | n |
      | 0 |
      | 1 |
      | 2 |
      | 3 |
      | 4 |
      | 5 |

  @qemu @SUB-FLT-01 @SUB-FLT-02 @SW-FLT-01 @IF-07 @CMP-09 @VER-SUB-17
  Scenario: The report prints even when the stack pointer is unusable
    When I enter "f 4"
    Then the console shows "*** Double exception"
    And the console shows a line matching /^pc  4008[0-9a-f]{4}  ps  [0-9a-f]{8}  excvaddr 00000094$/

  @qemu @STK-10 @VER-STK-08
  Scenario: The PC maps to a source line
    When I enter "f 0"
    And I run "xtensa-esp32-elf-addr2line -f -e e32.elf <pc>"
    Then the output contains "fault"
    And the output contains "mimmo.c"

  @qemu @pending @SUB-FLT-04 @SW-FLT-04 @VER-SUB-17
  Scenario: A fault while reporting a fault halts silently
    Given a build variant whose panic_handler reads address 0 after its first line
    When I enter "f 1"
    Then the console shows "*** Fatal exception 0: IllegalInstruction"
    And the console shows nothing more within 3 seconds

  @hardware @pending @SYS-20 @VER-SYS-16 @VER-STK-08
  Scenario: Reboot on a board
    Given the firmware is running on a board
    When I enter "f 0"
    And I press any key
    Then the console shows "rst:0x3 (SW_RESET)"
