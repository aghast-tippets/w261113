@EP-09 @F-17
Feature: Documentation and traceability
  As a learner and a maintainer
  I want complete documentation and traceable requirements
  So that I can understand the system and change it safely

  @host @SYS-28 @SUB-DOC-01 @VER-SYS-22 @VER-STK-12
  Scenario Outline: README covers the required topics
    When I read "README.md"
    Then it has a section or table about "<topic>"

    Examples:
      | topic                           |
      | Building and running            |
      | How it boots                    |
      | Memory map                      |
      | Interrupts and faults           |
      | Interrupt API                   |
      | mimmo commands                  |
      | GPIO notes                      |
      | Rules for interrupt handlers    |
      | What was tested                 |
      | LPC1343 equivalent              |

  @host @SYS-32 @SW-DOC-01 @VER-SYS-22 @VER-STK-12
  Scenario: The trace check passes
    When I run "python3 tools/tracecheck.py --check"
    Then the command succeeds
    And the output contains "0 errors"

  @host @SUB-DOC-01 @VER-SYS-22
  Scenario: The traceability matrix is up to date
    When I run "python3 tools/tracecheck.py"
    Then "docs/traceability.md" is unchanged

  @host @CMP-40 @VER-CMP-21
  Scenario: The checker detects every error class
    When I run "python3 tools/tracecheck.py --self-test"
    Then the command succeeds
    And the output contains "self-test: all error classes detected"
