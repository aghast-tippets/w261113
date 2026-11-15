@EP-07 @FEAT-069
Feature: FEAT-069: Faults and recovery
  Epic: EP-07 Fault reporting and recovery   ·   Level: software

  Supports: US-12 via SYS-10 → SUB-MON-01 → SW-MON-05
  Supports: US-14 via SYS-10 → SUB-MON-01 → SW-MON-05
  Supports: US-19 via STK-08 → SYS-31 → SUB-MON-01 → SW-MON-05
  Supports: US-20 via STK-09 → SYS-31 → SUB-MON-01 → SW-MON-05
  Supports: US-21 via STK-08 → SYS-31 → SUB-MON-01 → SW-MON-05
  Supports: US-22 via SYS-19 → SUB-EXC-05 → SW-EXC-11
  Supports: US-23 via STK-10 → SYS-20 → SUB-FLT-03 → SW-FLT-05
  Supports: US-24 via SYS-21 → SUB-MON-01 → SW-MON-05
  Supports: US-26 via STK-10 → SYS-20 → SUB-FLT-03 → SW-FLT-05
  Supports: US-29 via STK-08 → SYS-31 → SUB-MON-01 → SW-MON-05

  Background:
    Given the firmware is booted in QEMU from flash
    And the monitor prompt is shown

  @SW-EXC-11
  Rule: SW-EXC-11: Fatal vectors
    EARS: When the vectors at offsets `0x180`, `0x1C0`, `0x200`, `0x240`, `0x280`, `0x2C0`, `0x300` or `0x3C0` are entered, each shall save `a0` in `EXCSAVE1`, load its fault kind (`KIND_LEVEL(2…7)`, `KIND_KERNEL`, `KIND_DOUBLE`) and jump to `_panic`.

  @SW-FLT-01
  Rule: SW-FLT-01: _panic capture
    EARS: When `_panic` is entered with the kind in `a0`, it shall:
      1. keep the kind in `MISC0` and the incoming `PS` in `MISC1`;
      2. set `PS` = `EXCM | UM | WOE | INTLEVEL(15)`;
      3. store into `panic_frame`: `a0`–`a15`, the kind, `PS`, `EXCCAUSE`, `EXCVADDR`, `SAR`, `DEPC`, `LBEG`, `LEND`, `LCOUNT`, `WINDOWBASE`, `WINDOWSTART`, `EPC1`–`EPC7` and `EPS2`–`EPS7`;
      4. reset the register window;
      5. set SP to the top of a 2 KB private stack;
      6. set `PS` = `UM | WOE | INTLEVEL(15)`;
      7. call `panic_handler(&panic_frame)`.

  @SW-FLT-02
  Rule: SW-FLT-02: Report format
    EARS: When `panic_handler` runs, it shall print a first line that depends on the kind:
      - user or kernel: `*** Fatal|Kernel exception N: Name`;
      - double: `*** Double exception (cause N while handling an exception at EPC1)`;
      - level 6: `*** Debug exception (break?)`;
      - level 7: `*** NMI`;
      - levels 2–5: `*** Unexpected high-level interrupt`.
      For levels 2–7 it shall add `level L, pending X`. It shall then print the `pc`/`ps` line (with `excvaddr` for memory faults), the registers 4 per line, the `sar`/loop line, the window line, `called from ~X` and `Press any key to reboot`.

  @SW-FLT-03
  Rule: SW-FLT-03: Cause names
    EARS: `panic_handler` shall name the causes 0–3, 5, 6, 8, 9, 12–18, 20, 24–26, 28, 29 and 32 using the Xtensa exception names, and print `?` for any other cause.

  @SW-FLT-04
  Rule: SW-FLT-04: Nested fault
    EARS: If `panic_handler` is entered a second time, then it shall spin without printing.

    @qemu @pending @SUB-FLT-04 @VER-SUB-17
    Scenario: SW-FLT-04-S01: A fault while reporting a fault halts silently
      Given a build variant whose panic_handler reads address 0 after its first line
      When I enter "f 1"
      Then the console shows "*** Fatal exception 0: IllegalInstruction"
      And the console shows nothing more within 3 seconds

  @SW-FLT-05
  Rule: SW-FLT-05: Reboot
    EARS: When the report has been printed, the fault subsystem shall poll the UART0 RX FIFO for one byte and then write `SW_SYS_RST` to `RTC_CNTL_OPTIONS0`.

  @SW-MON-05
  Rule: SW-MON-05: Fault demos
    EARS: When `f n` is entered, the monitor shall act on n as follows:
      - 0: load from address 0;
      - 1: execute `ill`;
      - 2: divide 100 by a volatile zero with `quos`;
      - 3: execute `break 1, 15`;
      - 4: set `a1` = `0x100` and spin;
      - 5: enable line 29 and set it pending;
      - any other value: do nothing.
