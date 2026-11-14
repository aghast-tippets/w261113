# BDD pipeline status

This project follows the process in [`bdd-framework.md`](bdd-framework.md):
description → EARS → Gherkin → failing tests → TDD → traceability check.
This page records where e32 stands in that pipeline and what is still open.
Update it at every gate.

Last updated: 2026-11-14.

## Where each phase stands

| Phase | Gate | State | Evidence |
|---|---|---|---|
| 0 — Intake | Problem statement approved | Done (baseline) | [`../README.md`](../README.md), [`actors-and-roles.md`](actors-and-roles.md), [`epics.md`](epics.md) |
| 1 — Requirements (EARS) | Requirements approved | Done (baseline): 226 requirements, 128 VER entries | [`requirements/`](requirements/) |
| 2 — Behaviours (Gherkin) | Feature files approved | Done (baseline): 103 scenarios in 17 files | [`features/`](features/) |
| 3 — Tests (red) | Suite runs red | **Not started.** Scenarios are checked by hand; there are no executable step definitions | — |
| 4 — Implementation | Each scenario green | Firmware already exists. It was written before Phase 3, so tests will be retrofitted (see below) | source files in `..` |
| 5 — Verification | Matrix audited both ways | Link checking automated: `python3 tools/tracecheck.py --check` passes (354 entries, 0 errors, 0 warnings) | [`traceability.md`](traceability.md) |

"Baseline" means the artefacts arrived complete with the imported project
and are taken as the approved Phase 0–2 output. The owner confirms or
amends them at the Phase 3 gate.

Verification status today (from `traceability.md`): 64 Passed, 53 Partial,
11 Pending. Scenario environment tags: 31 `@host`, 58 `@qemu`,
15 `@hardware`, 29 `@pending`.

## Differences from the framework's conventions

These are kept on purpose or are open decisions. None of them breaks the
trace chain.

1. **ID format.** The framework shows `SYS-001`; e32 uses `SYS-12`,
   `SUB-EXC-03`, `VER-SYS-07`. IDs are permanent, so they are not renumbered.
2. **No scenario IDs.** The framework names scenarios `SYS-001-S01: …` and
   tests `SYS-001-S01-T01`. e32 scenarios carry requirement and VER tags but
   no scenario ID, and many tag several requirements. Open decision: which
   tag owns the scenario ID (for example the lowest-level requirement tag).
3. **Feature files by feature, not by level.** Files are grouped by feature
   (`console.feature`), and a scenario's level is read from its tags rather
   than from a `system/`, `unit/` folder.
4. **Implementation before tests.** Phase 4 normally follows Phase 3. Here
   the code exists, so Phase 3 tests must first be shown to fail for the
   right reason (for example against a stubbed or broken build) before they
   count as evidence.

## Environment notes for Phase 3

* The host build tools work here: `cc` builds `tools/mkimage`, and Python 3
  runs `tools/tracecheck.py`. Python test packages install from PyPI.
* The cross compiler (`xtensa-esp32-elf-gcc`) and Espressif QEMU are not
  installed. Their GitHub release downloads are blocked by this cloud
  environment's network policy, so `@qemu` scenarios cannot run here until
  that host is allowed or the tools are built from source
  (`tools/build-toolchain.sh`, about 30 minutes; also fetches from GitHub).
* `@hardware` scenarios need a physical board and stay manual.
