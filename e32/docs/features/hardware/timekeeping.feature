@EP-06 @FEAT-062
Feature: FEAT-062: Timekeeping
  Epic: EP-06 Exception and interrupt handling   ·   Level: hardware

  Supports: US-20 via HW-02

  @HW-02
  Rule: HW-02: Crystal
    EARS: The board shall use a 40 MHz crystal, so that the ROM's UART0 set-up gives 115200 baud and `CPU_HZ` = 40 MHz holds while the CPU runs from the crystal.

    @hardware @pending @SYS-17 @VER-SYS-13
    Scenario: HW-02-S01: Uptime follows wall-clock time on a board
      Given the firmware is running on a board
      When I enter "i" and start a stopwatch
      And I enter "i" again after 60 stopwatch seconds
      Then the uptime difference is between 59.4 and 60.6 seconds
