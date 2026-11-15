@EP-03 @FEAT-032
Feature: FEAT-032: Formatted output
  Epic: EP-03 Console input and output   ·   Level: software

  Supports: US-09 via STK-05 → SYS-06 → SUB-CON-04 → SW-FMT-02
  Supports: US-11 via SW-FMT-01
  Supports: US-12 via SYS-10 → SUB-CON-04 → SW-FMT-02
  Supports: US-14 via SYS-10 → SUB-CON-04 → SW-FMT-02
  Supports: US-22 via SYS-19 → SUB-CON-04 → SW-FMT-02

  # Host unit test: pp_printf.c is compiled natively with a stub putc,
  # and pp_sprintf is compared with the C library's snprintf.

  @SW-FMT-01
  Rule: SW-FMT-01: Conversion semantics
    EARS: The formatter shall render `%d %i %u %x %X %s %c %%`, the `-` and `0` flags and the field width as ISO C does, and handle these cases as follows:
      - accept and ignore the length modifiers `l`, `h` and `z`;
      - print `%p` as `0x` followed by 8 hex digits;
      - print a NULL `%s` argument as `(null)`;
      - print an unknown conversion character verbatim;
      - return the number of characters produced.

    @host @pending @VER-CMP-11
    Scenario Outline: SW-FMT-01-S01: Cases that differ from or extend ISO C
      Given pp_printf.c compiled for the host
      When I format <format> with <arguments>
      Then the result is <result>

      Examples:
        | format  | arguments  | result         |
        | "%s"    | NULL       | "(null)"       |
        | "%p"    | 0x3ffb0000 | "0x3ffb0000"   |
        | "%p"    | 0x10       | "0x00000010"   |
        | "%q"    | none       | "q"            |
        | "abc%"  | none       | "abc"          |

    @qemu @SW-FMT-02 @VER-SUB-14
    Scenario: SW-FMT-01-S02: Pointer and padded formats on the target
      When the firmware is booted in QEMU from flash
      Then the console shows "stack top 0x3ffdc000"
      When I enter "f 0"
      Then the console shows a line matching /^a0  [0-9a-f]{8}  a1  [0-9a-f]{8}  a2  [0-9a-f]{8}  a3  [0-9a-f]{8}$/

  @SW-FMT-02
  Rule: SW-FMT-02: Unbuffered printf, terminated sprintf
    EARS: `pp_printf` shall pass each character to `putc` without an intermediate buffer, and `pp_sprintf` shall NUL-terminate its output.
