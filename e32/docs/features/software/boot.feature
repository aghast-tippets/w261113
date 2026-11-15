@EP-02 @FEAT-017
Feature: FEAT-017: Boot paths (flash and RAM)
  Epic: EP-02 Boot and run on the ESP32   ·   Level: software

  Supports: US-06 via SW-BLD-03
  Supports: US-09 via STK-05 → SYS-07 → SUB-BOOT-03 → SW-CON-01
  Supports: US-11 via STK-05 → SYS-07 → SUB-BOOT-03 → SW-CON-01

  @SW-BLD-03
  Rule: SW-BLD-03: Serial targets
    EARS: When `make ram` is run, it shall invoke `ESPTOOL --chip esp32 -p PORT --no-stub load_ram e32.bin`. When `make flash` is run, it shall invoke `ESPTOOL --chip esp32 -p PORT -b 460800 write_flash -fm keep -ff keep -fs keep 0x1000 e32.bin`.

    @hardware @pending @SYS-26 @VER-SYS-04
    Scenario: SW-BLD-03-S01: Flash with make flash on a board
      Given a board in download mode on PORT
      When I run "make flash PORT=/dev/ttyUSB0"
      Then the command succeeds
      When I run "esptool --chip esp32 -p /dev/ttyUSB0 read_flash 0x1000 <size of e32.bin> /tmp/rb.bin"
      Then "/tmp/rb.bin" is identical to "e32.bin"
      When I reset the board
      Then the monitor prompt is shown

    @hardware @pending @SYS-27 @VER-SYS-04
    Scenario: SW-BLD-03-S02: RAM with make ram on a board
      Given a board in download mode on PORT
      When I run "make ram PORT=/dev/ttyUSB0"
      Then the command succeeds
      And the monitor prompt is shown

  @SW-CON-01
  Rule: SW-CON-01: Keep the ROM's UART set-up
    EARS: `serial_setup` shall not write `UART_CLKDIV` or `UART_CONF0`, and shall return once the transmit FIFO count is 0.
