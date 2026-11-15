@EP-09 @FEAT-083
Feature: FEAT-083: Stakeholder acceptance: Documentation and traceability
  Epic: EP-09 Documentation and traceability   ·   Level: acceptance

  User stories delivered:
    US-27  As a learner, I want documentation that explains the boot, interrupt
           and fault paths and maps each file to the LPC1343 original, so that I
           can understand and modify everything.

  Actors: Learner (ACT-H2, persona "lee")

  @STK-15 @US-27
  Rule: STK-15: Explanatory documentation
    EARS: The learner needs documentation that explains the boot, interrupt and fault paths, the memory map and the APIs, and maps each file to Rubini's LPC1343 original.

    @host @STK-20 @VER-STK-12
    Scenario: STK-15-S01: Learner and maintainer use the documentation
      When the learner reads README.md
      Then boot, memory map, vectors, interrupts, faults and the LPC1343 mapping are explained
      When the maintainer runs "python3 tools/tracecheck.py --check"
      Then it reports 0 errors
