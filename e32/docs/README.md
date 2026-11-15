# e32 project documentation

This folder specifies the e32 bare-metal ESP32 firmware and its tooling.
It covers why the project exists, who uses it, what it must do at every level,
and how each requirement is proven. Everything is plain text: Markdown for
the prose and requirements, and Gherkin `.feature` files for scenarios.

## Process

The project follows the gated BDD pipeline in
[`bdd-framework.md`](bdd-framework.md), version 2.0: description → actors,
epics and stories → EARS requirements → Gherkin features, rules and
scenarios → tests → TDD → traceability. [`pipeline.md`](pipeline.md)
records where each phase stands, how the v1 artefacts were migrated, and
which gate decisions are open.

## How to read it

The files are of three kinds (framework §1.6). **Records** define what each
item is and are never pruned. The **ledger** is the only place test status
is written. The **work view** lists what is left to do. Read top-down for
the "why", or bottom-up to see where a line of code comes from.

| File | Kind | Holds |
|---|---|---|
| [`actors.md`](actors.md) | Record | Every actor (`ACT-…`): type, goal, personas, and the roles they play |
| [`requirements.md`](requirements.md) | Record | The problem statement and the index of the requirement files |
| [`epics.md`](epics.md) | Record | The nine epics (`EP-nn`): goal, business goals realised, stories, status, completion record, history |
| [`stories.md`](stories.md) | Record | Every user story (`US-nn`): narrative, acceptance criteria → requirements, features, status, completion record, history |
| [`requirements/`](requirements/) | Record | The requirements, one file per type (table below) |
| [`features.md`](features.md) | Record index | The feature catalogue (`FEAT-nnn`) and the retired v1 feature IDs |
| [`features/<level>/`](features/) | Record | Gherkin: one feature per capability, epic and level; one `Rule:` per requirement; scenarios under their rule |
| [`traceability.md`](traceability.md) | Ledger | Generated: requirement, story and actor coverage, every scenario's tests and results, VER evidence, the Phase 6 audit |
| [`backlog.md`](backlog.md) | Work view | Generated: the stories that are not Done, and what each still needs |

## Requirement types

Every requirement carries a **type**. The type fixes its ID prefix, the
question it answers, what it derives from, and how it is normally verified.

| Level | Type | Prefix | File | Answers | Derives from | Typically verified by |
|---|---|---|---|---|---|---|
| 1 | Business | `BR` | [BR.md](requirements/BR.md) | *Why* build it? | — | Analysis (KPIs) |
| 2 | Stakeholder | `STK` | [STK.md](requirements/STK.md) | What do users *need*? | `BR` | Acceptance test / demonstration |
| 3 | System | `SYS` | [SYS.md](requirements/SYS.md) | What must the *whole system* do? | `STK` | System (end-to-end) test |
| 4 | Subsystem | `SUB` | [SUB.md](requirements/SUB.md) | What must each *subsystem* do? | `SYS` | Subsystem / integration test |
| 5 | Hardware | `HW` | [HW.md](requirements/HW.md) | What must the *hardware* do? | `SUB` | Hardware test / inspection |
| 5 | Software | `SW` | [SW.md](requirements/SW.md) | What must the *software* do? | `SUB` | Software test |
| 5 | Interface | `IF` | [IF.md](requirements/IF.md) | What crosses a *boundary*? | `SYS`/`SUB` | Interface / contract test |
| 6 | Component | `CMP` | [CMP.md](requirements/CMP.md) | What must this *building block* do? | `HW`/`SW` | Unit test |
| — | Verification | `VER` | [VER.md](requirements/VER.md) | *How* is a requirement proven? | Any it verifies | Defines the method |

Subsystem and software requirements carry the subsystem in the ID, as in
`SUB-EXC-03` or `SW-CON-04`, so the allocation is visible at a glance.
Verification IDs carry the level they verify at, as in `VER-SYS-07`.

### Verification methods (TAID)

Every `VER` entry names exactly one method:

* **T**est: exercise the item and observe the result. Most `VER` entries use
  this, and the Gherkin scenarios are their evidence.
* **A**nalysis: calculation, modelling or simulation, such as memory budgets,
  KPIs and coverage ratios.
* **I**nspection: examine an artefact directly, such as source code, a
  disassembly, a link map or a datasheet.
* **D**emonstration: show the system working in a representative scenario,
  used for stakeholder acceptance.

### Verification status

Each `VER` entry records an honest status (the ledger also shows the
outcome of its evidence in the last test run):

* **Passed**: executed and passed, with the environment and date stated.
* **Partial**: some of the procedure has been executed; the rest is listed.
* **Pending (hardware)**: needs a physical board; not yet executed.
* **Pending (automation)**: the scenario is written, but it is not
  automated yet (`@pending`).

Everything marked Passed was run in Espressif's QEMU fork with the real
ESP32 boot ROM (rev 3, "ets Jul 29 2019") or on the build host, during
development on 2026-11-14. No step has yet been executed on physical ESP32
hardware.

## EARS patterns

Requirement statements follow the EARS patterns (Easy Approach to
Requirements Syntax). Each entry names its pattern:

| Pattern | Template |
|---|---|
| Ubiquitous | The \<system\> shall \<response\>. |
| Event-driven | **When** \<trigger\>, the \<system\> shall \<response\>. |
| State-driven | **While** \<state\>, the \<system\> shall \<response\>. |
| Unwanted behaviour | **If** \<condition\>, **then** the \<system\> shall \<response\>. |
| Optional feature | **Where** \<feature is included\>, the \<system\> shall \<response\>. |
| Complex | A combination of the above, such as **While** … **when** … |

## Entry format

All requirement files use the same machine-readable layout, which
`tools/tracecheck.py` parses. A field's value may continue on indented
lines, such as a numbered list in a statement:

    ### SYS-12 — Drive a GPIO output
    - **Type:** System
    - **EARS:** Event-driven
    - **Priority:** Must
    - **Statement:** When the operator ..., the system shall ...
    - **Derives from:** STK-07
    - **Story:** US-15            (stakeholder requirements, and system
                                   requirements that formalise an
                                   acceptance criterion directly)
    - **Rationale:** ...
    - **Verified by:** VER-SYS-09

Stories and epics use one `## <ID> — title` section each, with
`- **Field:** value` lines (several fields may share a line, separated by
` · `), and an Index table that must agree with the sections.

## Features, rules and scenarios

A feature file holds one capability of one epic at one level. Its folder is
the level: `acceptance` (BR, STK), `system`, `subsystem`, `hardware`,
`software`, `interface`, `unit` (CMP). Each requirement appears as exactly
one `Rule:`, titled with its ID, with its EARS statement as the first
description line. Scenarios sit under the rule they illustrate, and their
permanent ID carries the rule's ID:

    @EP-05 @FEAT-042
    Feature: FEAT-042: GPIO control
      Epic: EP-05 GPIO control   ·   Level: software
      Supports: US-16 via STK-07 → SYS-14 → SUB-GPIO-02 → SW-GPIO-01

      @SW-GPIO-01
      Rule: SW-GPIO-01: Valid pins
        EARS: If a GPIO number is below 0, 40 or above, ... then `gpio_valid` shall return false.

        @qemu @SYS-14 @SUB-GPIO-02 @VER-SYS-10
        Scenario Outline: SW-GPIO-01-S01: Refused pins

Acceptance- and system-level features repeat, word for word, the narrative
of every story they deliver; lower levels name each story with the
derivation chain that links it. A scenario's own tags give its environment
(`@host`, `@qemu`, `@hardware`), `@pending` (not yet automated), `@gtest`
(implemented by GoogleTest), the `@VER-…` entry it is evidence for, and the
other requirements it also exercises.

Each test carries its scenario's ID plus a test number, `<REQ>-Snn-Tnn`.
For a scenario not tagged `@gtest`, T01 is its pytest-bdd binding
(`tests/bdd`); further tests, and every test of a `@gtest` scenario, are
GoogleTest tests in `tests/gtest`, named with underscores
(`CMP_21_S01_T02_…`). See [`../tests/README.md`](../tests/README.md).

## Status and the ledger

Story and epic status follow from the test results, one way only:

    tests/run_all.sh → tests/results/*.xml → traceability.md (rule ✅ / 🔴 / ⏭ / ⚠)
                     → stories.md, epics.md (✅ Done or reopened, with history)
                     → backlog.md (Open work)

A story is Done when every Test-verified requirement that traces to it
(its refining requirements and everything derived from them) has a Rule
whose scenarios are all ✅. "Skipped here" (no QEMU, board or cross
compiler) is not ✅.

## Checking traceability

    python3 tools/tracecheck.py                  # check, rewrite traceability.md and backlog.md
    python3 tools/tracecheck.py --check          # check only; non-zero exit on errors
    python3 tools/tracecheck.py --strict         # also fail on coverage gaps (Phase 6 sign-off)
    python3 tools/tracecheck.py --record-status  # write Done / reopened into stories.md, epics.md
    python3 tools/tracecheck.py --self-test      # prove every error class is detected

The checker reports an **error** (and exits 1) when:

* An ID is duplicated, or a parent, verified ID, story, actor, epic or
  feature it names does not exist.
* A requirement derives from the wrong level, or has no verification,
  priority, rationale or EARS statement; a `VER` entry lacks a method.
* An epic realises no business requirement or has no story; a business
  requirement has no epic; a primary actor has no persona or no story.
* A story has no epic, actor, narrative or refining requirement, a
  criterion without requirements, or an index row that disagrees with its
  section; `epics.md` and `stories.md` disagree on an epic's stories.
* A feature is not in a level folder, has no `FEAT-` ID or not exactly one
  epic; a rule is not a known requirement, is at the wrong level, appears
  twice, or its EARS line differs from the requirement; a scenario sits
  outside a rule or under another requirement's rule; a feature narrative
  differs from `stories.md`.
* A tag names an unknown ID.
* A scenario has no ID or no test; a test names an unknown scenario or
  takes the T01 of a pytest-bdd binding.
* A story or epic is recorded Done but its rules are not all ✅, or the
  other way round (run `--record-status`); a Done item has no completion
  record.

It reports a **coverage gap** when a Test-verified requirement has no Rule,
or its Rule has no scenario. Gaps are open Phase 3 work: they appear in the
ledger's audit and in `backlog.md`, and fail the run only with `--strict`.
It warns about parents with no children.

## Glossary

| Term | Meaning |
|---|---|
| Boot ROM | The ESP32 mask ROM that runs at reset and loads the image from flash at `0x1000`, or over UART in download mode. |
| Download mode | The ROM's serial loader, entered by holding GPIO0 low at reset. |
| Image | `e32.bin`: the ESP32 boot image format (header, segments, checksum) produced by `tools/mkimage`. |
| Register window | The Xtensa scheme in which 64 physical registers form a ring, and each call rotates the visible 16 by 4, 8 or 12. |
| Spill / fill | Storing an older frame's registers to its stack (overflow), and reloading them (underflow). |
| Level-1 interrupt | The lowest-priority interrupt level. It is taken through the user exception vector with `EXCCAUSE` = 4. |
| Interrupt matrix | The ESP32 block that routes 69 peripheral sources to the CPU's 32 interrupt lines. |
| mimmo | "MIni Memory MOnitor": the interactive command-line application. |
| Tick | The periodic `CCOMPARE0` interrupt that increments `jiffies`, `HZ` (100) times per second. |
| QEMU | Espressif's fork of the QEMU emulator, run with machine `esp32` and the real boot ROM. |
