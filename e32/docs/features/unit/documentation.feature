@EP-09 @FEAT-082
Feature: FEAT-082: Documentation
  Epic: EP-09 Documentation and traceability   ·   Level: unit

  Supports: US-28 via SW-DOC-01 → CMP-40

  @CMP-40
  Rule: CMP-40: tools/tracecheck.py
    EARS: When run with Python 3 and no third-party modules, `tracecheck.py` shall implement SW-DOC-01. The level rules it enforces are:
      - `STK` derives from `BR`;
      - `SYS` from `STK`;
      - `SUB` from `SYS`;
      - `HW` and `SW` from `SUB`;
      - `IF` from `SYS` or `SUB`;
      - `CMP` from `HW` or `SW`.

    @host @VER-CMP-21
    Scenario: CMP-40-S01: The checker detects every error class
      When I run "python3 tools/tracecheck.py --self-test"
      Then the command succeeds
      And the output contains "self-test: all error classes detected"
