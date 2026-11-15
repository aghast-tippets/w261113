@EP-02 @FEAT-016
Feature: FEAT-016: Boot paths (flash and RAM)
  Epic: EP-02 Boot and run on the ESP32   ·   Level: hardware

  Supports: US-03 via STK-04 → SYS-04 → SUB-TGT-01 → HW-04
  Supports: US-05 via STK-03 → SYS-05 → SUB-TGT-01 → HW-04
  Supports: US-06 via STK-04 → SYS-04 → SUB-TGT-01 → HW-04
  Supports: US-08 via STK-17 → SYS-23 → SUB-TGT-01 → HW-04
  Supports: US-09 via STK-05 → SYS-07 → SUB-TGT-01 → HW-04
  Supports: US-11 via STK-05 → SYS-07 → SUB-TGT-01 → HW-04

  @HW-04
  Rule: HW-04: Serial connection
    EARS: UART0 TXD (GPIO1) and RXD (GPIO3) shall be connected to a USB-serial bridge that the host can open as `PORT`.

  @HW-05
  Rule: HW-05: Boot and reset controls
    EARS: When GPIO0 is held low while EN is released, the board shall enter ROM download mode. The board shall provide a means to pulse EN, by a button or by the bridge's DTR/RTS circuit.

  @HW-09
  Rule: HW-09: Free SRAM after hand-over
    EARS: While the firmware runs, IRAM `0x40080000`–`0x4009FFFF` and DRAM `0x3FFB0000`–`0x3FFDBFFF` shall be usable by the application, with no ROM data that must be preserved.

    @host @SYS-23 @HW-10 @VER-SYS-19
    Scenario: HW-09-S01: Firmware runs from internal SRAM only
      Given the firmware is built
      When I run "esptool --chip esp32 image-info e32.bin"
      Then every segment lies in 0x3ffb0000-0x3ffdbfff or 0x40080000-0x4009ffff
      And "e32.map" places .rodata in DRAM
      And no source refers to 0x3f400000-0x3fbfffff or 0x400c2000-0x40bfffff

  @HW-11
  Rule: HW-11: Boot ROM behaviour relied on
    EARS: When the chip resets, the boot ROM shall:
      - load the segmented image from flash `0x1000` (in SPI boot), or over UART0 (in download mode);
      - verify the XOR checksum;
      - leave UART0 configured at 115200 8N1;
      - call the entry point with the windowed ABI.

    @qemu @SYS-04 @SUB-BOOT-01 @VER-SYS-02 @VER-STK-03 @VER-SUB-06
    Scenario: HW-11-S01: Flash boot through the ROM
      Given the firmware is built
      And "flash.img" holds e32.bin at offset 0x1000
      When the firmware is booted in QEMU from flash
      Then the console shows "rst:0x1 (POWERON_RESET),boot:0x12 (SPI_FAST_FLASH_BOOT)"
      And the console shows "e32: bare-metal ESP32"
      And the console shows "stack top 0x3ffdc000"
      And the monitor prompt is shown

    @qemu @SYS-04 @VER-SUB-03
    Scenario: HW-11-S02: The real boot ROM accepts the image
      Given the firmware is booted in QEMU from flash
      Then the console shows "load:0x3ffb0000"
      And the console shows "load:0x40080000"
      And the console shows a line matching /^entry 0x400803[0-9a-f]{2}$/
      And the console does not show "invalid header"
      And the console does not show "checksum"
