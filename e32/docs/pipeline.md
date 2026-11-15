# BDD pipeline status

This project follows [`bdd-framework.md`](bdd-framework.md), **version 2.0**:
description → actors, epics and stories → EARS → Gherkin features, rules and
scenarios → failing tests → TDD → traceability verification. This page
records where e32 stands in that pipeline, how the v1 artefacts were
migrated, and which gate decisions are open. Update it at every gate.

Last updated: 2026-11-15 (migration from framework v1 to v2.0).

## Where each phase stands

| Phase | Gate | State | Evidence |
|---|---|---|---|
| 0 — Intake | Problem statement and actor catalogue approved | **Awaiting approval (migration).** The problem statement is new: v1 had none. Actor types and personas are new | [`requirements.md`](requirements.md), [`actors.md`](actors.md) |
| 1 — Epics & stories | Epics and stories approved | **Awaiting approval (migration).** Content approved under v1 (2026-11-14), converted to v2.0 records. Priorities and INVEST are new | [`epics.md`](epics.md), [`stories.md`](stories.md), [`backlog.md`](backlog.md) |
| 2 — Requirements (EARS) | Requirements approved | **Awaiting approval (migration).** 226 requirements and 128 VER entries approved under v1. Priority, Rationale and Story fields are new | [`requirements/`](requirements/) |
| 3 — Gherkin (features → rules → scenarios) | Feature files approved | **Awaiting approval (migration).** The 135 approved scenarios are regrouped into 83 features with 184 rules. 91 rules have no scenario yet | [`features.md`](features.md), [`features/`](features/) |
| 4 — Tests (red) | Suite runs red | **Confirmed** (2026-11-14), still valid: scenario IDs and test names did not change | [`../tests/README.md`](../tests/README.md) |
| 5 — Implementation | Each scenario green; stories Done | **In progress.** 42 scenarios ✅, 90 ⏭ skipped here, 3 🔴 (`@pending`). US-27, US-28 and EP-09 are ✅ Done; 27 stories and 8 epics are open | [`traceability.md`](traceability.md), [`backlog.md`](backlog.md) |
| 6 — Verification | Matrix audited in all directions | **Report generated, sign-off blocked** by the 91 empty rules (`--strict` fails) and the skipped evidence | [`traceability.md`](traceability.md#audit-phase-6) |

"Approved under v1" means the artefacts existed before the migration and you
approved them on 2026-11-14. The migration changed their form, not their
intent. Everything it had to add is listed under "Gate decisions" below.

## What the migration did

| v1 | v2.0 | How |
|---|---|---|
| `actors-and-roles.md` | [`actors.md`](actors.md) | Same actors and IDs. People are Primary, systems Supporting. Each Primary actor has a persona. The roles table is kept, because stories are told by a role |
| — | [`requirements.md`](requirements.md) | New: the problem statement, plus the index of the requirement files |
| `epics.md` (prose) | [`epics.md`](epics.md) (record) | Index plus one section per epic: goal, realises, priority, stories, business check, outcome sought, status, completion record, history. US-26 was listed under both EP-07 and EP-08; it stays in EP-08, as in `stories.md` |
| `stories.md` (prose) | [`stories.md`](stories.md) (record) | Index plus one section per story. The actor ID comes from the story's role. Each acceptance criterion now names its requirements: v1 named scenario titles, which were mapped to the rules those scenarios illustrate |
| requirement entries | the same, plus fields | `Priority: Must` on every requirement. `Rationale` (derived from the parents) where there was none. `Story` on the 20 stakeholder requirements and on the 6 system requirements a criterion names directly. Multi-line statements are now checked in full |
| 18 feature files, one per capability, mixed levels | 83 features in [`features/<level>/`](features/) | One file per capability, epic and level. Each requirement is one `Rule:` with its EARS statement. Each scenario moved under the rule its ID already named. v1 IDs F-01…F-18 are retired (see `features.md`). Backgrounds were kept where a file's scenarios all came from one v1 file, and copied into the scenarios otherwise |
| `traceability.md`, `test-results.md`, `verification-report.md` | [`traceability.md`](traceability.md) (ledger) | Merged: the ledger now holds requirement, story and actor coverage, every scenario's results, VER evidence and the Phase 6 audit |
| — | [`backlog.md`](backlog.md) (work view) | New: generated |
| `tools/tracecheck.py` | the same, v2 | Parses and cross-checks every record, rule and narrative. Writes the ledger and the backlog. `--record-status` writes Done and reopened status into the records. `--strict` fails on coverage gaps. The self-test now covers 20 error classes |
| `tests/bdd` | the same | Binds the level folders recursively and supports `Rule:`. Deselects `@gtest` scenarios, which GoogleTest implements |

Scenario IDs, test IDs and both test suites are unchanged, so the Phase 4
evidence still holds.

## Gate decisions

Approve or amend each one; nothing new has been implemented.

1. **Phase 0:** the problem statement in `requirements.md`, the actor types,
   and the personas "dana", "lee", "olga" and "max".
2. **Phase 1:** every epic and story has priority **Must**: everything in
   scope has shipped. INVEST is marked "not yet assessed" on all 29 stories.
   Some, such as US-27 "Learn the system", may need splitting.
3. **Phase 2:** priority **Must** on all 226 requirements, and the derived
   rationales ("Needed to meet <parent> (<title>)"). These could be
   rewritten by hand where a better reason exists.
4. **Phase 3:** the feature structure. In particular, the 91 empty rules
   need scenarios before Phase 6 can be signed off:
   * 81 of them are already exercised by other rules' scenarios, through
     an extra requirement tag (listed in the ledger's audit). Each needs a
     scenario of its own under its rule. That is new Phase 3 work: about 81
     new scenarios, mostly reusing existing steps.
   * 10 have no scenario at all: HW-04, HW-05, IF-10, IF-11, SUB-MON-01,
     SUB-MON-03, SW-EXC-10, SW-TIME-04, SW-BLD-01 and SW-BLD-05.
5. **Story granularity:** a story counts as Done only when everything
   derived from its stakeholder requirement is green (framework §1.2).
   Several stakeholder requirements are shared by many stories: STK-06 by
   US-10, US-12, US-13 and US-14; STK-08 by US-19, US-21 and US-29. So
   most stories trace to 20–50 rules, and US-10 cannot be Done before every
   monitor rule is. Splitting those stakeholder requirements would make
   stories finish independently.

## Differences from the framework's templates

1. **ID format.** The template shows `SYS-001`, `EP-001`, `US-001`,
   `ACT-001`. e32 keeps its permanent v1 IDs: `SYS-12`, `SUB-EXC-03`,
   `EP-01`, `US-01`, `ACT-H1`, `ACT-S1`. Feature IDs are new, so they use
   `FEAT-001`.
2. **Requirements in files.** Requirements live in one file per type under
   `requirements/`, which `requirements.md` indexes, not in one table.
3. **Acceptance level.** Rules of stakeholder requirements (acceptance
   demonstrations) sit in `features/acceptance/`.
4. **Story narratives in features.** A feature repeats the stories its
   rules name directly (Story field or acceptance criterion), or else
   those of their nearest parents. Done status uses the framework's wider
   rule: everything derived from the story's refining requirements.
5. **Implementation before tests.** The code predates the tests. "Red" was
   shown by linking the GoogleTest suite against empty stubs.
6. **Host build seams.** The firmware compiles for the host behind
   `E32_HOST`. The target build has not been rebuilt since those changes,
   because the cross compiler is not available here.

## Environment notes

* Here: host `cc`/`c++`, CMake, GoogleTest 1.14 and GoogleMock, and
  Python 3 with pytest and pytest-bdd 9.
* Missing: `xtensa-esp32-elf-gcc`, Espressif QEMU, esptool and a board. The
  `@qemu` and `@hardware` scenarios, and those that need the cross
  compiler, are skipped here, which is why most rules show ⏭.
