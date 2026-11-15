# BDD pipeline status

This project follows the process in [`bdd-framework.md`](bdd-framework.md):
description → EARS → Gherkin → failing tests → TDD → traceability check.
This page records where e32 stands in that pipeline and what is still open.
Update it at every gate.

Last updated: 2026-11-14.

## Where each phase stands

| Phase | Gate | State | Evidence |
|---|---|---|---|
| 0 — Intake | Problem statement approved | **Approved** (baseline, 2026-11-14) | [`../README.md`](../README.md), [`actors-and-roles.md`](actors-and-roles.md), [`epics.md`](epics.md) |
| 1 — Requirements (EARS) | Requirements approved | **Approved** (baseline, 2026-11-14): 226 requirements, 128 VER entries | [`requirements/`](requirements/) |
| 2 — Behaviours (Gherkin) | Feature files approved | **Approved** (2026-11-14): 103 baseline scenarios with IDs, plus 32 unit-level scenarios in `features/unit/` | [`features/`](features/) |
| 3 — Tests (red) | Suite runs red | **Confirmed** (2026-11-14). GoogleTest against empty stubs (`-DE32_RED=ON`): 103 of 103 runnable tests fail on assertions, 2 skip (QEMU) | [`../tests/`](../tests/README.md) |
| 4 — Implementation | Each scenario green | **Green wherever it can run here.** The firmware predates the tests, so no new code was needed. `tests/run_all.sh`: 45 scenarios passing, 87 skipped (no QEMU, board or cross compiler), 3 failing as `PENDING automation` (STK-02-S01, CMP-36-S01, CMP-36-S02: the toolchain script, which clones from GitHub, which this environment blocks). Twelve VER entries updated with the new host evidence | [`test-results.md`](test-results.md), [`requirements/VER.md`](requirements/VER.md) |
| 5 — Verification | Matrix audited both ways | **Done, awaiting approval** (2026-11-15). Downward: 0 orphans, 0 childless parents. Across: every requirement has a VER entry, every scenario a test, every test a scenario. Thread: all 6 Business requirements reach a passing unit test. Evidence gaps: 64 Test-method VER entries are only skipped here (QEMU/board), 2 fail (toolchain script), 2 are manual board procedures. No retired items | [`verification-report.md`](verification-report.md) |

"Baseline" means the artefacts arrived complete with the imported project.
The owner approved them as the Phase 0–2 output on 2026-11-14.

To reproduce Phase 4: `tests/run_all.sh` builds and runs both suites,
keeps JUnit XML in `tests/results/`, and regenerates `traceability.md` and
`test-results.md`.

## Test layers

| Layer | Tool | What it covers | Test IDs |
|---|---|---|---|
| Gherkin binding | pytest-bdd (`tests/bdd`) | Every scenario in `features/*.feature`, executed from the feature text | `<scenario>-T01` |
| Unit (TDD) | GoogleTest + GoogleMock (`tests/gtest/unit`) | Firmware C files compiled for the host, against a simulated SoC and a mocked register bus | `CMP_…_Snn_Tnn` |
| Scenario (BDD) | GoogleTest (`tests/gtest/unit`) | Host scenarios from `features/*.feature` at component level (printf, lib, GPIO), steps marked with `GIVEN`/`WHEN`/`THEN` | `<scenario>_T02…` |
| End to end | GoogleTest (`tests/gtest/e2e`) | `tools/mkimage` run as a process on crafted ELF files. The firmware booted in QEMU (skipped here) | `SW_IMG_…`, `IF_03_S01_T02`, `CMP_26_S01_T02` |

## Differences from the framework's conventions

1. **ID format.** The framework shows `SYS-001`; e32 uses `SYS-12`,
   `SUB-EXC-03`, `VER-SYS-07`. IDs are permanent, so they are not renumbered.
2. **Scenario owner.** Many scenarios are tagged with several requirements.
   A scenario's ID is filed under its lowest-level tag (CMP over SW/HW/IF,
   over SUB, over SYS, over STK); ties go to the first tag written.
3. **Feature files by feature, not by level.** System-level files are
   grouped by feature (`console.feature`). Only unit-level scenarios have
   their own folder (`features/unit/`). The ID prefix shows each scenario's
   level.
4. **Implementation before tests.** The code predates the tests. "Red" is
   therefore shown by linking the GoogleTest suite against empty stubs of
   the same API (`tests/gtest/stubs`). That proves each test fails for want
   of behaviour, not because of a build error.
5. **Host build seams.** To compile the firmware for the host, its inline
   assembly and register accesses sit behind `E32_HOST` in `types.h` and
   `xtensa.h`. Four single-instruction `asm` statements in `io.c` and
   `mimmo.c` became macros, and the `format(printf)` attributes in `io.h`
   became `format(__printf__)`. Without `E32_HOST` they expand to the same
   code, **but the target build has not been rebuilt** here because the
   cross compiler is missing. Confirm with `make clean all` and the self
   test in QEMU before relying on it.

## Environment notes

* Here: host `cc`/`c++`, CMake, GoogleTest 1.14 and GoogleMock
  (`libgtest-dev`, `libgmock-dev`), and Python 3 with pytest and pytest-bdd.
* Missing: `xtensa-esp32-elf-gcc`, Espressif QEMU, esptool and a board.
  The cloud environment's network policy blocks GitHub release downloads,
  so `@qemu` scenarios and every scenario that needs the cross compiler
  are skipped here, with the reason in the report.
* `@hardware` scenarios need a physical board and stay manual.
