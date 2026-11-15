@EP-02 @FEAT-015
Feature: FEAT-015: Boot paths (flash and RAM)
  Epic: EP-02 Boot and run on the ESP32   ·   Level: subsystem

  Supports: US-01 via SYS-08 → SUB-BOOT-01
  Supports: US-03 via STK-03 → SYS-05 → SUB-BOOT-01
  Supports: US-05 via STK-03 → SYS-05 → SUB-BOOT-01
  Supports: US-09 via STK-05 → SYS-07 → SUB-BOOT-03
  Supports: US-11 via STK-05 → SYS-07 → SUB-BOOT-03
  Supports: US-18 via STK-11 → SYS-15 → SUB-BOOT-01
  Supports: US-19 via STK-08 → SYS-16 → SUB-BOOT-01
  Supports: US-21 via STK-08 → SYS-16 → SUB-BOOT-01
  Supports: US-29 via STK-08 → SYS-16 → SUB-BOOT-01

  @SUB-BOOT-01
  Rule: SUB-BOOT-01: C environment
    EARS: When the boot ROM transfers control to the entry point, the boot subsystem shall, before calling any C function:
      - disable all interrupts;
      - leave a single live register window;
      - install the firmware's vector table;
      - set the firmware's own stack and processor state;
      - clear BSS.

  @SUB-BOOT-03
  Rule: SUB-BOOT-03: Inherit the console set-up
    EARS: The boot subsystem shall keep the UART0 configuration left by the boot ROM, and shall wait until the ROM's pending output has left the transmit FIFO before the firmware prints.
