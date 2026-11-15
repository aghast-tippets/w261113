@EP-08 @FEAT-078
Feature: FEAT-078: Emulation and stress
  Epic: EP-08 Verification and emulation   ·   Level: interface

  Supports: US-25 via IF-16

  @IF-16
  Rule: IF-16: Emulator invocation
    EARS: The verification environment shall start QEMU as `qemu-system-xtensa -nographic -machine esp32 -drive file=flash.img,if=mtd,format=raw`. For download mode it shall add `-global driver=esp32.gpio,property=strap_mode,value=0x0f`, and put the console on stdio (`-serial stdio`) or TCP (`-serial tcp::PORT,server,nowait`).

    @qemu @SUB-VEN-01 @VER-SUB-19
    Scenario Outline: IF-16-S01: Both QEMU invocations work
      When QEMU is started with "<options>"
      And the firmware reaches the monitor through "<path>"
      And I enter "s"
      Then the console shows "all ok"

      Examples:
        | options                                                                  | path               |
        | -machine esp32 -drive file=flash.img,if=mtd,format=raw -serial stdio      | flash boot         |
        | -machine esp32 -drive file=empty.img,if=mtd,format=raw -global driver=esp32.gpio,property=strap_mode,value=0x0f -serial tcp::5556,server,nowait | esptool load-ram |
