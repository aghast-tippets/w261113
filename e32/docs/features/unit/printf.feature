@EP-03 @FEAT-033
Feature: FEAT-033: Formatted output
  Epic: EP-03 Console input and output   ·   Level: unit

  Supports: US-09 via STK-05 → SYS-06 → SUB-CON-04 → SW-FMT-02 → CMP-20
  Supports: US-11 via CMP-19
  Supports: US-12 via SYS-10 → SUB-CON-04 → SW-FMT-02 → CMP-20
  Supports: US-14 via SYS-10 → SUB-CON-04 → SW-FMT-02 → CMP-20
  Supports: US-22 via SYS-19 → SUB-CON-04 → SW-FMT-02 → CMP-20

  # Host unit test: pp_printf.c is compiled natively with a stub putc,
  # and pp_sprintf is compared with the C library's snprintf.

  @CMP-19
  Rule: CMP-19: pp_printf.c: formatter core
    EARS: `pp_format(out, arg, fmt, ap)` shall emit, through `out`, the same characters that ISO C `printf` produces for the SW-FMT-01 subset, and return their count. `emit_padded` shall place the sign before zero padding and after space padding.

    @host @SUB-CON-04 @SW-FMT-01 @SW-FMT-02 @CMP-20 @VER-CMP-11 @VER-SUB-14
    Scenario Outline: CMP-19-S01: pp_sprintf matches ISO C for the supported subset
      Given pp_printf.c compiled for the host
      When I format <format> with <arguments>
      Then pp_sprintf produces the same string as snprintf
      And it returns the same length

      Examples:
        | format                 | arguments                     |
        | "%d %i %u"             | -42, 0, 3000000000            |
        | "%x %X %08x"           | 0xdeadbeef, 0xabc, 0x12       |
        | "%8x\|%-8x\|"          | 0x12, 0x12                    |
        | "%5d\|%-5d\|%05d\|%-05d\|" | -3, -3, -3, -3            |
        | "%s\|%10s\|%-10s\|"    | "hi", "hi", "hi"              |
        | "%c%%"                 | 'z'                           |
        | "%lu %ld %zu"          | 7, -7, 9                      |
        | "%d"                   | -2147483648                   |
        | "%u"                   | 0                             |
        | "%-3c\|"               | 'a'                           |

  @CMP-20
  Rule: CMP-20: pp_printf.c: pp_printf, pp_sprintf
    EARS: `pp_printf` shall call `pp_format` with a `putc` sink. `pp_sprintf(buf, …)` shall write into `buf` and NUL-terminate it. Precondition: `buf` is large enough. Both shall return the character count, excluding the NUL.

    @host @gtest @VER-CMP-11
    Scenario: CMP-20-S01: pp_printf sends its output through putc and returns its length
      When the firmware calls pp_printf with "x=%d\n" and 42
      Then it returns 5
      And the UART transmits the bytes "x=42" 0d 0a
