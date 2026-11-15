@EP-02 @FEAT-014
Feature: FEAT-014: Boot paths (flash and RAM)
  Epic: EP-02 Boot and run on the ESP32   ·   Level: system

  User stories delivered:
    US-03  As a developer, I want the ELF converted into a boot-ROM image as part
           of the build, so that I can load or flash it directly.
    US-05  As a developer, I want to load and start the firmware in RAM over the
           serial port, so that I iterate without writing flash.
    US-06  As a developer, I want to store the firmware in flash at `0x1000`, so
           that it starts on its own after every reset.

  Actors: Firmware developer (ACT-H1, persona "dana")

  @SYS-04
  Rule: SYS-04: Flash boot
    EARS: The e32 image shall be accepted and started by the ESP32 boot ROM when stored at flash offset `0x1000`.

  @SYS-05
  Rule: SYS-05: RAM boot
    EARS: When the boot ROM, in UART download mode, loads the image into RAM and jumps to its entry point, the e32 firmware shall start and behave as after a flash boot.

  @SYS-26
  Rule: SYS-26: Flash programming target
    EARS: When `make flash` is run with a board in download mode on `PORT`, the system shall write `e32.bin` at flash offset `0x1000` without altering the image header.

  @SYS-27
  Rule: SYS-27: RAM load target
    EARS: When `make ram` is run with a board in download mode on `PORT`, the system shall load `e32.bin` into RAM through the boot ROM and start it.
