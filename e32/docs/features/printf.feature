@EP-03 @F-07
Feature: Formatted output
  As an integrator
  I want printf and sprintf with the common conversions
  So that output is as easy as in hosted C

  # Host unit test: pp_printf.c is compiled natively with a stub putc,
  # and pp_sprintf is compared with the C library's snprintf.

  @host @SUB-CON-04 @SW-FMT-01 @SW-FMT-02 @CMP-19 @CMP-20 @VER-CMP-11 @VER-SUB-14
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

  @host @pending @SW-FMT-01 @VER-CMP-11
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

  @qemu @SW-FMT-01 @SW-FMT-02 @VER-SUB-14
  Scenario: SW-FMT-01-S02: Pointer and padded formats on the target
    When the firmware is booted in QEMU from flash
    Then the console shows "stack top 0x3ffdc000"
    When I enter "f 0"
    Then the console shows a line matching /^a0  [0-9a-f]{8}  a1  [0-9a-f]{8}  a2  [0-9a-f]{8}  a3  [0-9a-f]{8}$/
