@EP-05 @FEAT-048
Feature: FEAT-048: Blink mode
  Epic: EP-05 GPIO control   ·   Level: unit

  Supports: US-17 via CMP-32

  @CMP-32
  Rule: CMP-32: main.c: main
    EARS: When `main()` is called, it shall print the banner and memory lines, call `irq_init`, `timer_init(HZ)` and `serial_irq_init(17)`, then run `mimmo()`. In blink mode it shall instead run the `LED_GPIO` toggle loop (500 ms, printing `led N`). It never returns.

    @qemu @SYS-22 @SW-MON-07 @VER-SYS-18
    Scenario: CMP-32-S01: The LED state alternates every half second
      Given a build variant with "if (1)" changed to "if (0)" in main.c
      When the firmware is booted in QEMU from flash
      And I wait 4 seconds
      Then the console shows at least 6 lines alternating "led 0" and "led 1"

    @host @gtest @VER-CMP-16
    Scenario: CMP-32-S02: main prints the banner, starts interrupts and enters the monitor
      When main runs until the monitor waits for input
      Then the console shows a line starting with "e32: bare-metal ESP32, built "
      And the console shows a line starting with "bss 0x"
      And the console shows "mimmo.c: Ready to get input (h for help)"
      And CPU lines 6 and 17 are enabled
      And interrupt matrix source 34 is routed to line 17
