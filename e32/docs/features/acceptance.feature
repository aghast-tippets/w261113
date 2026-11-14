@F-18
Feature: Stakeholder acceptance
  Demonstrations that the stakeholder needs (STK) are met, one per
  verification entry. Each is performed by or for the role named.

  @host @EP-01 @STK-01 @STK-18 @VER-STK-01
  Scenario: Developer builds with nothing but a bare toolchain
    Given a host with xtensa-esp32-elf-gcc, make and cc only
    When the developer runs "make clean all"
    Then e32.elf and e32.bin are produced without warnings
    And the inspection shows no SDK, no libc and no ROM routine in use

  @host @pending @EP-01 @STK-02 @VER-STK-02
  Scenario: Maintainer reproduces the toolchain
    When the maintainer runs "tools/build-toolchain.sh" in an empty directory
    Then the resulting compiler builds e32 without warnings

  @qemu @hardware @EP-02 @STK-03 @STK-04 @VER-STK-03
  Scenario: Developer uses both load paths
    When the developer runs "make ram" with the board in download mode
    Then the monitor prompt appears
    When the developer runs "make flash" and resets the board
    Then the monitor prompt appears after every reset

  @qemu @EP-03 @STK-05 @STK-19 @VER-STK-04
  Scenario: Operator gets a console that keeps pasted input
    When the operator opens a terminal at 115200 8N1 and resets the board
    Then the banner and "> " are shown
    When the operator pastes 20 commands while the self test runs
    Then all 20 are answered

  @qemu @EP-04 @STK-06 @VER-STK-05
  Scenario: Operator inspects and modifies memory
    When the operator enters "h", "w 3ffb1000 cafe", "r 3ffb1000", "d 3ffb0000" and "g <gpio_init>"
    Then each command answers in its documented format
    When the operator enters "r 3ffb0002"
    Then the console shows "?? (h for help)"

  @hardware @pending @EP-05 @STK-07 @STK-16 @VER-STK-06
  Scenario: Operator drives pins and sees a blink
    When the operator enters "p 2 1" and "p 2 0"
    Then the LED on GPIO2 follows
    When the operator enters "p 7 1"
    Then the command is refused
    When the blink build is flashed
    Then the LED blinks at about 1 Hz

  @qemu @EP-06 @STK-08 @STK-09 @VER-STK-07
  Scenario: Integrator attaches handlers and uses the tick
    When the operator enters "s" and then "i"
    Then the software interrupt handler ran once
    And lines 6 and 17 are counting

  @qemu @EP-07 @STK-10 @VER-STK-08
  Scenario: Developer reads a crash report and reboots
    When the developer enters "f 0"
    Then the report names "LoadProhibited" and the PC maps to fault() in mimmo.c
    When the developer presses a key
    Then the board reboots with "rst:0x3 (SW_RESET)"

  @qemu @EP-06 @STK-11 @VER-STK-09
  Scenario: Developer relies on ordinary C semantics
    When the developer enters "s"
    Then deep recursion and the variable-length array both report "ok"

  @hardware @pending @EP-02 @STK-12 @VER-STK-10
  Scenario: Operator leaves the board running
    When the board idles at the prompt for 10 minutes
    Then it has not reset

  @qemu @EP-08 @STK-13 @STK-14 @VER-STK-11
  Scenario: Tester verifies without hardware
    When the tester runs "make qemu" and enters "s" and "f 0" to "f 5"
    Then the self test reports "all ok"
    And every fault is reported and followed by a reboot

  @host @EP-09 @STK-15 @STK-20 @VER-STK-12
  Scenario: Learner and maintainer use the documentation
    When the learner reads README.md
    Then boot, memory map, vectors, interrupts, faults and the LPC1343 mapping are explained
    When the maintainer runs "python3 tools/tracecheck.py --check"
    Then it reports 0 errors

  @hardware @pending @EP-02 @STK-17 @VER-STK-13
  Scenario: Developer uses the cheapest board
    Given an ESP32-WROOM-32 DevKit without PSRAM
    When the developer flashes e32 and enters "s"
    Then the self test reports "all ok"
