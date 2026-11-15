@EP-08 @FEAT-077
Feature: FEAT-077: Emulation and stress
  Epic: EP-08 Verification and emulation   ·   Level: software

  Supports: US-25 via SW-BLD-02

  @SW-BLD-02
  Rule: SW-BLD-02: Flash image for QEMU
    EARS: When `flash.img` is built, it shall be 4 MiB of `0xFF` with `e32.bin` written at offset `0x1000`.

    @host @SUB-BLD-05 @VER-SUB-04
    Scenario: SW-BLD-02-S01: The QEMU flash image has the right layout
      When I run "make flash.img"
      Then the size of "flash.img" is 4194304 bytes
      And bytes 0x1000 onwards of "flash.img" equal "e32.bin"
      And every other byte of "flash.img" is 0xff
