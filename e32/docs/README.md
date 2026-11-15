# e32 project documentation

This folder specifies the e32 bare-metal ESP32 firmware and its tooling.
It covers why the project exists, who uses it, what it must do at every level,
and how each requirement is proven. Everything is plain text: Markdown for
the prose and requirements, and Gherkin `.feature` files for scenarios.

## Process

The project follows the gated BDD pipeline in
[`bdd-framework.md`](bdd-framework.md) (description → EARS → Gherkin → tests
→ TDD → traceability). [`pipeline.md`](pipeline.md) records which phase each
artefact has reached and what is still open.

## How to read it

Read top-down for the "why", or bottom-up to see where a line of code comes
from:

1. [`actors-and-roles.md`](actors-and-roles.md): who and what interacts
   with the system.
2. [`epics.md`](epics.md): the nine large bodies of work.
3. [`features.md`](features.md): the features each epic delivers, one
   `.feature` file each.
4. [`stories.md`](stories.md): user stories with acceptance criteria.
5. [`requirements/`](requirements/): the requirement levels, one file per
   type (table below).
6. [`features/*.feature`](features/): Gherkin scenarios, the verification
   evidence for the `Test` method.
7. [`traceability.md`](traceability.md): the generated matrix linking every
   requirement to its parent, children, verification and scenarios.
8. [`test-results.md`](test-results.md): the generated outcome of every
   scenario and requirement in the last `tests/run_all.sh`.
9. [`verification-report.md`](verification-report.md): the generated
   Phase 5 audit: derivation, verification, Business-to-unit threads and
   the full-chain matrix.

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

Each `VER` entry records an honest status:

* **Passed**: executed and passed, with the environment and date stated.
* **Partial**: some of the procedure has been executed; the rest is listed.
* **Pending (hardware)**: needs a physical board; not yet executed.
* **Pending (automation)**: the scenario is written, but there is no
  executable step definition yet (Phase 3).

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
`tools/tracecheck.py` parses:

    ### SYS-12 — Drive a GPIO output
    - **Type:** System
    - **EARS:** Event-driven
    - **Statement:** When the operator ..., the system shall ...
    - **Derives from:** STK-07
    - **Verified by:** VER-SYS-09

Feature files tag each scenario with the requirement IDs it exercises and
the `VER` entry it belongs to, for example `@SYS-12 @VER-SYS-09`.

Every scenario also has a permanent ID in its name, `<REQ>-Snn`, filed
under the lowest-level requirement it is tagged with, so the prefix gives
its level:

    @qemu @SYS-14 @SUB-GPIO-02 @SW-GPIO-01 @HW-07 @VER-SYS-10
    Scenario Outline: SW-GPIO-01-S01: Refused pins

Each test carries the ID of the scenario it implements plus a test number,
`<REQ>-Snn-Tnn`. For a scenario in `features/*.feature`, T01 is its
pytest-bdd binding (`tests/bdd`). Further tests, and every test of a
unit-level scenario in `features/unit/`, are GoogleTest tests in
`tests/gtest`, named with underscores (`CMP_21_S01_T02_…`). See
[`../tests/README.md`](../tests/README.md).

## Checking traceability

    python3 tools/tracecheck.py           # check links, rewrite traceability.md
    python3 tools/tracecheck.py --check   # check only; non-zero exit on errors

The checker fails when any of these is true:

* An ID is duplicated.
* A parent or a verified ID does not exist.
* A requirement derives from the wrong level.
* A requirement has no verification.
* A `VER` entry lacks a method.
* A feature-file tag names an unknown ID.
* A scenario has no ID, a duplicate ID, or an ID whose requirement it is
  not tagged with.
* A scenario has no test, a test names an unknown scenario, or a
  GoogleTest test takes the T01 reserved for a pytest-bdd binding.

It warns about parents with no children and about `VER` entries that point
to scenarios that don't exist.

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
