@EP-04 @F-08
Feature: mimmo.c, panic.c and main.c unit behaviour
  Unit level (CMP). The monitor, fault reporter and main are compiled for
  the host and run against a simulated UART, bus and CPU; the GoogleTest
  suite implements these scenarios.

  @host @CMP-24 @VER-CMP-13
  Scenario Outline: CMP-24-S02: Numbers are parsed strictly
    Given memory word 3ffb1000 holds 0000cafe
    When the operator enters "<line>"
    Then the console shows "<reply>"

    Examples:
      | line            | reply         |
      | r 3ffb1000      | read 3ffb1000 |
      | r 0x3ffb1000    | read 3ffb1000 |
      | r 0X3FFB1000    | read 3ffb1000 |
      | r   3ffb1000    | read 3ffb1000 |
      | r 3ffb100g      | ?? (h for help) |
      | r 0x            | ?? (h for help) |
      | r 3ffb1000x     | ?? (h for help) |
      | p 1a            | ?? (h for help) |
      | p 0x2           | ?? (h for help) |

  @host @CMP-25 @VER-CMP-13
  Scenario: CMP-25-S01: Read, write and dump answer in their documented formats
    Given memory words 3ffb2000 to 3ffb201c hold 00000000 to 00000007
    When the operator enters "w 3ffb2000 cafe", "r 3ffb2000" and "d 3ffb2000 8"
    Then the console shows exactly:
      """
      write 3ffb2000 = 0000cafe
      read 3ffb2000
      0000cafe
      3ffb2000: 0000cafe 00000001 00000002 00000003
      3ffb2010: 00000004 00000005 00000006 00000007
      """

  @host @CMP-25 @VER-CMP-13
  Scenario Outline: CMP-25-S02: GPIO commands report their outcome
    Given GPIO_IN reads 00000010
    When the operator enters "<line>"
    Then the console shows "<reply>"

    Examples:
      | line   | reply                                                 |
      | p 2 1  | gpio 2 <- 1                                           |
      | p 2 5  | gpio 2 <- 1                                           |
      | p 4    | gpio 4 = 1                                            |
      | p 5    | gpio 5 = 0                                            |
      | p 7 1  | invalid gpio (6..11 are flash, 34..39 are input only) |
      | a 2 3  | gpio 2: function 3                                    |
      | a 2 6  | invalid gpio or function                              |

  @host @CMP-25 @VER-CMP-13
  Scenario: CMP-25-S03: The prompt is printed before every read and blank lines are ignored
    When the operator enters "", "   " and "h"
    Then the console shows the prompt "> " 4 times
    And the console does not show "??"
    And the console shows "h                     this help"

  @host @CMP-26 @VER-CMP-13
  Scenario: CMP-26-S02: The self test passes on the simulated CPU
    Given the 100 Hz tick is running
    When the operator enters "s"
    Then the console shows "recursion 200 deep: 20100 (ok)"
    And the console shows "VLA after spill:   919 (ok)"
    And the console shows "software irq:      1 hit (ok)"
    And the console shows "all ok"
    And CPU line 7 is disabled afterwards

  @host @CMP-28 @VER-CMP-14
  Scenario Outline: CMP-28-S01: The fault report names the cause and the registers
    Given a panic frame of kind <kind> with cause <cause>, EPC1 400815db, DEPC 40081000 and a0 80081658
    When panic_handler runs
    Then the console shows "<heading>"
    And the console shows "<pc line>"
    And the console shows "called from ~40081658"
    And the console shows "Press any key to reboot"

    Examples:
      | kind | cause | heading                                      | pc line                                         |
      | 1    | 28    | *** Fatal exception 28: LoadProhibited       | pc  400815db  ps  00060530  excvaddr 00000000   |
      | 1    | 0     | *** Fatal exception 0: IllegalInstruction    | pc  400815db  ps  00060530                      |
      | 1    | 6     | *** Fatal exception 6: IntegerDivideByZero   | pc  400815db  ps  00060530                      |
      | 2    | 29    | *** Kernel exception 29: StoreProhibited     | pc  400815db  ps  00060530  excvaddr 00000000   |
      | 3    | 29    | *** Double exception (cause 29 while handling an exception at 400815db) | pc  40081000  ps  00060530  excvaddr 00000000 |

  @host @CMP-28 @VER-CMP-14
  Scenario: CMP-28-S02: A high-level interrupt reports its level and the pending lines
    Given a panic frame of kind 19 (level 3) with EPC3 40082000 and EPS3 00060023
    And the INTERRUPT register reads 20000000
    When panic_handler runs
    Then the console shows "*** Unexpected high-level interrupt"
    And the console shows "    level 3, pending 20000000"
    And the console shows "pc  40082000  ps  00060023"

  @host @CMP-29 @VER-CMP-14
  Scenario: CMP-29-S02: A key press after the report reboots the chip
    Given a panic frame of kind 1 with cause 0
    And the UART will receive "q" after the report
    When panic_handler runs
    Then 80000000 is written to RTC_CNTL_OPTIONS0 at 3ff48000
    And nothing is written after it

  @host @CMP-32 @VER-CMP-16
  Scenario: CMP-32-S02: main prints the banner, starts interrupts and enters the monitor
    When main runs until the monitor waits for input
    Then the console shows a line starting with "e32: bare-metal ESP32, built "
    And the console shows a line starting with "bss 0x"
    And the console shows "mimmo.c: Ready to get input (h for help)"
    And CPU lines 6 and 17 are enabled
    And interrupt matrix source 34 is routed to line 17
