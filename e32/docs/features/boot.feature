@EP-02 @F-04
Feature: Boot paths
  As a developer
  I want the firmware to start from flash and from RAM
  So that I can iterate quickly and still ship a self-starting board

  @qemu @SYS-04 @SUB-BOOT-01 @HW-11 @VER-SYS-02 @VER-STK-03 @VER-SUB-06
  Scenario: Flash boot through the ROM
    Given the firmware is built
    And "flash.img" holds e32.bin at offset 0x1000
    When the firmware is booted in QEMU from flash
    Then the console shows "rst:0x1 (POWERON_RESET),boot:0x12 (SPI_FAST_FLASH_BOOT)"
    And the console shows "e32: bare-metal ESP32"
    And the console shows "stack top 0x3ffdc000"
    And the monitor prompt is shown

  @qemu @SYS-05 @SYS-27 @IF-04 @VER-SYS-03 @VER-STK-03
  Scenario: RAM boot through ROM download mode
    Given QEMU is started in download mode with the console on TCP port 5556
    When I run "esptool --chip esp32 -p socket://localhost:5556 --no-stub --before no-reset --after no-reset load-ram e32.bin"
    Then the output contains "Loaded 2 segments from 'e32.bin' to RAM"
    When I enter "s"
    Then the console shows "all ok"

  @hardware @pending @SYS-26 @SW-BLD-03 @VER-SYS-04
  Scenario: Flash with make flash on a board
    Given a board in download mode on PORT
    When I run "make flash PORT=/dev/ttyUSB0"
    Then the command succeeds
    When I run "esptool --chip esp32 -p /dev/ttyUSB0 read_flash 0x1000 <size of e32.bin> /tmp/rb.bin"
    Then "/tmp/rb.bin" is identical to "e32.bin"
    When I reset the board
    Then the monitor prompt is shown

  @hardware @pending @SYS-27 @SW-BLD-03 @VER-SYS-04
  Scenario: RAM with make ram on a board
    Given a board in download mode on PORT
    When I run "make ram PORT=/dev/ttyUSB0"
    Then the command succeeds
    And the monitor prompt is shown

  @qemu @SUB-BOOT-03 @SW-CON-01 @CMP-18 @VER-SUB-08
  Scenario: The ROM's last line is not mixed with the banner
    When the firmware is booted in QEMU from flash
    Then the console shows a line matching /^entry 0x[0-9a-f]{8}$/
    And the next non-empty line starts with "e32: bare-metal ESP32"

  @qemu @IF-02 @IF-16 @SUB-VEN-01 @VER-SUB-19
  Scenario Outline: The firmware works after either ROM hand-over
    Given the firmware is <loaded>
    When I enter "s"
    Then the console shows "all ok"

    Examples:
      | loaded                                           |
      | booted in QEMU from flash                        |
      | loaded into RAM in QEMU download mode            |

  @host @SYS-23 @HW-09 @HW-10 @VER-SYS-19
  Scenario: Firmware runs from internal SRAM only
    Given the firmware is built
    When I run "esptool --chip esp32 image-info e32.bin"
    Then every segment lies in 0x3ffb0000-0x3ffdbfff or 0x40080000-0x4009ffff
    And "e32.map" places .rodata in DRAM
    And no source refers to 0x3f400000-0x3fbfffff or 0x400c2000-0x40bfffff
