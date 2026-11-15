@EP-06 @FEAT-057
Feature: FEAT-057: Interrupts
  Epic: EP-06 Exception and interrupt handling   ·   Level: software

  Supports: US-10 via STK-19 → SYS-18 → SUB-EXC-04 → SW-EXC-05
  Supports: US-18 via STK-11 → SYS-15 → SUB-EXC-02 → SW-EXC-02
  Supports: US-19 via SW-CON-04
  Supports: US-20 via STK-09 → SYS-31 → SUB-EXC-04 → SW-EXC-05
  Supports: US-21 via SW-CON-06
  Supports: US-22 via SYS-19 → SUB-EXC-05 → SW-EXC-02
  Supports: US-29 via STK-08 → SYS-16 → SUB-EXC-03 → SW-EXC-02

  @SW-CON-04
  Rule: SW-CON-04: Enable interrupt receive
    EARS: When `serial_irq_init(irq)` is called, it shall:
      1. set the RX-FIFO-full threshold to 1, preserving the other `UART_CONF1` bits;
      2. clear all UART0 interrupt status;
      3. enable only `RXFIFO_FULL`;
      4. map interrupt source 34 (UART0) to `irq`;
      5. register the receive handler on `irq`.

    @qemu @SUB-EXC-04 @IF-12 @VER-SUB-10
    Scenario: SW-CON-04-S01: The tick and the matrix-routed UART are counted
      Given the firmware is booted in QEMU from flash
      When I enter "i"
      Then the console shows a line matching /^irq  6: [1-9]\d*$/
      And the console shows a line matching /^irq 17: [1-9]\d*$/

  @SW-CON-06
  Rule: SW-CON-06: Sleeping getc
    EARS: While interrupt receive is enabled, `getc` shall check the ring buffer with interrupts masked by `irq_save`. If the buffer holds data, it shall return the oldest byte; otherwise it shall execute `waiti 0` and check again. It shall restore the caller's `PS` before returning.

    @qemu @SW-EXC-09 @VER-SUB-13
    Scenario: SW-CON-06-S01: Waiting for input sleeps without losing a wake-up
      Given the firmware is booted in QEMU from flash
      When I enter "r 3ffb1000" 20 times in quick succession
      Then the console shows "read 3ffb1000" 20 times

  @SW-EXC-02
  Rule: SW-EXC-02: User-vector dispatch
    EARS: When the user exception vector is entered, it shall save `a0` in `EXCSAVE1`, then branch on `EXCCAUSE`:
      - 4 goes to the level-1 handler;
      - 5 goes to the alloca handler;
      - anything else goes to `_panic` with kind `KIND_USER`.

  @SW-EXC-03
  Rule: SW-EXC-03: Level-1 handler sequence
    EARS: When a level-1 interrupt is dispatched, the handler shall:
      1. build a frame at SP − 16 − 96;
      2. save `a0`–`a15`, `EPC1`, `PS`, `SAR`, `LBEG`, `LEND` and `LCOUNT`;
      3. set `LCOUNT` to 0;
      4. set `PS` to `WOE | UM | INTLEVEL(1)`;
      5. spill all other register windows;
      6. set SP to the frame and call `irq_dispatch(frame)`;
      7. restore `PS` (`EXCM` = 1) and every saved register;
      8. execute `rfe`.

  @SW-EXC-05
  Rule: SW-EXC-05: irq_init
    EARS: When `irq_init` is called, it shall write 6 (an internal line, which ignores the matrix) to all 69 `PRO_INTR_MAP` registers, write 0 to `INTENABLE`, and write `0xFFFFFFFF` to `INTCLEAR`.

  @SW-EXC-06
  Rule: SW-EXC-06: irq_request
    EARS: If `irq_request` is given a line outside 0–31 or a line that is not level 1, then it shall return −1 and change nothing. Otherwise it shall store the handler and argument, enable the line, and return 0.

    @qemu @SYS-16 @SUB-EXC-03 @SW-EXC-07 @IF-09 @VER-SYS-12 @VER-STK-07 @VER-BR-04
    Scenario: SW-EXC-06-S01: A software interrupt runs its handler once
      Given the firmware is booted in QEMU from flash
      When I enter "s"
      Then the console shows "software irq:      1 hit (ok)"
      When I enter "i"
      Then the console shows "irq  7: 1"

  @SW-EXC-07
  Rule: SW-EXC-07: irq_dispatch
    EARS: While `INTERRUPT & INTENABLE & 0x000637FF` is non-zero, `irq_dispatch` shall take the lowest-numbered line. If that line is 7 or 10, it shall clear the line through `INTCLEAR` first. It shall then increment the line's count and call its handler.

  @SW-EXC-08
  Rule: SW-EXC-08: Unhandled line
    EARS: If a pending, enabled level-1 line has no registered handler, then `irq_dispatch` shall disable the line and print `irq N: no handler, disabled`.

  @SW-EXC-09
  Rule: SW-EXC-09: Critical sections
    EARS: `irq_save` shall raise `PS.INTLEVEL` to 3 (`rsil 3`) and return the previous `PS`. `irq_restore` shall write the given `PS` back and execute `rsync`.

  @SW-EXC-10
  Rule: SW-EXC-10: Enable and disable
    EARS: `irq_enable` and `irq_disable` shall read, modify and write `INTENABLE` inside a critical section.
