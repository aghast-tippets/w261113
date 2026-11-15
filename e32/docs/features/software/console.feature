@EP-03 @FEAT-028
Feature: FEAT-028: Console I/O
  Epic: EP-03 Console input and output   ·   Level: software

  Supports: US-09 via STK-05 → SYS-06 → SUB-CON-01 → SW-CON-02
  Supports: US-10 via STK-19 → SYS-18 → SUB-CON-03 → SW-CON-05
  Supports: US-11 via STK-05 → SYS-06 → SUB-CON-01 → SW-CON-02
  Supports: US-12 via SYS-10 → SUB-CON-02 → SW-CON-03
  Supports: US-14 via SYS-10 → SUB-CON-02 → SW-CON-03

  @SW-CON-02
  Rule: SW-CON-02: putc
    EARS: `putc` shall wait while the transmit FIFO holds 126 or more bytes, emit CR before every LF, and write each byte to the FIFO register only after reading the status register.

  @SW-CON-03
  Rule: SW-CON-03: gets
    EARS: `gets(s, size)` shall handle each received character as follows:
      - On CR or LF, echo a newline and end the line.
      - On BS (`0x08`) or DEL (`0x7F`), remove the last stored character, if any, and echo `"\b \b"`.
      - Ignore any other character below `0x20`, and any character beyond `size − 1`.
      - Store and echo every other character.
      It shall NUL-terminate the result and return its length.

    @qemu @pending @VER-SW-04
    Scenario: SW-CON-03-S01: Control characters are ignored
      Given the monitor prompt is shown
      When I send the bytes "r 3ffb" 01 "0000" 0d
      Then the console shows "read 3ffb0000"

    @qemu @pending @VER-SW-04
    Scenario: SW-CON-03-S02: Overlong lines are truncated at 79 characters
      Given the monitor prompt is shown
      When I send "h" followed by 84 spaces and 0d
      Then the console echoes 79 characters before the newline
      And the console shows "r <addr>"

    @qemu @pending @SW-CON-07 @VER-SW-04
    Scenario: SW-CON-03-S03: LF also ends a line
      Given the monitor prompt is shown
      When I send the bytes "h" 0a
      Then the console shows "r <addr>"

  @SW-CON-05
  Rule: SW-CON-05: Receive handler
    EARS: When the UART0 interrupt runs, the handler shall drain the RX FIFO into the 256-byte ring buffer, count each byte dropped because the buffer is full as an overrun, and then clear `RXFIFO_FULL`.

    @qemu @pending @VER-SW-05
    Scenario: SW-CON-05-S01: Overruns are counted when the ring is full
      Given a build variant with RXBUF_SIZE set to 4
      And the monitor prompt is shown
      When I send 64 characters while "s" runs
      Then "rx_overruns" read with "r" is greater than 0

  @SW-CON-07
  Rule: SW-CON-07: Polled getc
    EARS: While interrupt receive is not enabled, `getc` shall poll the RX FIFO count and return the first byte read.
