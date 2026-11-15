@EP-02 @FEAT-019
Feature: FEAT-019: Boot paths (flash and RAM)
  Epic: EP-02 Boot and run on the ESP32   ·   Level: unit

  Supports: US-03 via HW-11 → CMP-18
  Supports: US-06 via HW-11 → CMP-18
  Supports: US-09 via STK-05 → SYS-07 → SUB-BOOT-03 → SW-CON-01 → CMP-18
  Supports: US-11 via STK-05 → SYS-07 → SUB-BOOT-03 → SW-CON-01 → CMP-18

  @CMP-18
  Rule: CMP-18: io.c: serial_setup
    EARS: When `serial_setup()` is called, it shall spin until `TXCNT(STATUS)` = 0, and shall write no UART register.

    @qemu @SUB-BOOT-03 @SW-CON-01 @VER-SUB-08
    Scenario: CMP-18-S01: The ROM's last line is not mixed with the banner
      When the firmware is booted in QEMU from flash
      Then the console shows a line matching /^entry 0x[0-9a-f]{8}$/
      And the next non-empty line starts with "e32: bare-metal ESP32"

    @host @gtest @VER-CMP-10
    Scenario: CMP-18-S02: serial_setup waits for the ROM's output to drain
      Given the UART transmit FIFO holds 5 bytes for the next 2 status reads
      When the firmware calls serial_setup
      Then the status register was read 3 times
      And no UART register was written
