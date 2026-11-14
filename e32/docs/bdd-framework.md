# BDD Project Framework: Description → EARS → Gherkin → Tests → TDD

A language-agnostic framework for turning a plain-text project description into verified, traceable software. This document contains three parts:

1. **The Plan** — how the framework works and why
2. **The Prompt** — a ready-to-paste Claude prompt that runs the framework
3. **The Templates** — file skeletons the framework produces

For where e32 currently stands in this pipeline, see [`pipeline.md`](pipeline.md).

---

## Part 1: The Plan

### 1.1 Purpose

Most projects fail the "did we build the right thing?" test because requirements, behaviours, and tests drift apart. This framework enforces a single unbroken chain:

```
Text description
      ↓  (analysis + clarifying questions)
EARS requirements          typed & traced across levels:
                           BR-001 → STK-001 → SYS-001 → SUB-001
                                  → HW/SW/IF-001 → CMP-001   (+ VER-001)
      ↓  (each requirement → one or more scenarios)
Gherkin behaviours         SYS-001-S01, CMP-001-S01, …  (per level)
      ↓  (each scenario → one or more tests)
Failing tests              SYS-001-S01-T01, CMP-001-S01-T01, …
      ↓  (red → green → refactor)
Implementation
      ↓  (matrix check)
Traceability verification  every requirement derived + covered, every test justified
```

Nothing is implemented that doesn't trace back to a requirement. No requirement is considered done until its scenarios pass as tests.

### 1.2 The Five Phases

**Phase 0 — Intake.** The user provides a free-text description of what they want. Claude asks clarifying questions until the scope, actors, and success criteria are unambiguous. Output: an agreed problem statement.

**Phase 1 — Requirements (EARS).** Every requirement is written in one of the six EARS (Easy Approach to Requirements Syntax) patterns:

| Pattern | Template |
|---|---|
| Ubiquitous | The `<system>` shall `<response>` |
| Event-driven | **When** `<trigger>`, the `<system>` shall `<response>` |
| State-driven | **While** `<state>`, the `<system>` shall `<response>` |
| Optional feature | **Where** `<feature is included>`, the `<system>` shall `<response>` |
| Unwanted behaviour | **If** `<condition>`, **then** the `<system>` shall `<response>` |
| Complex | Combinations of the above (When/While/If + shall) |

Each requirement is also **classified by type/level** (business, stakeholder, system, subsystem, hardware, software, interface, component/unit, or verification & test — see §1.3) and gets a typed ID (`SYS-001`), a priority (Must/Should/Could), a **parent link** to the requirement it derives from, and a rationale. Higher-level requirements are decomposed downward into lower-level ones, and every requirement is paired with a verification & test requirement that says how it will be proven met. **Gate: the user approves the requirements before Phase 2.**

**Phase 2 — Behaviours (Gherkin).** Each requirement is decomposed into one or more Gherkin scenarios covering the happy path, edge cases, and failure modes. Scenarios are tagged with the typed requirement they satisfy (`@SYS-001`) and carry their own ID (`SYS-001-S01`), whose prefix records the verification level. Scenarios must be concrete: real example values, no vague language. **Gate: the user approves the feature files before Phase 3.**

**Phase 3 — Tests (Red).** Once the user names the target language and test framework, each scenario becomes one or more executable tests. Test names embed the scenario ID so traceability survives in the test runner output. All tests are written first and must fail for the right reason (missing implementation, not syntax errors). **Gate: the full suite runs red before any implementation.**

**Phase 4 — Implementation (Green → Refactor).** Classic TDD loop, one scenario at a time: write the minimum code to pass the current test, run the suite, refactor with the suite green, move on. No code is written that isn't demanded by a failing test.

**Phase 5 — Verification.** The traceability matrix is completed and audited in both directions: downward, every requirement below Business derives from a parent and every parent has a satisfying child; across and up, every functional requirement maps to a verification requirement and ≥1 passing test, every scenario to ≥1 passing test, and every test back to a requirement. At least one unbroken thread must run from a business goal down to a passing unit/component test. Orphans in either direction are defects — a missing derivation, a missing test, or scope creep.

### 1.3 Requirement Types & Levels

Real systems don't have one flat list of requirements — they have a **ladder** of them. A business goal is decomposed into stakeholder needs, those into system behaviour, that into subsystems, and those are allocated to hardware, software, and the interfaces between them, down to individual components or units. Each level is written by (and readable to) a different audience, and each level is **verified by a matching class of test**. This framework makes that ladder explicit so a single business goal can be traced all the way down to a unit test — and back up again.

Every requirement carries a **type** that fixes its ID prefix, the question it answers, whom it derives from, and how it is verified:

| Level | Type | Prefix | Answers | Derives from | Typically verified by |
|---|---|---|---|---|---|
| 1 | Business | `BR` | *Why* are we building this? What business outcome? | — (top of the chain) | Business validation / KPIs (analysis) |
| 2 | Stakeholder | `STK` | What do users/stakeholders *need*? | `BR` | Acceptance test / demonstration |
| 3 | System | `SYS` | What must the *whole system* do? | `STK` | System (end-to-end) test |
| 4 | Subsystem | `SUB` | What must each *subsystem* do? | `SYS` | Subsystem / integration test |
| 5 | Hardware | `HW` | What must the *hardware* do? | `SUB` (allocated) | Hardware test / inspection |
| 5 | Software | `SW` | What must the *software* do? | `SUB` (allocated) | Software test |
| 5 | Interface | `IF` | What crosses the *boundary* between two elements? | `SYS`/`SUB` (allocated) | Interface / contract test |
| 6 | Component / Unit | `CMP` | What must this individual *build block* do? | `HW`/`SW` | Unit test |
| — | Verification & Test | `VER` | *How* is a requirement proven met, and at what level? | any requirement it verifies | (defines the method — see below) |

**Verification methods (TAID).** Every `VER` requirement names one of four methods: **T**est (exercise it and observe), **A**nalysis (calculation, modelling, or simulation), **I**nspection (examine the artifact directly), **D**emonstration (show it operating in a representative scenario). In this framework most verification is by Test — the Gherkin scenarios (Phase 2) and executable tests (Phase 3) *are* the verification evidence — but business and hardware requirements often use Analysis or Inspection instead.

**The requirements "V".** Decomposition runs down the left; verification runs up the right, each level checked by the class of test that matches it:

```
                   VALIDATION  (did we build the right thing?)

  Business (BR) ......................................  Business validation / KPIs
     |  derives                                              ^
     v                                                       |  validates
  Stakeholder (STK) ..................................  Acceptance / demonstration
     |                                                       ^
     v                                                       |
  System (SYS) .......................................  System (end-to-end) test
     |                                                       ^
     v                                                       |
  Subsystem (SUB) ....................................  Subsystem / integration test
     |                                                       ^
     v                                                       |
  Hardware / Software / Interface ....................  HW / SW / interface test
  (HW / SW / IF)                                             ^
     |                                                       |
     v                                                       |
  Component / Unit (CMP) .............................  Unit test
                                                             ^
                   VERIFICATION  (did we build it right?)
```

**Two directions of trace.**
- **Downward (derivation / allocation):** every requirement below the top records the parent it *derives from*. No lower requirement may exist without a parent, and no parent is "done" until its children are satisfied — this is how scope creep and orphaned work are caught.
- **Upward + across (verification / validation):** every requirement is *verified by* at least one `VER` requirement whose method and level match its own. Because a requirement's type prefix flows into its scenario and test IDs (`SYS-001-S01-T01` is a system-level test; `CMP-001-S01-T01` is a unit test), the **level of any test is self-documenting**.

Small or flat projects don't need every rung: use only the levels that apply (a pure library might have just `SW`, `IF`, and `CMP`), and the generic `REQ` prefix remains valid when levels genuinely don't matter. The rule is that whatever levels you *do* use must form an unbroken derive-from / verified-by chain.

### 1.4 Traceability Scheme

```
SYS-001                  a requirement, prefixed by its type (§1.3): BR/STK/SYS/SUB/HW/SW/IF/CMP/VER
SYS-001  derives from    STK-004        downward link to its parent requirement
SYS-001  verified by     VER-012        link to the verification & test requirement (method + level)
SYS-001-S01              scenario 1 for SYS-001
SYS-001-S01-T01          test 1 for scenario S01 (a system-level test — the prefix names the level)
```

- IDs are never reused. Deleted items are marked `RETIRED`, not renumbered.
- Changed requirements bump a revision suffix (`SYS-001r2`) and force re-review of their **children, scenarios, tests, and verification requirements**.
- Numbering runs **per type** (`SYS-001`, `SYS-002`, … independently of `SW-001`, `SW-002`, …).
- The matrix (`traceability.md`) is the single source of truth for coverage status, and now spans the full chain: business goal → … → unit → test.

### 1.5 Design Decisions

- **Language agnostic:** Phases 0–2 are pure text and work for any target. The framework only asks for a language/framework at Phase 3.
- **Hard gates:** Claude must stop and wait for explicit approval between phases. This prevents an eager cascade of assumptions.
- **Paste-in prompt:** the prompt below is self-contained; no project setup or custom instructions required. Paste it as the first message of a fresh chat, then answer its questions.

---

## Part 2: The Prompt (paste everything in the box below into a new Claude chat)

````text
You are a BDD/TDD project bootstrapper. Your job is to take my plain-text
description of a piece of software and drive it through a strict, gated
pipeline: EARS requirements → Gherkin behaviours → failing tests → TDD
implementation → traceability verification. Follow these rules exactly.

## PIPELINE (never skip or merge phases)

PHASE 0 — INTAKE
- I will describe what I want in plain text.
- Ask clarifying questions (batched, numbered) until you can state the
  scope, actors, inputs/outputs, and success criteria without ambiguity.
- Produce a short "Problem Statement" and ask me to approve it.
- Do not proceed until I say "approved" or equivalent.

PHASE 1 — REQUIREMENTS (EARS)
- Convert the approved problem statement into requirements using ONLY the
  six EARS patterns:
    Ubiquitous:  The <system> shall <response>
    Event:       When <trigger>, the <system> shall <response>
    State:       While <state>, the <system> shall <response>
    Optional:    Where <feature>, the <system> shall <response>
    Unwanted:    If <condition>, then the <system> shall <response>
    Complex:     valid combinations of the above
- CLASSIFY every requirement by type/level and prefix its ID accordingly:
    BR  Business      (why / business outcome)      -> derives from: nothing
    STK Stakeholder   (user/stakeholder need)       -> derives from: BR
    SYS System        (whole-system behaviour)      -> derives from: STK
    SUB Subsystem     (per-subsystem behaviour)     -> derives from: SYS
    HW  Hardware      (hardware behaviour)          -> allocated from: SUB
    SW  Software      (software behaviour)          -> allocated from: SUB
    IF  Interface     (boundary between elements)   -> allocated from: SYS/SUB
    CMP Component/Unit(single build block)          -> derives from: HW/SW
    VER Verification  (how a requirement is proven) -> verifies: any requirement
  Number per type (SYS-001, SYS-002, … independent of SW-001, …). Use only
  the levels that apply to this project; the plain REQ prefix is allowed
  when levels genuinely don't matter, but whatever levels you use MUST form
  an unbroken chain.
- DERIVE downward: decompose higher-level requirements into lower-level
  ones. Every non-business requirement records the parent it derives from
  (or is allocated to). No orphan lower-level requirements; no parent left
  without children that satisfy it.
- VERIFY across: give every functional requirement at least one VER
  requirement stating the method — Test / Analysis / Inspection /
  Demonstration (TAID) — and the level at which it is checked. In this
  pipeline, Test-method verification is fulfilled by the Phase 2 scenarios
  and Phase 3 tests; Analysis/Inspection/Demonstration are recorded as VER
  requirements even when no automated test backs them.
- Each requirement gets: ID (typed, e.g. SYS-001), EARS pattern name,
  priority (Must/Should/Could), Derived-From link, Verified-By link, and a
  one-line rationale.
- Include unwanted-behaviour requirements for every plausible failure mode.
- Output the requirements as a markdown table (grouped by level, highest
  first), then STOP and ask for my approval, amendments, or additions.
  Renumber nothing; retire instead.

PHASE 2 — BEHAVIOURS (Gherkin)
- For each approved requirement, write one or more Gherkin scenarios in
  .feature file format.
- Rules:
  - Tag every Scenario with its requirement using the typed ID: @SYS-001
  - Give every scenario an ID in its name: "SYS-001-S01: <short title>".
    The type prefix carries the verification level, so the level of the
    scenario (system, subsystem, software, unit, …) is self-evident.
  - Cover happy path, boundary/edge cases, and failure modes.
  - Use concrete example values, never placeholders like "some input".
  - Use Scenario Outline + Examples tables where variations are tabular.
  - Given = context, When = single action, Then = observable outcome.
    No implementation detail in any step.
- Output the complete .feature file(s), then STOP for my approval.

PHASE 3 — TESTS (RED)
- Ask me for the target language and test framework if I have not already
  stated them. Everything before this point is language-agnostic.
- Convert every scenario into executable test(s). Embed the scenario ID in
  each test name (e.g. test_SYS_001_S01_valid_login, or the idiomatic
  equivalent for the chosen framework). Number multiple tests per scenario
  T01, T02, …. The test's type prefix pins its level: SYS-* tests are
  system tests, CMP-* tests are unit tests, IF-* tests are interface/
  contract tests — organise the suite by level accordingly.
- Propose a project/file structure appropriate to the language.
- All tests must be runnable and must FAIL because the implementation is
  missing — not because of syntax errors or bad imports. Provide stub
  interfaces/signatures only where required for the suite to compile/run.
- Output the tests and instructions to run them. STOP and wait for me to
  confirm the suite runs red.

PHASE 4 — IMPLEMENTATION (GREEN → REFACTOR)
- Work one scenario at a time, in priority order (Must first).
- For each: write the MINIMUM code to pass its test(s), tell me to run the
  suite, then refactor only while green.
- Never write code not demanded by a currently failing test. If you think
  code is needed that no test demands, propose a new requirement/scenario
  first and route it back through the pipeline.
- After each scenario goes green, update the traceability matrix row.

PHASE 5 — VERIFICATION
- Produce the final traceability matrix, spanning the full chain:
    REQ id | Level | EARS pattern | Derives-From | Scenario id(s) |
    Test id(s) | VER (method) | Status
- Audit BOTH directions:
    * Downward: every requirement (except Business) has a parent it derives
      from; every parent has ≥1 child that satisfies it. Orphans and
      childless parents are defects.
    * Across/up: every functional requirement has ≥1 VER requirement, and
      every Test-method VER has ≥1 passing test. Scenario with no test, or
      test with no requirement, is a defect.
- Confirm at least one unbroken thread runs top to bottom (a Business
  requirement traceable down to a passing unit/component test) and report
  any level that breaks the chain.
- Summarise coverage and list any RETIRED items.

## STANDING RULES
- Maintain three artifacts throughout and reprint any that change:
  requirements.md, the .feature files, traceability.md.
- IDs are permanent and typed by level (BR/STK/SYS/SUB/HW/SW/IF/CMP/VER),
  numbered per type. Never renumber. Mark removed items RETIRED. Amended
  requirements become <TYPE>-NNNr2 and invalidate their children,
  scenarios, tests, and verification requirements until re-reviewed.
- Every requirement below Business must trace up to a parent and be covered
  by a verification requirement; keep both links current as things change.
- At every gate, wait for my explicit approval before continuing.
- If I ask for something mid-pipeline that isn't covered by a requirement,
  route it through Phase 1 first (as a new REQ), then cascade.
- Be concise in commentary; be complete in artifacts.

Acknowledge these rules in one short paragraph, then ask me for my project
description to begin Phase 0.
````

---

## Part 3: File Templates

### 3.1 `requirements.md`

```markdown
# Requirements — <Project Name>
Status: Draft | Approved   ·   Revision: 1   ·   Date: YYYY-MM-DD

## Problem Statement
<Approved Phase 0 statement.>

## Requirements  (grouped by level, highest first)

Columns: Derives-From = parent requirement (blank for Business);
Verified-By = the VER requirement(s) that prove it.

| ID      | Level       | Pattern    | Priority | Requirement (EARS)                                                                       | Derives-From | Verified-By | Rationale             |
|---------|-------------|------------|----------|------------------------------------------------------------------------------------------|--------------|-------------|-----------------------|
| BR-001  | Business    | Ubiquitous | Must     | The product shall let returning customers reach their account securely.                   | —            | VER-001     | Cut support-reset cost|
| STK-001 | Stakeholder | Event      | Must     | When a returning customer provides their credentials, they shall be granted account access. | BR-001    | VER-002     | Primary user need     |
| SYS-001 | System      | Event      | Must     | When a user submits valid credentials, the system shall create an authenticated session.  | STK-001      | VER-003     | Core login flow       |
| SYS-002 | System      | Unwanted   | Must     | If credentials are invalid, then the system shall reject the attempt and record it.       | STK-001      | VER-004     | Security              |
| SUB-001 | Subsystem   | Ubiquitous | Must     | The Identity subsystem shall authenticate users and manage their sessions.                | SYS-001      | VER-005     | Decomposition         |
| SW-001  | Software    | Event      | Must     | When given valid credentials, the auth service shall issue a signed session token.        | SUB-001      | VER-006     | Session issuance      |
| IF-001  | Interface   | Event      | Must     | When a client POSTs credentials to /login, the API shall return a session token or 401.   | SUB-001      | VER-007     | Client/service contract|
| HW-001  | Hardware    | Ubiquitous | Should   | The hardware security module shall store the session-signing key and never export it.     | SUB-001      | VER-008     | Key protection        |
| CMP-001 | Component   | State      | Must     | While issuing a token, the token generator shall set a 15-minute expiry.                  | SW-001       | VER-009     | Session hygiene       |

## Verification & Test Requirements

Method = TAID (Test / Analysis / Inspection / Demonstration). For Test-method
rows, the Evidence column names the scenario/test IDs that fulfil it.

| ID      | Verifies | Level       | Method        | Acceptance / Evidence                                  |
|---------|----------|-------------|---------------|--------------------------------------------------------|
| VER-001 | BR-001   | Business    | Analysis      | Password-reset support tickets fall ≥ 30% in a quarter |
| VER-002 | STK-001  | Stakeholder | Demonstration | Returning customer signs in during an acceptance demo  |
| VER-003 | SYS-001  | System      | Test          | SYS-001-S01 → SYS-001-S01-T01                           |
| VER-004 | SYS-002  | System      | Test          | SYS-002-S01 → SYS-002-S01-T01, -T02                     |
| VER-006 | SW-001   | Software    | Test          | SW-001-S01 → SW-001-S01-T01                             |
| VER-007 | IF-001   | Interface   | Test          | IF-001-S01 → IF-001-S01-T01 (contract test)            |
| VER-008 | HW-001   | Hardware    | Inspection    | HSM datasheet + config review confirm non-exportable key|
| VER-009 | CMP-001  | Component   | Test          | CMP-001-S01 → CMP-001-S01-T01 (unit test)              |

## Retired
| ID      | Reason | Date |
|---------|--------|------|
```

### 3.2 `features/<area>.feature`

```gherkin
Feature: Authentication
  Covers SYS-001, SYS-002 (system level)

  Background:
    Given a registered user "alice" with password "Correct-Horse-9"

  @SYS-001
  Scenario: SYS-001-S01: Valid login creates a session
    Given "alice" is on the login page
    When she submits username "alice" and password "Correct-Horse-9"
    Then an authenticated session is created for "alice"
    And she is redirected to her dashboard

  @SYS-002
  Scenario Outline: SYS-002-S01: Invalid credentials are rejected
    Given "alice" is on the login page
    When she submits username "<username>" and password "<password>"
    Then the attempt is rejected with message "Invalid credentials"
    And the failed attempt is recorded

    Examples:
      | username | password        |
      | alice    | wrong-password  |
      | bob      | Correct-Horse-9 |
```

Lower-level requirements get their own feature files at their own level — e.g.
`features/unit/token-generator.feature` tagged `@CMP-001`, or
`features/interface/login-api.feature` tagged `@IF-001` — so each `.feature`
file (and the tests it drives) sits at exactly one point on the requirements V.

### 3.3 `traceability.md`

```markdown
# Traceability Matrix — <Project Name>

Spans the full chain: level → parent → requirement → scenario → test → verification.

| REQ ID  | Level     | Derives-From | Pattern    | Scenario ID(s) | Test ID(s)                       | VER (method)       | Status         |
|---------|-----------|--------------|------------|----------------|----------------------------------|--------------------|----------------|
| BR-001  | Business  | —            | Ubiquitous | —              | —                                | VER-001 (Analysis) | 📊 KPI-tracked |
| STK-001 | Stakeholder| BR-001      | Event      | —              | —                                | VER-002 (Demo)     | 📊 Acceptance  |
| SYS-001 | System    | STK-001      | Event      | SYS-001-S01    | SYS-001-S01-T01                  | VER-003 (Test)     | ✅ Green       |
| SYS-002 | System    | STK-001      | Unwanted   | SYS-002-S01    | SYS-002-S01-T01, SYS-002-S01-T02 | VER-004 (Test)     | 🔴 Red         |
| SW-001  | Software  | SUB-001      | Event      | SW-001-S01     | SW-001-S01-T01                   | VER-006 (Test)     | 🔴 Red         |
| IF-001  | Interface | SUB-001      | Event      | IF-001-S01     | IF-001-S01-T01                   | VER-007 (Test)     | 🔴 Red         |
| HW-001  | Hardware  | SUB-001      | Ubiquitous | —              | —                                | VER-008 (Inspect)  | 🔍 Inspection  |
| CMP-001 | Component | SW-001       | State      | —              | —                                | VER-009 (Test)     | ⚠ No scenario  |

Status legend: ⚠ gap · 📝 scenario only · 🔴 tests failing (expected pre-impl.) · ✅ passing · 📊 non-test verification (Analysis/Demo) · 🔍 Inspection · ⛔ RETIRED
Audit rules:
- Downward: any requirement below Business with no Derives-From, or any parent with no child, is a defect.
- Across: any functional requirement with no VER, any ⚠ row, or any test with no requirement, is a defect.
- Thread check: at least one unbroken line must run Business → … → passing test.
```

### 3.4 Test naming convention (language-agnostic)

```
<framework-idiomatic prefix> + <TYPE>_NNN_SNN_TNN + short_description
(the <TYPE> prefix names the verification level: SYS = system test,
 IF = interface test, CMP = unit test, …)

Examples:
  Python/pytest : def test_SYS_001_S01_T01_valid_login_creates_session():
  JS/Jest       : it("SYS-001-S01-T01: valid login creates session", …)
  Java/JUnit    : @DisplayName("CMP-001-S01-T01 …") void tokenHas15MinExpiry()
  Go            : func TestIF001S01T01LoginApiReturnsToken(t *testing.T)
```

### 3.5 Suggested project layout (adapt per language)

```
project/
├── docs/
│   ├── requirements.md      # typed requirements + VER requirements
│   └── traceability.md      # full chain: business → … → unit → test
├── features/                # one .feature per requirement, filed by level
│   ├── system/              #   @SYS-* scenarios
│   ├── subsystem/           #   @SUB-* scenarios
│   ├── interface/           #   @IF-*  scenarios (contract tests)
│   └── unit/                #   @CMP-* scenarios
├── tests/                   # mirrors the levels above (or idiomatic location)
│   ├── system/  interface/  unit/  …
└── src/                     # implementation, written only under Phase 4
```

Not every project needs every level — keep only the folders whose levels you
actually use. The point is that a test's location and its ID prefix agree on
which rung of the requirements V it verifies.
