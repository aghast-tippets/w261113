@EP-03 @FEAT-026
Feature: FEAT-026: Console I/O
  Epic: EP-03 Console input and output   ·   Level: system

  User stories delivered:
    US-09  As an operator, I want a banner and a prompt at 115200 8N1 when the
           board starts, so that I know it is alive and ready.
    US-10  As an operator, I want to correct typing with backspace and to paste
           lines while the firmware is busy, so that no input is lost or mangled.
    US-11  As an integrator, I want a `printf` with the common integer, string
           and pointer conversions, so that application output is easy to write.

  Actors: Firmware developer (ACT-H1, persona "dana"), Bench operator /
    tester (ACT-H3, persona "olga")

  @SYS-06
  Rule: SYS-06: Start-up banner and prompt
    EARS: When the e32 firmware starts, it shall print on UART0 a banner with the program name and build date and time, a line with the BSS range and stack top, the line `mimmo.c: Ready to get input (h for help)` and the prompt `> `.

  @SYS-07
  Rule: SYS-07: Serial line parameters
    EARS: The e32 firmware shall use UART0 with the bit rate and frame format configured by the boot ROM, which is 115200 baud 8N1 with a 40 MHz crystal.

    @hardware @pending @SYS-18 @VER-SYS-06 @VER-SYS-14
    Scenario: SYS-07-S01: Line parameters and buffering on a board
      Given the firmware is running on a board
      And a terminal on PORT at 115200 baud, 8 data bits, no parity, 1 stop bit
      When I reset the board
      Then the banner is readable
      When I paste 200 characters of commands while "s" runs
      Then every pasted command is answered

  @SYS-18
  Rule: SYS-18: Receive buffering
    EARS: While console receive interrupts are enabled, the e32 firmware shall retain up to 256 received characters not yet read by the application, in addition to the UART's hardware FIFO.
