@EP-03 @F-06
Feature: io.c unit behaviour
  Unit level (CMP). io.c is compiled for the host and runs against a
  simulated UART0 and CPU; the GoogleTest suite implements these scenarios.

  @host @CMP-15 @VER-CMP-10
  Scenario: CMP-15-S02: Newline is sent as CR LF
    Given the UART transmit FIFO is empty
    When the firmware calls puts with "ok\n"
    Then the UART transmits the bytes 6f 6b 0d 0a

  @host @CMP-15 @VER-CMP-10
  Scenario: CMP-15-S03: putc waits while the transmit FIFO is nearly full
    Given the UART transmit FIFO holds 126 bytes for the next 3 status reads
    When the firmware calls putc with "A"
    Then the status register was read at least 4 times before the FIFO write
    And the UART transmits the byte 41

  @host @CMP-18 @VER-CMP-10
  Scenario: CMP-18-S02: serial_setup waits for the ROM's output to drain
    Given the UART transmit FIFO holds 5 bytes for the next 2 status reads
    When the firmware calls serial_setup
    Then the status register was read 3 times
    And no UART register was written

  @host @CMP-16 @VER-CMP-10
  Scenario Outline: CMP-16-S02: Line editing in gets
    Given the UART receives the bytes <input>
    When the firmware calls gets with a buffer of <size> bytes
    Then the line read is "<line>"
    And the echo is <echo>

    Examples:
      | input                    | size | line | echo                      |
      | "ab" 0d                  | 80   | ab   | "ab" 0d 0a                |
      | "ab" 08 "c" 0d           | 80   | ac   | "ab" 08 20 08 "c" 0d 0a   |
      | "ab" 7f 7f 7f "c" 0d     | 80   | c    | "ab" 08 20 08 08 20 08 "c" 0d 0a |
      | "a" 01 1b "b" 0a         | 80   | ab   | "ab" 0d 0a                |
      | "abcdef" 0d              | 4    | abc  | "abc" 0d 0a               |

  @host @CMP-17 @VER-CMP-10
  Scenario: CMP-17-S02: serial_irq_init routes UART0 to a CPU line
    When the firmware calls serial_irq_init with line 17
    Then UART_CONF1 has a receive threshold of 1
    And UART_INT_CLR was written with ffffffff before UART_INT_ENA was written with 1
    And interrupt matrix source 34 is routed to line 17
    And CPU line 17 is enabled

  @host @CMP-16 @CMP-17 @VER-CMP-10
  Scenario: CMP-16-S03: getc sleeps until the UART interrupt brings a byte
    Given serial_irq_init was called with line 17
    And the UART receives "x" while the CPU is waiting for an interrupt
    When the firmware calls getc
    Then it returns "x"
    And the CPU executed waiti at least once
    And interrupt line 17 was dispatched once

  @host @CMP-17 @VER-CMP-10
  Scenario: CMP-17-S03: Bytes beyond the 256-byte ring are dropped
    Given serial_irq_init was called with line 17
    When 300 bytes arrive before the firmware reads any
    Then the next 256 calls to getc return the first 256 bytes in order
    And the 257th call to getc waits for new input instead of returning a dropped byte
