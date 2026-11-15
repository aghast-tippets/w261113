@EP-05 @FEAT-041
Feature: FEAT-041: GPIO control
  Epic: EP-05 GPIO control   ·   Level: subsystem

  Supports: US-15 via SUB-GPIO-01
  Supports: US-16 via STK-07 → SYS-14 → SUB-GPIO-02

  @SUB-GPIO-01
  Rule: SUB-GPIO-01: Pin configuration and access
    EARS: The GPIO subsystem shall configure any valid pad, numbered 0–39, as a GPIO input or output or select one of its alternate functions 0–5 (0 always being GPIO), and set and read GPIO levels.

    @qemu @SYS-12 @SYS-13 @VER-SYS-09
    Scenario: SUB-GPIO-01-S01: GPIO command paths in the emulator
      Given the firmware is booted in QEMU from flash
      When I enter "p 2 1"
      Then the console shows "gpio 2 <- 1"
      When I enter "p 34"
      Then the console shows a line matching /^gpio 34 = [01]$/
      When I enter "a 2 3"
      Then the console shows "gpio 2: function 3"

  @SUB-GPIO-02
  Rule: SUB-GPIO-02: Pin protection
    EARS: If a pin does not exist, is connected to the flash (6–11), or is input-only (34–39) when output is requested, or the function number is outside 0–5, then the GPIO subsystem shall return an error without writing any register.
