@EP-02 @FEAT-018
Feature: FEAT-018: Boot paths (flash and RAM)
  Epic: EP-02 Boot and run on the ESP32   ·   Level: interface

  Supports: US-01 via SYS-08 → SUB-BOOT-01 → IF-02
  Supports: US-03 via STK-03 → SYS-05 → SUB-BOOT-01 → IF-02
  Supports: US-05 via STK-03 → SYS-05 → SUB-BOOT-01 → IF-02
  Supports: US-09 via STK-05 → SYS-07 → SUB-BOOT-03 → IF-02
  Supports: US-11 via STK-05 → SYS-07 → SUB-BOOT-03 → IF-02
  Supports: US-18 via STK-11 → SYS-15 → SUB-BOOT-01 → IF-02
  Supports: US-19 via STK-08 → SYS-16 → SUB-BOOT-01 → IF-02
  Supports: US-21 via STK-08 → SYS-16 → SUB-BOOT-01 → IF-02
  Supports: US-29 via STK-08 → SYS-16 → SUB-BOOT-01 → IF-02

  @IF-02
  Rule: IF-02: ROM-to-firmware hand-over
    EARS: When the boot ROM has loaded every segment, it shall call the entry point, `call_start`. At that moment the firmware shall assume only the following:
      - its segments are in place;
      - UART0 is configured by the ROM;
      - the CPU is running windowed code on a ROM stack, with ROM vectors and possibly ROM-enabled interrupts.
      It shall assume nothing about any other register, and shall never return to the ROM.

    @qemu @IF-16 @SUB-VEN-01 @VER-SUB-19
    Scenario Outline: IF-02-S01: The firmware works after either ROM hand-over
      Given the firmware is <loaded>
      When I enter "s"
      Then the console shows "all ok"

      Examples:
        | loaded                                           |
        | booted in QEMU from flash                        |
        | loaded into RAM in QEMU download mode            |

  @IF-04
  Rule: IF-04: Host loader transport
    EARS: When the board is in ROM download mode, the host shall drive the ROM's serial loader through esptool:
      - `load_ram` without the flasher stub, to load and run in RAM;
      - `write_flash` at `0x1000` with flash mode, frequency and size all set to `keep`.
      No other host tool shall be required to load the firmware.

    @qemu @SYS-05 @SYS-27 @VER-SYS-03 @VER-STK-03
    Scenario: IF-04-S01: RAM boot through ROM download mode
      Given QEMU is started in download mode with the console on TCP port 5556
      When I run "esptool --chip esp32 -p socket://localhost:5556 --no-stub --before no-reset --after no-reset load-ram e32.bin"
      Then the output contains "Loaded 2 segments from 'e32.bin' to RAM"
      When I enter "s"
      Then the console shows "all ok"
