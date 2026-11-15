@EP-01 @FEAT-009
Feature: FEAT-009: Boot image generation
  Epic: EP-01 Build from source without an SDK   ·   Level: unit

  Supports: US-03 via CMP-33

  @CMP-33
  Rule: CMP-33: tools/mkimage.c
    EARS: When invoked as `mkimage in.elf out.bin`, the tool shall implement SW-IMG-01 to SW-IMG-06 in portable C99 with no dependency beyond the C standard library, and exit with 0 on success or 1 on any error.

    @host @IF-01 @SUB-BLD-04 @SW-IMG-03 @SW-IMG-06 @VER-SUB-03 @VER-CMP-18
    Scenario: CMP-33-S01: A valid image is decoded by an independent implementation
      Given the firmware is built
      When I run "esptool --chip esp32 image-info e32.bin"
      Then the output contains "Segments: 2"
      And the output contains "Chip ID: 0 (ESP32)"
      And the output contains "(valid)"
      And segment 0 is loaded at 0x3ffb0000 with memory type "DRAM"
      And segment 1 is loaded at 0x40080000 with memory type "IRAM"
