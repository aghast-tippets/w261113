@EP-07 @FEAT-070
Feature: FEAT-070: Faults and recovery
  Epic: EP-07 Fault reporting and recovery   ·   Level: unit

  Supports: US-22 via CMP-09
  Supports: US-23 via CMP-29
  Supports: US-26 via CMP-27

  @CMP-09
  Rule: CMP-09: vectors.S: _panic
    EARS: When entered with the kind in `a0` and the original `a0` in `EXCSAVE1`, `_panic` shall fill `panic_frame` (IF-07), then call `panic_handler(&panic_frame)` on the private 2 KB stack with `PS.INTLEVEL` = 15. It never returns.

    @qemu @SUB-FLT-01 @SUB-FLT-02 @SW-FLT-01 @IF-07 @VER-SUB-17
    Scenario: CMP-09-S01: The report prints even when the stack pointer is unusable
      Given the firmware is booted in QEMU from flash
      And the monitor prompt is shown
      When I enter "f 4"
      Then the console shows "*** Double exception"
      And the console shows a line matching /^pc  4008[0-9a-f]{4}  ps  [0-9a-f]{8}  excvaddr 00000094$/

  @CMP-27
  Rule: CMP-27: mimmo.c: fault
    EARS: When `fault(n)` is called, it shall execute the SW-MON-05 action for n ∈ 0–5, using volatile operands so that the compiler cannot remove or rewrite the faulting operation.

    @qemu @SYS-19 @SYS-30 @SUB-EXC-05 @SW-EXC-11 @SW-MON-05 @SW-FLT-02 @SW-FLT-03 @CMP-28 @VER-SYS-15 @VER-STK-11
    Scenario Outline: CMP-27-S01: Deliberate faults
      Given the firmware is booted in QEMU from flash
      And the monitor prompt is shown
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

  @CMP-28
  Rule: CMP-28: panic.c: panic_handler
    EARS: When `panic_handler(f)` is called, it shall select the PC and PS for `f->kind` as follows:
      - user or kernel: `EPC1` and `f->ps`;
      - double: `DEPC` and `f->ps`;
      - level L: `EPC[L]` and `EPS[L]`.
      It shall then print the SW-FLT-02 report, with names from SW-FLT-03. A second call shall spin silently. Compile-time assertions shall check the IF-06 and IF-07 offsets.

    @host @gtest @VER-CMP-14
    Scenario Outline: CMP-28-S01: The fault report names the cause and the registers
      Given a panic frame of kind <kind> with cause <cause>, EPC1 400815db, DEPC 40081000 and a0 80081658
      When panic_handler runs
      Then the console shows "<heading>"
      And the console shows "<pc line>"
      And the console shows "called from ~40081658"
      And the console shows "Press any key to reboot"

      Examples:
        | kind | cause | heading                                      | pc line                                         |
        | 1    | 28    | *** Fatal exception 28: LoadProhibited       | pc  400815db  ps  00060530  excvaddr 00000000   |
        | 1    | 0     | *** Fatal exception 0: IllegalInstruction    | pc  400815db  ps  00060530                      |
        | 1    | 6     | *** Fatal exception 6: IntegerDivideByZero   | pc  400815db  ps  00060530                      |
        | 2    | 29    | *** Kernel exception 29: StoreProhibited     | pc  400815db  ps  00060530  excvaddr 00000000   |
        | 3    | 29    | *** Double exception (cause 29 while handling an exception at 400815db) | pc  40081000  ps  00060530  excvaddr 00000000 |

    @host @gtest @VER-CMP-14
    Scenario: CMP-28-S02: A high-level interrupt reports its level and the pending lines
      Given a panic frame of kind 19 (level 3) with EPC3 40082000 and EPS3 00060023
      And the INTERRUPT register reads 20000000
      When panic_handler runs
      Then the console shows "*** Unexpected high-level interrupt"
      And the console shows "    level 3, pending 20000000"
      And the console shows "pc  40082000  ps  00060023"

  @CMP-29
  Rule: CMP-29: panic.c: panic_getc, reboot
    EARS: When called, `panic_getc()` shall poll the UART0 RX FIFO and return one byte. When called, `reboot()` shall write `0x80000000` to `RTC_CNTL_OPTIONS0` and spin.

    @qemu @SYS-20 @SUB-FLT-03 @SW-FLT-05 @HW-12 @VER-SYS-16
    Scenario Outline: CMP-29-S01: A key press reboots after a fault
      Given the firmware is booted in QEMU from flash
      And the monitor prompt is shown
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

    @host @gtest @VER-CMP-14
    Scenario: CMP-29-S02: A key press after the report reboots the chip
      Given a panic frame of kind 1 with cause 0
      And the UART will receive "q" after the report
      When panic_handler runs
      Then 80000000 is written to RTC_CNTL_OPTIONS0 at 3ff48000
      And nothing is written after it
