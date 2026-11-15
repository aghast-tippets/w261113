@EP-02 @FEAT-025
Feature: FEAT-025: Stakeholder acceptance: Boot and run on the ESP32
  Epic: EP-02 Boot and run on the ESP32   ·   Level: acceptance

  User stories delivered:
    US-03  As a developer, I want the ELF converted into a boot-ROM image as part
           of the build, so that I can load or flash it directly.
    US-05  As a developer, I want to load and start the firmware in RAM over the
           serial port, so that I iterate without writing flash.
    US-07  As an operator, I want the board to stay up indefinitely, so that my
           monitor session is not interrupted by watchdogs the ROM armed.
    US-08  As a developer, I want the firmware to run from internal SRAM only, so
           that the cheapest ESP32 boards without PSRAM work.

  Actors: Firmware developer (ACT-H1, persona "dana"), Bench operator /
    tester (ACT-H3, persona "olga")

  @STK-03 @US-03 @US-05
  Rule: STK-03: Run without writing flash
    EARS: When iterating, the developer needs to load and run the firmware in RAM over the serial port without writing flash.

    @qemu @hardware @STK-04 @VER-STK-03
    Scenario: STK-03-S01: Developer uses both load paths
      When the developer runs "make ram" with the board in download mode
      Then the monitor prompt appears
      When the developer runs "make flash" and resets the board
      Then the monitor prompt appears after every reset

  @STK-12 @US-07
  Rule: STK-12: No spontaneous resets
    EARS: While the firmware is running, the operator needs the board not to reset by itself.

    @hardware @pending @VER-STK-10
    Scenario: STK-12-S01: Operator leaves the board running
      When the board idles at the prompt for 10 minutes
      Then it has not reset

  @STK-17 @US-08
  Rule: STK-17: Basic board is enough
    EARS: The developer needs the firmware to fit and run on a basic ESP32 module with no PSRAM.

    @hardware @pending @VER-STK-13
    Scenario: STK-17-S01: Developer uses the cheapest board
      Given an ESP32-WROOM-32 DevKit without PSRAM
      When the developer flashes e32 and enters "s"
      Then the self test reports "all ok"
