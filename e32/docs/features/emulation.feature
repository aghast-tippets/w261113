@EP-08 @F-16
Feature: Emulation
  As a tester
  I want to run the firmware in QEMU with the real ESP32 boot ROM
  So that most requirements can be verified without a board

  @qemu @SYS-24 @SUB-VEN-01 @SUB-BLD-05 @VER-SYS-20
  Scenario: SUB-VEN-01-S01: make qemu boots to the monitor
    Given the firmware is built
    When I run "make qemu QEMU=<path to qemu-system-xtensa>" and enter "h"
    Then the console shows "e32: bare-metal ESP32"
    And the console shows "mimmo.c: Ready to get input (h for help)"
    And the console shows "r <addr>"

  @qemu @IF-16 @SUB-VEN-01 @VER-SUB-19
  Scenario Outline: IF-16-S01: Both QEMU invocations work
    When QEMU is started with "<options>"
    And the firmware reaches the monitor through "<path>"
    And I enter "s"
    Then the console shows "all ok"

    Examples:
      | options                                                                  | path               |
      | -machine esp32 -drive file=flash.img,if=mtd,format=raw -serial stdio      | flash boot         |
      | -machine esp32 -drive file=empty.img,if=mtd,format=raw -global driver=esp32.gpio,property=strap_mode,value=0x0f -serial tcp::5556,server,nowait | esptool load-ram |

  @host @SW-BLD-02 @SUB-BLD-05 @VER-SUB-04
  Scenario: SW-BLD-02-S01: The QEMU flash image has the right layout
    When I run "make flash.img"
    Then the size of "flash.img" is 4194304 bytes
    And bytes 0x1000 onwards of "flash.img" equal "e32.bin"
    And every other byte of "flash.img" is 0xff

  @host @SUB-BLD-05 @VER-SUB-04
  Scenario: SUB-BLD-05-S01: make clean removes all build outputs
    Given the firmware is built
    And "flash.img" exists
    When I run "make clean"
    Then none of "e32.elf", "e32.bin", "e32.map", "flash.img", "tools/mkimage" exists
