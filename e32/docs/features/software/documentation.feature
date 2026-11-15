@EP-09 @FEAT-081
Feature: FEAT-081: Documentation
  Epic: EP-09 Documentation and traceability   ·   Level: software

  Supports: US-28 via SW-DOC-01

  @SW-DOC-01
  Rule: SW-DOC-01: Trace checker
    EARS: When `tools/tracecheck.py` runs, it shall parse `docs/requirements/*.md` and the tags in `docs/features/*.feature`.
      - It shall report as errors: duplicate IDs; unknown parents or verified IDs; parents of the wrong level; requirements without verification; `VER` entries without exactly one TAID method; and feature tags naming unknown IDs.
      - It shall report as warnings: non-leaf requirements without children, and `VER` evidence tags that no scenario carries.
      - Unless `--check` is given, it shall write `docs/traceability.md`.
      - It shall exit with status 1 if there are errors.

    @host @SYS-32 @VER-SYS-22 @VER-STK-12
    Scenario: SW-DOC-01-S01: The trace check passes
      When I run "python3 tools/tracecheck.py --check"
      Then the command succeeds
      And the output contains "0 errors"
