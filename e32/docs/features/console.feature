@EP-03 @F-06
Feature: Console input and output
  As an operator
  I want a dependable serial console
  So that I can talk to the firmware without losing characters

  @qemu @SYS-06 @IF-03 @VER-SYS-06 @VER-STK-04
  Scenario: Banner and prompt after boot
    When the firmware is booted in QEMU from flash
    Then the console shows a line matching /^e32: bare-metal ESP32, built \w{3} [ \d]\d \d{4} \d\d:\d\d:\d\d$/
    And the console shows a line matching /^bss 0x3ffb[0-9a-f]{4}-0x3ffb[0-9a-f]{4}, stack top 0x3ffdc000$/
    And the console shows "mimmo.c: Ready to get input (h for help)"
    And the console shows "> "

  @qemu @SUB-CON-01 @SW-CON-02 @CMP-15 @VER-SUB-13
  Scenario: Output lines end with CR LF
    When the firmware is booted in QEMU from flash
    Then every line the firmware prints ends with the bytes 0d 0a

  @qemu @SUB-CON-02 @SW-CON-03 @CMP-16 @VER-SUB-13 @VER-SW-04
  Scenario: Backspace erases the last character
    Given the monitor prompt is shown
    When I send the bytes "r 3ffb0001" 08 "0" 0d
    Then the console shows "read 3ffb0000"

  @qemu @pending @SW-CON-03 @VER-SW-04
  Scenario: Control characters are ignored
    Given the monitor prompt is shown
    When I send the bytes "r 3ffb" 01 "0000" 0d
    Then the console shows "read 3ffb0000"

  @qemu @pending @SW-CON-03 @VER-SW-04
  Scenario: Overlong lines are truncated at 79 characters
    Given the monitor prompt is shown
    When I send "h" followed by 84 spaces and 0d
    Then the console echoes 79 characters before the newline
    And the console shows "r <addr>"

  @qemu @pending @SW-CON-03 @SW-CON-07 @VER-SW-04
  Scenario: LF also ends a line
    Given the monitor prompt is shown
    When I send the bytes "h" 0a
    Then the console shows "r <addr>"

  @qemu @SYS-18 @SUB-CON-03 @SW-CON-04 @SW-CON-05 @SW-CON-06 @CMP-17 @VER-SYS-14 @VER-STK-04 @VER-SUB-13
  Scenario: Input typed while busy is kept
    Given the monitor prompt is shown
    When I enter "s"
    And I immediately enter "r 3ffb1000" 20 times
    Then the console shows "read 3ffb1000" 20 times

  @hardware @pending @SYS-07 @SYS-18 @VER-SYS-06 @VER-SYS-14
  Scenario: Line parameters and buffering on a board
    Given the firmware is running on a board
    And a terminal on PORT at 115200 baud, 8 data bits, no parity, 1 stop bit
    When I reset the board
    Then the banner is readable
    When I paste 200 characters of commands while "s" runs
    Then every pasted command is answered

  @qemu @pending @SW-CON-05 @VER-SW-05
  Scenario: Overruns are counted when the ring is full
    Given a build variant with RXBUF_SIZE set to 4
    And the monitor prompt is shown
    When I send 64 characters while "s" runs
    Then "rx_overruns" read with "r" is greater than 0
