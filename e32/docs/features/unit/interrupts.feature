@EP-06 @FEAT-059
Feature: FEAT-059: Interrupts
  Epic: EP-06 Exception and interrupt handling   ·   Level: unit

  Supports: US-19 via CMP-08

  @CMP-08
  Rule: CMP-08: vectors.S: _level1_handler
    EARS: When entered with `EXCCAUSE` = 4, the handler shall carry out the SW-EXC-03 sequence using the IF-06 frame, and return with `rfe` with every saved register, `EPC1`, `PS`, `SAR`, `LBEG`, `LEND` and `LCOUNT` restored to its value at entry.

    @qemu @SYS-16 @SUB-EXC-03 @SW-EXC-02 @SW-EXC-03 @VER-SYS-12 @VER-SUB-10
    Scenario: CMP-08-S01: Heavy interrupt load leaves computations intact
      Given a build variant with timer_init(20000) and the stress command "S"
      When the firmware is booted in QEMU from flash
      And I enter "S"
      Then the console shows "stress: 0 bad"
      And "irq 6" counts more than 100000 interrupts in total

  @CMP-10
  Rule: CMP-10: irq.c: irq_init, irq_map
    EARS: When `irq_init()` is called, it shall write 6 to every `PRO_INTR_MAP(0..68)`, set `INTENABLE` = 0 and `INTCLEAR` = `0xFFFFFFFF`. `irq_map(s, n)` shall write n to `PRO_INTR_MAP(s)`.

    @qemu @pending @SW-EXC-05 @VER-SW-09
    Scenario: CMP-10-S01: Initialisation disconnects every matrix source
      Given the firmware is booted in QEMU from flash
      When I enter "d 3ff00104 45"
      Then every word except the one at 3ff0018c (UART0, 00000011) is 00000006

    @host @gtest @VER-CMP-07
    Scenario: CMP-10-S02: irq_init disconnects every interrupt matrix source
      Given interrupt matrix source 34 is routed to line 17 and INTENABLE is 00020040
      When the firmware calls irq_init
      Then all 69 sources from 3ff00104 to 3ff00214 are routed to line 6
      And INTENABLE is 00000000
      And INTCLEAR was written with ffffffff

    @host @gtest @VER-CMP-07
    Scenario: CMP-10-S03: irq_map writes one matrix register
      When the firmware calls irq_map with source 34 and line 17
      Then 00000011 is written to 3ff0018c and nothing else is written

  @CMP-11
  Rule: CMP-11: irq.c: irq_request, irq_enable, irq_disable, irq_count
    EARS: If `irq_request` is called with `irq` ∉ [0, 31] or with `(1<<irq) & 0x000637FF` = 0, then it shall return −1 and change nothing. Otherwise it shall store `fn` and `arg` in the line's descriptor, set `INTENABLE` bit `irq` under `irq_save`, and return 0. `irq_count(n)` shall return the dispatch count of line `n & 31`.

    @qemu @pending @SW-EXC-06 @VER-SW-09
    Scenario Outline: CMP-11-S01: Only level-1 lines can be requested
      Given a build variant that prints the result of irq_request(<line>, handler, 0)
      When the firmware is booted in QEMU from flash
      Then the console shows "irq_request(<line>) = <result>"

      Examples:
        | line | result |
        | 17   | 0      |
        | 11   | -1     |
        | 19   | -1     |
        | 32   | -1     |
        | -1   | -1     |

    @host @gtest @VER-CMP-07
    Scenario Outline: CMP-11-S02: Only level-1 lines can be requested
      Given INTENABLE is 00000000
      When the firmware calls irq_request with line <line>
      Then it returns <result>
      And INTENABLE is <intenable>

      Examples:
        | line | result | intenable |
        | 0    | 0      | 00000001  |
        | 13   | 0      | 00002000  |
        | 17   | 0      | 00020000  |
        | 11   | -1     | 00000000  |
        | 19   | -1     | 00000000  |
        | 29   | -1     | 00000000  |
        | 32   | -1     | 00000000  |
        | -1   | -1     | 00000000  |

  @CMP-12
  Rule: CMP-12: irq.c: irq_dispatch
    EARS: While `INTERRUPT & INTENABLE & 0x000637FF` is non-zero, `irq_dispatch` shall pick n = ctz(pending). If bit n is in `0x480`, it shall write it to `INTCLEAR`. It shall then increment `count[n]` and call `fn(n, arg)`, or, if there is no `fn`, clear `INTENABLE` bit n and print `irq n: no handler, disabled`.

    @qemu @pending @SW-EXC-08 @VER-SW-09
    Scenario: CMP-12-S01: An enabled line without a handler is disabled
      Given a build variant that enables CPU line 9 without a handler and raises it
      When the firmware is booted in QEMU from flash
      Then the console shows "irq 9: no handler, disabled"
      And the monitor prompt is shown

    @host @gtest @VER-CMP-07
    Scenario: CMP-12-S02: Pending handlers run lowest line first and latched lines are cleared
      Given handlers are installed on lines 7 and 17
      And lines 7 and 17 are both pending
      When the CPU takes a level-1 interrupt
      Then the handler for line 7 runs before the handler for line 17
      And INTCLEAR was written with 00000080 and never with 00020000
      And irq_count reports one more interrupt on each line

    @host @gtest @VER-CMP-07
    Scenario: CMP-12-S03: A pending line without a handler is disabled
      Given line 9 is enabled without a handler and pending
      When the CPU takes a level-1 interrupt
      Then the console shows "irq 9: no handler, disabled"
      And INTENABLE bit 9 is 0
