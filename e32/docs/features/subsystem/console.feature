@EP-03 @FEAT-027
Feature: FEAT-027: Console I/O
  Epic: EP-03 Console input and output   ·   Level: subsystem

  Supports: US-09 via STK-05 → SYS-06 → SUB-CON-01
  Supports: US-10 via STK-19 → SYS-18 → SUB-CON-03
  Supports: US-11 via STK-05 → SYS-06 → SUB-CON-01
  Supports: US-12 via SYS-10 → SUB-CON-02
  Supports: US-14 via SYS-10 → SUB-CON-02

  @SUB-CON-01
  Rule: SUB-CON-01: Output
    EARS: The console subsystem shall transmit characters on UART0, translating each LF into CR LF.

  @SUB-CON-02
  Rule: SUB-CON-02: Line input
    EARS: When a line is requested, the console subsystem shall read characters with echo and backspace editing until CR or LF is received.

  @SUB-CON-03
  Rule: SUB-CON-03: Interrupt-driven receive
    EARS: While receive interrupt mode is enabled, the console subsystem shall move received bytes from the UART FIFO into a 256-byte ring buffer from the interrupt handler, and the reader shall sleep until data is available.
