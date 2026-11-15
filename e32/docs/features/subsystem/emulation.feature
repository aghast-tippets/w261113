@EP-08 @FEAT-076
Feature: FEAT-076: Emulation and stress
  Epic: EP-08 Verification and emulation   ·   Level: subsystem

  Supports: US-25 via SUB-BLD-05

  @SUB-BLD-05
  Rule: SUB-BLD-05: Make targets
    EARS: The build subsystem shall provide the make targets `all`, `ram`, `flash`, `flash.img`, `qemu`, `e32.dis` and `clean`, with `CROSS_COMPILE`, `PORT`, `ESPTOOL`, `QEMU`, `HOSTCC` and `EXTRA_CFLAGS` overridable.

    @host @VER-SUB-04
    Scenario: SUB-BLD-05-S01: make clean removes all build outputs
      Given the firmware is built
      And "flash.img" exists
      When I run "make clean"
      Then none of "e32.elf", "e32.bin", "e32.map", "flash.img", "tools/mkimage" exists

  @SUB-VEN-01
  Rule: SUB-VEN-01: Emulated target
    EARS: The verification environment shall run the firmware in Espressif's QEMU with the real ESP32 boot ROM, in flash-boot mode from a 4 MB image and in download mode (strap `0x0f`), with the console reachable on stdio or TCP.

    @qemu @SYS-24 @SUB-BLD-05 @VER-SYS-20
    Scenario: SUB-VEN-01-S01: make qemu boots to the monitor
      Given the firmware is built
      When I run "make qemu QEMU=<path to qemu-system-xtensa>" and enter "h"
      Then the console shows "e32: bare-metal ESP32"
      And the console shows "mimmo.c: Ready to get input (h for help)"
      And the console shows "r <addr>"
