@EP-09 @FEAT-080
Feature: FEAT-080: Documentation
  Epic: EP-09 Documentation and traceability   ·   Level: subsystem

  Supports: US-27 via SUB-DOC-01

  @SUB-DOC-01
  Rule: SUB-DOC-01: Document set
    EARS: The documentation subsystem shall consist of `README.md`, the `docs/` set (actors, epics, features, stories, requirements at every level, verification and Gherkin scenarios) and `tools/tracecheck.py`, which generates `docs/traceability.md`. The README shall include a provenance section stating the origin of every source file and naming every externally specified or fetched input.

    @host @SYS-28 @VER-SYS-22 @VER-STK-12
    Scenario Outline: SUB-DOC-01-S01: README covers the required topics
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

    @host @VER-SYS-22
    Scenario: SUB-DOC-01-S02: The traceability matrix is up to date
      When I run "python3 tools/tracecheck.py"
      Then "docs/traceability.md" is unchanged
