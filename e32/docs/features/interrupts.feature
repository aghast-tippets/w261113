@EP-06 @F-12
Feature: Interrupts
  As an integrator
  I want to route sources to CPU lines and attach C handlers
  So that my code reacts to events without touching the vectors

  @qemu @SYS-16 @SUB-EXC-03 @SW-EXC-06 @SW-EXC-07 @IF-09 @VER-SYS-12 @VER-STK-07 @VER-BR-04
  Scenario: A software interrupt runs its handler once
    Given the firmware is booted in QEMU from flash
    When I enter "s"
    Then the console shows "software irq:      1 hit (ok)"
    When I enter "i"
    Then the console shows "irq  7: 1"

  @qemu @SUB-EXC-04 @SW-CON-04 @IF-12 @VER-SUB-10
  Scenario: The tick and the matrix-routed UART are counted
    Given the firmware is booted in QEMU from flash
    When I enter "i"
    Then the console shows a line matching /^irq  6: [1-9]\d*$/
    And the console shows a line matching /^irq 17: [1-9]\d*$/

  @qemu @SYS-16 @SUB-EXC-03 @SW-EXC-02 @SW-EXC-03 @CMP-08 @VER-SYS-12 @VER-SUB-10
  Scenario: Heavy interrupt load leaves computations intact
    Given a build variant with timer_init(20000) and the stress command "S"
    When the firmware is booted in QEMU from flash
    And I enter "S"
    Then the console shows "stress: 0 bad"
    And "irq 6" counts more than 100000 interrupts in total

  @qemu @SW-CON-06 @SW-EXC-09 @VER-SUB-13
  Scenario: Waiting for input sleeps without losing a wake-up
    Given the firmware is booted in QEMU from flash
    When I enter "r 3ffb1000" 20 times in quick succession
    Then the console shows "read 3ffb1000" 20 times

  @qemu @pending @SW-EXC-08 @CMP-12 @VER-SW-09
  Scenario: An enabled line without a handler is disabled
    Given a build variant that enables CPU line 9 without a handler and raises it
    When the firmware is booted in QEMU from flash
    Then the console shows "irq 9: no handler, disabled"
    And the monitor prompt is shown

  @qemu @pending @SW-EXC-06 @CMP-11 @VER-SW-09
  Scenario Outline: Only level-1 lines can be requested
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

  @qemu @pending @SW-EXC-05 @CMP-10 @VER-SW-09
  Scenario: Initialisation disconnects every matrix source
    Given the firmware is booted in QEMU from flash
    When I enter "d 3ff00104 45"
    Then every word except the one at 3ff0018c (UART0, 00000011) is 00000006
