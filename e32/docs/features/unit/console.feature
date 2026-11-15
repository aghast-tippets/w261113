@EP-03 @FEAT-030
Feature: FEAT-030: Console I/O
  Epic: EP-03 Console input and output   ·   Level: unit

  Supports: US-09 via STK-05 → SYS-06 → SUB-CON-01 → SW-CON-02 → CMP-15
  Supports: US-10 via CMP-16
  Supports: US-11 via STK-05 → SYS-06 → SUB-CON-01 → SW-CON-02 → CMP-15

  @CMP-15
  Rule: CMP-15: io.c: putc, puts
    EARS: When `putc(c)` is called with `c` = `'\n'`, it shall call `putc('\r')` first. It shall then spin while `TXCNT(STATUS)` ≥ 126 and write `c & 0xFF` to the FIFO. `puts(s)` shall call `putc` for each character of `s`, without adding a newline.

    @qemu @SUB-CON-01 @SW-CON-02 @VER-SUB-13
    Scenario: CMP-15-S01: Output lines end with CR LF
      When the firmware is booted in QEMU from flash
      Then every line the firmware prints ends with the bytes 0d 0a

    @host @gtest @VER-CMP-10
    Scenario: CMP-15-S02: Newline is sent as CR LF
      Given the UART transmit FIFO is empty
      When the firmware calls puts with "ok\n"
      Then the UART transmits the bytes 6f 6b 0d 0a

    @host @gtest @VER-CMP-10
    Scenario: CMP-15-S03: putc waits while the transmit FIFO is nearly full
      Given the UART transmit FIFO holds 126 bytes for the next 3 status reads
      When the firmware calls putc with "A"
      Then the status register was read at least 4 times before the FIFO write
      And the UART transmits the byte 41

  @CMP-16
  Rule: CMP-16: io.c: getc, gets
    EARS: While `rx_irq_mode` is 0, `getc` shall poll the FIFO. While it is 1, `getc` shall apply the SW-CON-06 loop. `gets(s, size)` shall implement SW-CON-03. Precondition: `size` ≥ 1. Postcondition: `s` is NUL-terminated, and its length is at most `size − 1`.

    @qemu @SUB-CON-02 @SW-CON-03 @VER-SUB-13 @VER-SW-04
    Scenario: CMP-16-S01: Backspace erases the last character
      Given the monitor prompt is shown
      When I send the bytes "r 3ffb0001" 08 "0" 0d
      Then the console shows "read 3ffb0000"

    @host @gtest @VER-CMP-10
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

    @host @gtest @CMP-17 @VER-CMP-10
    Scenario: CMP-16-S03: getc sleeps until the UART interrupt brings a byte
      Given serial_irq_init was called with line 17
      And the UART receives "x" while the CPU is waiting for an interrupt
      When the firmware calls getc
      Then it returns "x"
      And the CPU executed waiti at least once
      And interrupt line 17 was dispatched once

  @CMP-17
  Rule: CMP-17: io.c: serial_irq_init, uart_rx_irq
    EARS: When `serial_irq_init(irq)` is called, it shall perform the SW-CON-04 steps and set `rx_irq_mode` = 1 before enabling the line. When `uart_rx_irq` runs, it shall store bytes while `rx_head − rx_tail` < 256, otherwise increment `rx_overruns`, and finally write `RXFIFO_FULL` to `INT_CLR`.

    @qemu @SYS-18 @SUB-CON-03 @SW-CON-04 @SW-CON-05 @SW-CON-06 @VER-SYS-14 @VER-STK-04 @VER-SUB-13
    Scenario: CMP-17-S01: Input typed while busy is kept
      Given the monitor prompt is shown
      When I enter "s"
      And I immediately enter "r 3ffb1000" 20 times
      Then the console shows "read 3ffb1000" 20 times

    @host @gtest @VER-CMP-10
    Scenario: CMP-17-S02: serial_irq_init routes UART0 to a CPU line
      When the firmware calls serial_irq_init with line 17
      Then UART_CONF1 has a receive threshold of 1
      And UART_INT_CLR was written with ffffffff before UART_INT_ENA was written with 1
      And interrupt matrix source 34 is routed to line 17
      And CPU line 17 is enabled

    @host @gtest @VER-CMP-10
    Scenario: CMP-17-S03: Bytes beyond the 256-byte ring are dropped
      Given serial_irq_init was called with line 17
      When 300 bytes arrive before the firmware reads any
      Then the next 256 calls to getc return the first 256 bytes in order
      And the 257th call to getc waits for new input instead of returning a dropped byte
