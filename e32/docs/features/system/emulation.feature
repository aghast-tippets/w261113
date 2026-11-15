@EP-08 @FEAT-075
Feature: FEAT-075: Emulation and stress
  Epic: EP-08 Verification and emulation   ·   Level: system

  User stories delivered:
    US-25  As a tester, I want to run the firmware in QEMU with the real boot
           ROM, so that I can verify most requirements without a board.

  Actors: Bench operator / tester (ACT-H3, persona "olga")

  @SYS-24
  Rule: SYS-24: Emulator boot
    EARS: When `make qemu` is run with Espressif's QEMU available as `QEMU`, the system shall boot the firmware in machine `esp32` through the real ESP32 boot ROM from a 4 MB flash image.
