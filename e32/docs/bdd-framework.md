# v2.0 BDD Project Framework: Description → Actors, Epics & Stories → EARS → Gherkin (Features, Rules, Scenarios) → Tests → TDD

A language-agnostic framework for turning a plain-text project description into verified, traceable software. This document contains three parts:

1. **The Plan** — how the framework works and why
2. **The Prompt** — a ready-to-paste Claude prompt that runs the framework
3. **The Templates** — file skeletons the framework produces

For where e32 stands in this pipeline, and how its v1 artefacts were migrated, see [`pipeline.md`](pipeline.md).

---

## Part 1: The Plan

### 1.1 Purpose

Most projects fail the "did we build the right thing?" test because requirements, behaviours, and tests drift apart. This framework enforces a single unbroken chain:

```
Text description
      ↓  (analysis + clarifying questions)
Problem statement + Actors   ACT-001, ACT-002, …  (who uses or touches the system)
      ↓  (business goals → epics → user stories)
Epics & user stories         BR-001 → EP-001 → US-001
                             "As a <actor>, I want <capability>, so that <benefit>"
      ↓  (each story's acceptance criteria → EARS requirements)
EARS requirements            typed & traced across levels:
                             BR-001 → STK-001 → SYS-001 → SUB-001
                                    → HW/SW/IF-001 → CMP-001   (+ VER-001)
      ↓  (requirements grouped into features; each requirement → one Rule)
Gherkin features & rules     FEAT-001 (.feature file)  ⊃  Rule: SYS-001 …
      ↓  (each rule → one or more concrete examples)
Gherkin scenarios            SYS-001-S01, CMP-001-S01, …  (per level)
      ↓  (each scenario → one or more tests)
Failing tests                SYS-001-S01-T01, CMP-001-S01-T01, …
      ↓  (red → green → refactor)
Implementation
      ↓  (matrix check)
Traceability verification    every story realised, every requirement derived + covered,
                             every test justified
```

Nothing is implemented that doesn't trace back to a requirement, and no requirement exists that doesn't trace back to a user story or business goal. No story is done until every rule it produced passes as tests.

### 1.2 The Building Blocks

The framework produces seven kinds of artefact. Each has a fixed meaning, an ID, a home, and the phase that creates it.

| Building block | What it is | ID | Lives in | Created in |
|---|---|---|---|---|
| **Actor** | A role, person, or external system that interacts with (or has a stake in) the system | `ACT-001` | `actors.md` | Phase 0 |
| **Epic** | A large outcome that delivers one or more business goals; too big for one iteration | `EP-001` | `epics.md` | Phase 1 |
| **User story** | A small, valuable, testable slice of an epic from one actor's point of view: *As a … I want … so that …* | `US-001` | `stories.md` | Phase 1 |
| **Feature** | One cohesive capability of one epic at one level, written as one Gherkin `.feature` file | `FEAT-001` | `features/<level>/*.feature` | Phase 3 |
| **Rule** | One business rule the feature must obey. It is **exactly one EARS requirement**, written with Gherkin's `Rule:` keyword | the requirement's ID (`SYS-001`) | inside a `.feature` | Phase 1 (as acceptance criteria) → Phase 2 (as EARS) → Phase 3 (as `Rule:`) |
| **Scenario** | One concrete example that illustrates a rule | `SYS-001-S01` | under its `Rule:` | Phase 3 |
| **Gherkin** | The structured plain-language syntax that carries features, rules and scenarios: `Feature`, `Rule`, `Background`, `Scenario`, `Scenario Outline`, `Examples`, `Given`, `When`, `Then`, `And`, `But` | — | `.feature` files | Phase 3 |

**How they nest:**

```
ACT   Actor ............... who?        named in stories, STK requirements and Gherkin steps
BR    Business goal ....... why?
 EP    Epic ............... big outcome that realises ≥1 BR
  US    User story ........ As a <ACT>, I want <capability>, so that <benefit>
         └─ acceptance criteria ──► EARS requirements (STK → SYS → … → CMP, + VER)

FEAT  Feature ............. one .feature file = one capability of one epic at one level
 Rule  Rule ............... one per requirement:   Rule: SYS-001: <rule in business language>
  Scen Scenario ........... concrete example:      Scenario: SYS-001-S01: <title>
   T    Test .............. SYS-001-S01-T01
```

**Actors.** Every actor has a type:
- **Primary** — initiates interactions to get value (e.g. a customer). Each primary actor gets at least one named **persona** (e.g. `"alice"`) for use in Gherkin steps, so examples are concrete.
- **Supporting** — an external person or system the system relies on (e.g. a payment gateway, an email service). These often turn into `IF` interface requirements.
- **Offstage** — has a stake but never touches the system (e.g. a regulator). Their needs still become `STK` requirements, but they don't appear in `When` steps.

**Epics** each realise at least one `BR` business goal and contain at least one story.

**User stories** follow the *As a / I want / So that* form, name exactly one actor from the catalogue, belong to exactly one epic, carry a Must/Should/Could priority, and pass **INVEST** (Independent, Negotiable, Valuable, Estimable, Small, Testable); split any that don't. Each story lists **acceptance criteria** in plain language. These are the candidate **rules**: in Phase 2 each becomes one or more EARS requirements, and in Phase 3 each of those becomes a Gherkin `Rule:`.

**Status.** Every epic and story carries one status:
- 💡 **Proposed**: drafted and waiting for approval, either in Phase 1 or as a change raised later.
- ⏳ **Open**: approved but not yet finished.
- ✅ **Done**: a story is Done when every Test-verified requirement that traces to it (directly, or through Derives-From) has a Rule whose scenarios are all ✅. An epic is Done when all its non-retired stories are Done. A Done item gets a **completion record**: the date and the evidence that finished it.
- ⛔ **RETIRED**: withdrawn, but kept in the record with the reason.

A later change that invalidates a rule **reopens** every Done story (and epic) that traces to it. The reopening is logged in the item's history, and the item returns to the open work list.

**Features** group related rules into one `.feature` file. A feature belongs to one epic and sits at one level of the requirements V (§1.4). System- and acceptance-level features repeat the full narrative of the user stories they deliver, copied word for word from `stories.md`. Lower-level features (subsystem, interface, unit) list the stories they support and the requirement chain that links them.

**Rules** don't get their own ID scheme. A Rule *is* its requirement, so it is titled with the requirement's ID and carries the EARS sentence as its description. A rule can't drift from its requirement, and each scenario sits under the rule it illustrates.

### 1.3 The Phases

**Phase 0 — Intake.** The user provides a free-text description of what they want. Claude asks clarifying questions until the scope, actors, inputs/outputs, and success criteria are unambiguous. Output: an agreed problem statement (kept in `requirements.md`) and an **actor catalogue** in `actors.md` (`ACT-nnn`, type, goal, personas). **Gate: the user approves both before Phase 1.**

**Phase 1 — Epics & User Stories.** The business goals are written as `BR` requirements (EARS, usually Ubiquitous, usually verified by Analysis). Work is grouped into **epics** (`EP-nnn`) that realise them, and each epic is split into **user stories** (`US-nnn`), each with an actor, a priority, and plain-language acceptance criteria (candidate rules). Epics are recorded in `epics.md` and stories, in full, in `stories.md`. Both start as 💡 Proposed and become ⏳ Open on approval. `backlog.md` is generated alongside them, with every story under **Open work**. Coverage checks: every `BR` has an epic, every epic has a story, every primary actor appears in a story. **Gate: the user approves the epics and stories before Phase 2.**

**Phase 2 — Requirements (EARS).** Each story's acceptance criteria are formalised as EARS requirements in one of the six patterns:

| Pattern | Template |
|---|---|
| Ubiquitous | The `<system>` shall `<response>` |
| Event-driven | **When** `<trigger>`, the `<system>` shall `<response>` |
| State-driven | **While** `<state>`, the `<system>` shall `<response>` |
| Optional feature | **Where** `<feature is included>`, the `<system>` shall `<response>` |
| Unwanted behaviour | **If** `<condition>`, **then** the `<system>` shall `<response>` |
| Complex | Combinations of the above (When/While/If + shall) |

Each requirement is **classified by type/level** (business, stakeholder, system, subsystem, hardware, software, interface, component/unit, or verification & test — see §1.4). Each gets a typed ID (`SYS-001`), a priority (Must/Should/Could), a **parent link** to the requirement it derives from, a **story link** to the user story it refines (where direct), and a rationale. Higher-level requirements are decomposed into lower-level ones, and every requirement is paired with a verification & test requirement that says how it will be proven met. The links are written back into each story's record in `stories.md` (each acceptance criterion → its requirement ID, plus Refined by). **Gate: the user approves the requirements before Phase 3.**

**Phase 3 — Behaviours (Gherkin: Features → Rules → Scenarios).** Approved requirements are grouped into **features** (`FEAT-nnn`), one `.feature` file each, filed by level. Inside each feature, every requirement becomes one Gherkin **`Rule:`** titled with its ID. Under each rule, one or more **scenarios** (`SYS-001-S01`) cover the happy path, edge cases, and failure modes, with real example values and named personas. Each story's record gains links to the features that deliver it. **Gate: the user approves the feature files before Phase 4.**

**Phase 4 — Tests (Red).** Once the user names the target language and test framework, each scenario becomes one or more executable tests. Test names embed the scenario ID so traceability survives in the test runner output. All tests are written first and must fail for the right reason (missing implementation, not syntax errors). `backlog.md` is regenerated so each open story shows the rules it still needs. **Gate: the full suite runs red before any implementation.**

**Phase 5 — Implementation (Green → Refactor).** Classic TDD loop, one scenario at a time, Must stories first: write the minimum code to pass the current test, run the suite, refactor with the suite green, move on. No code is written that isn't demanded by a failing test. Each time a scenario goes green, its row in `traceability.md` is updated. When the last rule tracing to a story goes green, the story is marked ✅ Done in `stories.md` with its completion record, and `backlog.md` is regenerated so it drops out of Open work. When all of an epic's non-retired stories are Done, the epic is marked Done in `epics.md`.

**Phase 6 — Verification.** The traceability matrix is completed and audited:
- **Epics & stories:** every `BR` is realised by ≥1 epic, every epic has ≥1 story, every story has one epic, one catalogued actor and ≥1 requirement refining it, and every primary actor appears in ≥1 story.
- **Downward:** every requirement below Business derives from a parent, and every parent has a satisfying child.
- **Behaviour:** every feature belongs to one epic and one level, every rule maps to exactly one approved requirement and has ≥1 scenario, and no scenario sits outside a rule.
- **Across and up:** every functional requirement maps to a verification requirement and ≥1 passing test, every scenario maps to ≥1 passing test, and every test maps back to a requirement.
- **Records and views:** every story that isn't Done or retired appears under Open work in `backlog.md`, and no other story does. A story is Done in `stories.md` exactly when all its traced rules are ✅ in the matrix. Every Done story and epic has a completion record, and no actor, epic or story is defined anywhere but its record file.

At least one unbroken thread must run from a business goal through an epic and a story down to a passing unit/component test. Orphans in any direction are defects: a missing derivation, a missing test, an unused actor, or scope creep. Anything still under Open work at the end is reported as unfinished, with what it still needs.

### 1.4 Requirement Types & Levels

Real systems don't have one flat list of requirements. They have a **ladder** of them. A business goal is decomposed into stakeholder needs, those into system behaviour, that into subsystems, and those are allocated to hardware, software, and the interfaces between them, down to individual components or units. Each level is written by (and readable to) a different audience, and each level is **verified by a matching class of test**. This framework makes that ladder explicit so a single business goal can be traced all the way down to a unit test and back up again.

Every requirement carries a **type** that fixes its ID prefix, the question it answers, whom it derives from, and how it is verified:

| Level | Type | Prefix | Answers | Derives from | Typically verified by |
|---|---|---|---|---|---|
| 1 | Business | `BR` | *Why* are we building this? What business outcome? | — (top of the chain) | Business validation / KPIs (analysis) |
| 2 | Stakeholder | `STK` | What do users/stakeholders *need*? | `BR` (and refines a `US`) | Acceptance test / demonstration |
| 3 | System | `SYS` | What must the *whole system* do? | `STK` | System (end-to-end) test |
| 4 | Subsystem | `SUB` | What must each *subsystem* do? | `SYS` | Subsystem / integration test |
| 5 | Hardware | `HW` | What must the *hardware* do? | `SUB` (allocated) | Hardware test / inspection |
| 5 | Software | `SW` | What must the *software* do? | `SUB` (allocated) | Software test |
| 5 | Interface | `IF` | What crosses the *boundary* between two elements? | `SYS`/`SUB` (allocated) | Interface / contract test |
| 6 | Component / Unit | `CMP` | What must this individual *build block* do? | `HW`/`SW` | Unit test |
| — | Verification & Test | `VER` | *How* is a requirement proven met, and at what level? | any requirement it verifies | (defines the method — see below) |

**Actors, epics and stories alongside the ladder.** Actors, epics and user stories are not requirements. They are the agile view of the same intent, and they attach to the top of the ladder:

| Item | Attaches to | Link |
|---|---|---|
| Epic `EP` | Business `BR` | an epic *realises* ≥1 business goal |
| User story `US` | Stakeholder `STK` (and, where direct, `SYS`) | a requirement *refines* the story it formalises |
| Actor `ACT` | User stories, `STK` requirements, Gherkin personas | a story *is told by* one actor |

Requirements below `SYS` inherit their story through the derivation chain, so they don't need a direct story link.

**Verification methods (TAID).** Every `VER` requirement names one of four methods: **T**est (exercise it and observe), **A**nalysis (calculation, modelling, or simulation), **I**nspection (examine the artifact directly), **D**emonstration (show it operating in a representative scenario). In this framework most verification is by Test, where the Gherkin rules and scenarios (Phase 3) and the executable tests (Phase 4) *are* the verification evidence. Business and hardware requirements often use Analysis or Inspection instead.

**The requirements "V".** Decomposition runs down the left; verification runs up the right, each level checked by the class of test that matches it:

```
                   VALIDATION  (did we build the right thing?)

  Business (BR)  ⟷ Epics (EP) ........................  Business validation / KPIs
     |  derives                                              ^
     v                                                       |  validates
  Stakeholder (STK) ⟷ User stories (US) ..............  Acceptance / demonstration
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

  At every level from SYS down: Feature (.feature file) ⊃ Rule (= requirement) ⊃ Scenarios ⊃ Tests
```

**Two directions of trace.**
- **Downward (derivation / allocation):** every requirement below the top records the parent it *derives from*. No lower requirement may exist without a parent, and no parent is "done" until its children are satisfied. This is how scope creep and orphaned work are caught.
- **Upward + across (verification / validation):** every requirement is *verified by* at least one `VER` requirement whose method and level match its own. A requirement's type prefix flows into its rule, scenario and test IDs (`SYS-001-S01-T01` is a system-level test; `CMP-001-S01-T01` is a unit test), so the **level of any test is self-documenting**.

Small or flat projects don't need every rung. Use only the levels that apply (a pure library might have just `SW`, `IF`, and `CMP`), and the generic `REQ` prefix remains valid when levels genuinely don't matter. Whatever levels you *do* use must form an unbroken derive-from / verified-by chain, and the chain must still start from a story and an epic.

### 1.5 Traceability Scheme

```
ACT-001                  an actor (role or external system); personas like "alice" are instances
EP-001   realises        BR-001         an epic delivers ≥1 business goal
US-001   in epic         EP-001         a user story belongs to exactly one epic
US-001   told by         ACT-001        the "As a …" of the story
SYS-001                  a requirement, prefixed by its type (§1.4): BR/STK/SYS/SUB/HW/SW/IF/CMP/VER
STK-001  refines         US-001         a requirement formalising a story's acceptance criterion
SYS-001  derives from    STK-004        downward link to its parent requirement
SYS-001  verified by     VER-012        link to the verification & test requirement (method + level)
FEAT-001 in epic         EP-001         a .feature file: one capability, one epic, one level
Rule: SYS-001            the requirement written as a Gherkin Rule inside a feature
SYS-001-S01              scenario 1 for SYS-001, under its Rule
SYS-001-S01-T01          test 1 for scenario S01 (a system-level test; the prefix names the level)
```

- IDs are never reused. Deleted items are marked `RETIRED`, not renumbered. This applies to actors, epics, stories and features as well as requirements. Retired items stay in their record file with the reason and date.
- Changed requirements bump a revision suffix (`SYS-001r2`) and force re-review of their **children, rule, scenarios, tests, and verification requirements**. Changed stories (`US-001r2`) force re-review of the requirements that refine them. Any change that invalidates a rule reopens every Done story and epic that traces to it.
- Numbering runs **per type** (`SYS-001`, `SYS-002`, … independently of `SW-001`, `US-001`, `FEAT-001`, …).
- Rules have no separate number: a Rule is identified by its requirement ID.
- The matrix (`traceability.md`) is the single source of truth for test and coverage status. It spans the full chain: actor → epic → story → business goal → … → unit → rule → scenario → test. §1.6 says where every other fact lives.

### 1.6 Files: Records, Ledger and Work View

Each fact is written in exactly one place. The framework's files fall into three kinds:

| File | Kind | Holds | Changes when |
|---|---|---|---|
| `actors.md` | Record | Every actor: type, goal, personas; retired actors with reason | Phase 0; on amendment |
| `epics.md` | Record | Every epic: goal, what it realises, its stories, status, completion record, history | Phase 1; when its stories finish or reopen |
| `stories.md` | Record | Every story in full: narrative, acceptance criteria → requirements, features, status, completion record, history | Phase 1; links in Phases 2–3; status in Phase 5 |
| `requirements.md` | Record | Problem statement, every requirement and VER requirement | Phases 0–2; on amendment |
| `features/**/*.feature` | Record | Features, rules and scenarios | Phase 3; on amendment |
| `traceability.md` | Ledger | Status of every requirement, rule, scenario and test; story and actor coverage; audit | Every phase; every test-status change |
| `backlog.md` | Work view | **Open work**: only the stories that aren't Done, and what each still needs | Regenerated at every status change |

**Records** say what each item *is*. They are never pruned: a Done item keeps its completion record (the date and the passing evidence), a retired item keeps its reason, and every status change is logged in the item's history. Read together, `epics.md` and `stories.md` are the finished record of what was built and how it was proven, not a to-do list.

**The ledger** is the only place test status is written. Status flows one way:

```
test run → traceability.md   rule ✅ / 🔴
         → stories.md        story ✅ Done (or reopened)
         → epics.md          epic ✅ Done (or reopened)
         → backlog.md        Open work regenerated
```

**The work view** holds nothing of its own. `backlog.md` opens with an **Open work** summary listing only the stories that aren't Done, followed by what each still needs. It is regenerated from `stories.md` and `traceability.md`, and if it ever disagrees with them, they win. It starts with every approved story and ends as "Open work: none".

### 1.7 Design Decisions

- **Language agnostic:** Phases 0–3 are pure text and work for any target. The framework only asks for a language/framework at Phase 4.
- **Hard gates:** Claude must stop and wait for explicit approval between phases. This prevents an eager cascade of assumptions.
- **Stories before EARS:** stories are cheap to reshape. Agreeing on *who* wants *what* and *why* before formalising it keeps the EARS phase from encoding the wrong intent.
- **Record separate from to-do list:** the files that define epics and stories never shrink, so they stay complete after the work is finished, while `backlog.md` shrinks as work gets done. Keeping both in one file would mean either deleting finished work (losing the record) or keeping it (burying what's left).
- **Done is evidence, not opinion:** a story's status is derived from the ledger, and its completion record names the passing tests, so "Done" can be checked rather than taken on trust.
- **Rules are requirements:** a Gherkin `Rule:` is the requirement in business language. No separate rule ID means no drift between what the requirement says and what the examples illustrate.
- **Gherkin `Rule` support:** the `Rule:` keyword is part of modern Gherkin, but some runners don't support it (or don't support tags on it). If the chosen runner doesn't, flatten the file: drop the `Rule:` line, keep its EARS sentence as a comment, and put the rule's tags on each of its scenarios. Traceability is unchanged because scenario IDs already carry the requirement ID.
- **Paste-in prompt:** the prompt below is self-contained; no project setup or custom instructions required. Paste it as the first message of a fresh chat, then answer its questions.

---

## Part 2: The Prompt (paste everything in the box below into a new Claude chat)

````text
You are a BDD/TDD project bootstrapper. Your job is to take my plain-text
description of a piece of software and drive it through a strict, gated
pipeline: actors → epics & user stories → EARS requirements → Gherkin
features, rules & scenarios → failing tests → TDD implementation →
traceability verification. Follow these rules exactly.

## PIPELINE (never skip or merge phases)

PHASE 0 — INTAKE
- I will describe what I want in plain text.
- Ask clarifying questions (batched, numbered) until you can state the
  scope, actors, inputs/outputs, and success criteria without ambiguity.
- Produce:
    1. A short "Problem Statement".
    2. An ACTOR CATALOGUE (actors.md):
       ACT-nnn | name | type | goal/interest | personas
       Types: Primary (initiates interactions to get value), Supporting
       (external person/system the system relies on), Offstage (has a stake
       but never interacts). Give every Primary actor at least one named
       persona (e.g. "alice") for use in Gherkin.
- Ask me to approve both. Do not proceed until I say "approved" or
  equivalent.

PHASE 1 — EPICS & USER STORIES
- Write the business goals as BR requirements (EARS, usually Ubiquitous),
  each with a VER requirement (usually Analysis against a KPI).
- Group the work into EPICS: EP-nnn | title | goal | realises (BR ids) |
  priority | stories | status.
- Split each epic into USER STORIES: US-nnn, written as
    "As a <actor from the catalogue>, I want <capability>,
     so that <benefit>."
  Each story has exactly one actor and one epic, a priority
  (Must/Should/Could), and must pass INVEST (Independent, Negotiable,
  Valuable, Estimable, Small, Testable). Split any story that fails.
- Under each story, list ACCEPTANCE CRITERIA in plain language. These are
  the candidate RULES: each must become ≥1 EARS requirement in Phase 2.
- Every epic and story starts as Proposed and becomes Open when I approve
  it. Statuses: Proposed / Open / Done / RETIRED.
- Check: every BR is realised by ≥1 epic; every epic has ≥1 story; every
  Primary actor appears in ≥1 story. Report any unused actor.
- Output epics.md and stories.md (the records: every epic and story in
  full, with status and history) and backlog.md (the work view: an
  "Open work" summary at the top listing every story that isn't Done).
  Then STOP for my approval.

PHASE 2 — REQUIREMENTS (EARS)
- Convert every story's acceptance criteria into requirements using ONLY
  the six EARS patterns:
    Ubiquitous:  The <system> shall <response>
    Event:       When <trigger>, the <system> shall <response>
    State:       While <state>, the <system> shall <response>
    Optional:    Where <feature>, the <system> shall <response>
    Unwanted:    If <condition>, then the <system> shall <response>
    Complex:     valid combinations of the above
  Carry the Phase 1 BR requirements over unchanged.
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
- LINK TO STORIES: every STK requirement (and any SYS requirement that
  directly formalises an acceptance criterion) records the US-nnn it
  refines. Every story must be refined by ≥1 requirement. Name actors in
  STK requirements using the catalogue's role names. Write these links
  back into stories.md: each acceptance criterion → its requirement
  ID(s), plus Refined by.
- DERIVE downward: decompose higher-level requirements into lower-level
  ones. Every non-business requirement records the parent it derives from
  (or is allocated to). No orphan lower-level requirements; no parent left
  without children that satisfy it.
- VERIFY across: give every functional requirement at least one VER
  requirement stating the method — Test / Analysis / Inspection /
  Demonstration (TAID) — and the level at which it is checked. In this
  pipeline, Test-method verification is fulfilled by the Phase 3 rules and
  scenarios and the Phase 4 tests; Analysis/Inspection/Demonstration are
  recorded as VER requirements even when no automated test backs them.
- Each requirement gets: ID (typed, e.g. SYS-001), EARS pattern name,
  priority (Must/Should/Could), Derived-From link, Story link (where
  direct), Verified-By link, and a one-line rationale.
- Include unwanted-behaviour requirements for every plausible failure mode.
- Output requirements.md as a markdown table (grouped by level, highest
  first) and the updated stories.md, then STOP and ask for my approval,
  amendments, or additions.
  Renumber nothing; retire instead.

PHASE 3 — BEHAVIOURS (GHERKIN: FEATURES → RULES → SCENARIOS)
- FEATURES: group the approved requirements into features. A feature is
  one cohesive capability of ONE epic at ONE level, written as one
  .feature file and filed by level (features/system/, features/interface/,
  features/unit/, …).
    - Title: "Feature: FEAT-nnn: <capability>". Tag: @EP-nnn @FEAT-nnn
    - Description: the epic and level, then
        * system/acceptance level: the full narrative of every user story
          the feature delivers, copied word for word from stories.md,
          plus the actors and personas involved;
        * lower levels: "Supports: US-nnn via <requirement chain>".
- RULES: inside the feature, write one Gherkin `Rule:` block per approved
  requirement that is verified by Test.
    - Title: "Rule: <REQ-ID>: <the rule in business language>"
    - First description line: "EARS: <the exact requirement sentence>"
    - Tag: @<REQ-ID>, plus @US-nnn where the requirement refines a story
      directly. Scenarios inherit these tags.
    - Each such requirement appears as exactly one Rule in exactly one
      feature.
    - If the target runner lacks Rule support, flatten: drop the Rule line,
      keep the EARS sentence as a comment, and put the tags on each
      scenario.
- SCENARIOS: under each Rule, write one or more scenarios.
    - Name: "Scenario: <REQ-ID>-Snn: <short title>". The type prefix
      carries the verification level.
    - Cover happy path, boundary/edge cases, and failure modes.
    - Use concrete example values, never placeholders like "some input".
    - Use Scenario Outline + Examples tables where variations are tabular.
    - Given = context, When = single action, Then = observable outcome.
      No implementation detail in any step.
    - Refer to people only by catalogue role or persona name; introduce no
      actor that is not in the catalogue.
    - Use Background only for context shared by every scenario in the file.
- Output the complete .feature file(s), stories.md with each story's
  feature links added, and the updated traceability.md, then STOP for my
  approval.

PHASE 4 — TESTS (RED)
- Ask me for the target language and test framework if I have not already
  stated them. Everything before this point is language-agnostic.
- Convert every scenario into executable test(s). Embed the scenario ID in
  each test name (e.g. test_SYS_001_S01_valid_login, or the idiomatic
  equivalent for the chosen framework). Number multiple tests per scenario
  T01, T02, …. The test's type prefix pins its level: SYS-* tests are
  system tests, CMP-* tests are unit tests, IF-* tests are interface/
  contract tests. Organise the suite by level, and within a level by
  feature.
- Propose a project/file structure appropriate to the language.
- All tests must be runnable and must FAIL because the implementation is
  missing — not because of syntax errors or bad imports. Provide stub
  interfaces/signatures only where required for the suite to compile/run.
- Output the tests and instructions to run them, and regenerate
  backlog.md so each open story lists the rules it still needs. STOP and
  wait for me to confirm the suite runs red.

PHASE 5 — IMPLEMENTATION (GREEN → REFACTOR)
- Work one scenario at a time, in priority order (Must stories first).
- For each: write the MINIMUM code to pass its test(s), tell me to run the
  suite, then refactor only while green.
- Never write code not demanded by a currently failing test. If you think
  code is needed that no test demands, propose a new story/requirement/
  scenario first and route it back through the pipeline.
- After each scenario goes green, update its row in traceability.md.
- A story is Done when every Test-verified requirement that traces to it
  (directly, or through Derives-From) has a Rule whose scenarios are all
  green. When a story becomes Done:
    * mark it Done in stories.md and add a completion record: the date,
      each traced rule with its passing test IDs, and the status of any
      non-test VER that traces to it;
    * log it in the story's history;
    * regenerate backlog.md so the story drops out of Open work.
  When every non-retired story in an epic is Done, mark the epic Done in
  epics.md with its own completion record (date, each story with its
  Done date, business-check status).

PHASE 6 — VERIFICATION
- Produce the final traceability matrix, spanning the full chain:
    REQ id | Level | EARS pattern | Derives-From | Story | Feature |
    Scenario id(s) | Test id(s) | VER (method) | Status
  plus a story coverage table:
    Epic | Realises | Story | Actor | Refined by | Feature(s) |
    Rules (direct + inherited) | Rules green
- Audit ALL directions:
    * Epics & stories: every BR realised by ≥1 epic; every epic has ≥1
      story; every story has one epic, one catalogued actor and ≥1
      requirement refining it; every Primary actor appears in ≥1 story.
    * Records & views: every story that is not Done or RETIRED appears in
      backlog.md Open work, and no other story does; a story is Done in
      stories.md exactly when all its traced rules are green in the
      matrix; every Done story and epic has a completion record;
      epics.md and stories.md agree on which stories each epic contains;
      no actor, epic or story is defined outside its record file, and
      feature narratives match stories.md word for word.
    * Downward: every requirement (except Business) has a parent it derives
      from; every parent has ≥1 child that satisfies it. Orphans and
      childless parents are defects.
    * Behaviour: every feature belongs to one epic and one level; every
      Rule maps to exactly one approved requirement and has ≥1 scenario;
      no scenario sits outside a Rule.
    * Across/up: every functional requirement has ≥1 VER requirement, and
      every Test-method VER has ≥1 passing test. Scenario with no test, or
      test with no requirement, is a defect.
- Confirm at least one unbroken thread runs top to bottom (Business goal →
  epic → story → … → a passing unit/component test) and report any level
  that breaks the chain.
- Summarise coverage (stories Done, epics Done), report anything still in
  backlog.md Open work and what it needs, and list any RETIRED items.

## STANDING RULES
- Maintain these files throughout and reprint any that change:
    Records    actors.md, epics.md, stories.md, requirements.md, the
               .feature files. Never pruned: Done items keep their
               completion record, retired items their reason and date,
               and every status change is logged in the item's history.
    Ledger     traceability.md, the only place test status is written.
    Work view  backlog.md: starts with an "Open work" summary listing
               only stories that aren't Done, then what each still
               needs. Regenerate it from stories.md and traceability.md
               at every status change; it holds nothing of its own.
- IDs are permanent and typed: ACT, EP, US, FEAT for actors, epics,
  stories and features; BR/STK/SYS/SUB/HW/SW/IF/CMP/VER for requirements, numbered per
  type. Rules use their requirement's ID. Never renumber. Mark removed
  items RETIRED. Amended items become <TYPE>-NNNr2: an amended story
  invalidates the requirements that refine it; an amended requirement
  invalidates its children, rule, scenarios, tests, and verification
  requirements until re-reviewed. Any Done story or epic that traces to an
  invalidated rule is reopened: log it in its history and return it to
  Open work.
- Every requirement below Business must trace up to a parent (and, through
  the chain, to a story and epic) and be covered by a verification
  requirement; keep all links current as things change.
- At every gate, wait for my explicit approval before continuing.
- If I ask for something mid-pipeline that isn't covered by a story and
  requirement, route it through Phase 1 (a new or amended story, recorded
  as Proposed in stories.md) and Phase 2 (new REQ) first, then cascade.
- Be concise in commentary; be complete in artifacts.

Acknowledge these rules in one short paragraph, then ask me for my project
description to begin Phase 0.
````

---

## Part 3: File Templates

### 3.1 `actors.md`

```markdown
# Actors — <Project Name>
Record   ·   Revision: 1   ·   Date: YYYY-MM-DD

Types: Primary = initiates interactions to get value · Supporting = external
person/system the system relies on · Offstage = has a stake, never interacts.

| ID      | Actor              | Type     | Goal / interest                        | Personas (for Gherkin) |
|---------|--------------------|----------|----------------------------------------|------------------------|
| ACT-001 | Returning Customer | Primary  | Reach their account quickly and safely | "alice"                |
| ACT-002 | Security Auditor   | Primary  | Detect attacks on customer accounts    | "sam"                  |
| ACT-003 | Support Agent      | Offstage | Fewer password-reset calls             | —                      |

## Retired
| ID | Reason | Date |
|----|--------|------|
```

### 3.2 `epics.md`

```markdown
# Epics — <Project Name>
Record   ·   Revision: 1   ·   Date: YYYY-MM-DD

Every epic, whatever its status. Nothing is deleted. What's left to do is in backlog.md.
Status: 💡 Proposed · ⏳ Open · ✅ Done (all non-retired stories Done) · ⛔ RETIRED

## Index
| ID     | Epic                  | Realises | Priority | Stories        | Status  |
|--------|-----------------------|----------|----------|----------------|---------|
| EP-001 | Secure account access | BR-001   | Must     | US-001, US-002 | ⏳ Open |

## EP-001 — Secure account access
- **Goal:** Returning customers reach their account securely, without calling support.
- **Realises:** BR-001 · **Priority:** Must
- **Stories:** US-001, US-002 (0 of 2 Done)
- **Business check:** VER-001 (Analysis): password-reset tickets fall ≥ 30% in a quarter
- **Status:** ⏳ Open
- **Completion record:** — *(when Done: date · each story with its Done date · business-check status)*
- **History:** 2026-01-05 Proposed · 2026-01-06 Approved
```

### 3.3 `stories.md`

```markdown
# User Stories — <Project Name>
Record   ·   Revision: 1   ·   Date: YYYY-MM-DD

Every story, whatever its status. Nothing is deleted. What's left to do is in backlog.md.
Status: 💡 Proposed · ⏳ Open · ✅ Done · ⛔ RETIRED
Done = every Test-verified requirement that traces to the story (directly, or
through Derives-From) has a Rule whose scenarios are all ✅ in traceability.md.

## Index
| ID     | Title                              | Epic   | Actor   | Priority | Status  |
|--------|------------------------------------|--------|---------|----------|---------|
| US-001 | Sign in with username and password | EP-001 | ACT-001 | Must     | ⏳ Open |
| US-002 | Record failed sign-in attempts     | EP-001 | ACT-002 | Must     | ⏳ Open |

## US-001 — Sign in with username and password
- **Epic:** EP-001 · **Actor:** ACT-001 Returning Customer · **Priority:** Must
- **Story:** As a Returning Customer, I want to sign in with my username and
  password, so that I can reach my account without calling support.
- **Acceptance criteria → requirements:**
  1. Correct credentials sign me in and take me to my dashboard. → SYS-001
  2. Wrong credentials are refused with a clear message. → SYS-002
- **Refined by:** STK-001 · **Feature(s):** FEAT-001 · **INVEST:** ✔
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-01-05 Proposed · 2026-01-06 Approved

## US-002 — Record failed sign-in attempts
- **Epic:** EP-001 · **Actor:** ACT-002 Security Auditor · **Priority:** Must
- **Story:** As a Security Auditor, I want every failed sign-in attempt
  recorded, so that I can spot credential-stuffing attacks.
- **Acceptance criteria → requirements:**
  1. Every rejected attempt is recorded with the username tried. → SYS-002
- **Refined by:** STK-002 · **Feature(s):** FEAT-001 · **INVEST:** ✔
- **Status:** ⏳ Open
- **Completion record:** —
- **History:** 2026-01-05 Proposed · 2026-01-06 Approved
```

Once a story is finished, its status, completion record and history become the record of how it was proven. US-001, once Done:

```markdown
- **Status:** ✅ Done
- **Completion record:** 2026-02-14
  - Rules ✅: SYS-001 (SYS-001-S01-T01) · SYS-002 (SYS-002-S01-T01, -T02) ·
    SUB-001 (SUB-001-S01-T01) · SW-001 (SW-001-S01-T01) ·
    IF-001 (IF-001-S01-T01) · CMP-001 (CMP-001-S01-T01)
  - Other verification: VER-002 Demonstration — passed 2026-02-13 ·
    VER-008 Inspection — passed 2026-02-10
- **History:** 2026-01-05 Proposed · 2026-01-06 Approved · 2026-02-14 Done
```

If a later change invalidates one of those rules, the story goes back to ⏳ Open and its history gains an entry such as `2026-03-02 Reopened (SYS-001r2)`. The earlier Done entry stays in the history, and a new completion record is written when the story is Done again.

### 3.4 `backlog.md`

```markdown
# Backlog — <Project Name>
Work view   ·   Regenerated: YYYY-MM-DD
Derived from stories.md and traceability.md; holds nothing of its own.
Done and retired stories are not listed here: their record is in stories.md.

## Open work
**Progress:** 0 of 2 stories Done · 0 of 1 epics Done · **Next:** US-001

| Order | Story  | Title                              | Epic   | Actor   | Priority | Status  | Rules ✅ | Still needs                                                 |
|-------|--------|------------------------------------|--------|---------|----------|---------|---------|-------------------------------------------------------------|
| 1     | US-001 | Sign in with username and password | EP-001 | ACT-001 | Must     | ⏳ Open | 1 of 6  | SYS-002 🔴 · SUB-001 ⚠ · SW-001 🔴 · IF-001 🔴 · CMP-001 📝 |
| 2     | US-002 | Record failed sign-in attempts     | EP-001 | ACT-002 | Must     | ⏳ Open | 0 of 1  | SYS-002 🔴                                                  |

Order: Must → Should → Could, then by epic and story ID; 💡 Proposed stories
last, marked "awaiting approval". Before Phase 3 there are no rules yet, so
Rules ✅ shows — and Still needs names the phase the story is waiting on.

## What each open story still needs

### 1. US-001 — Sign in with username and password
- SYS-002 🔴 — implement until SYS-002-S01-T01, -T02 pass (Phase 5). Also unblocks US-002.
- SUB-001 ⚠ — no rule yet: write Rule SUB-001 and scenario SUB-001-S01 (Phase 3), then its test (Phase 4).
- SW-001 🔴 — implement until SW-001-S01-T01 passes (Phase 5).
- IF-001 🔴 — implement until IF-001-S01-T01 passes (Phase 5).
- CMP-001 📝 — write test CMP-001-S01-T01 (Phase 4), then implement.

### 2. US-002 — Record failed sign-in attempts
- SYS-002 🔴 — shared with US-001 (see above).

## Defects not tied to a story
None. (Orphan requirements, rules or tests from the last audit are listed here.)
```

When every story is Done, the file shrinks to:

```markdown
## Open work
None. All 2 stories and 1 epic are Done; see stories.md and epics.md.
```

### 3.5 `requirements.md`

```markdown
# Requirements — <Project Name>
Status: Draft | Approved   ·   Revision: 1   ·   Date: YYYY-MM-DD

## Problem Statement
<Approved Phase 0 statement.>

## Requirements  (grouped by level, highest first)

Columns: Derives-From = parent requirement (blank for Business);
Story = the user story this requirement directly refines (lower levels inherit
it through Derives-From); Verified-By = the VER requirement(s) that prove it.

| ID      | Level       | Pattern    | Priority | Requirement (EARS)                                                                          | Derives-From     | Story  | Verified-By | Rationale              |
|---------|-------------|------------|----------|---------------------------------------------------------------------------------------------|------------------|--------|-------------|------------------------|
| BR-001  | Business    | Ubiquitous | Must     | The product shall let returning customers reach their account securely.                      | —                | —      | VER-001     | Cut support-reset cost |
| STK-001 | Stakeholder | Event      | Must     | When a returning customer provides their credentials, they shall be granted account access. | BR-001           | US-001 | VER-002     | Primary user need      |
| STK-002 | Stakeholder | Event      | Must     | When a sign-in attempt fails, the product shall make a record of it available to security auditors. | BR-001   | US-002 | VER-010     | Attack detection       |
| SYS-001 | System      | Event      | Must     | When a user submits valid credentials, the system shall create an authenticated session.     | STK-001          | US-001 | VER-003     | Core login flow        |
| SYS-002 | System      | Unwanted   | Must     | If credentials are invalid, then the system shall reject the attempt and record it.          | STK-001, STK-002 | US-001, US-002 | VER-004 | Security       |
| SUB-001 | Subsystem   | Ubiquitous | Must     | The Identity subsystem shall authenticate users and manage their sessions.                   | SYS-001          | ↑      | VER-005     | Decomposition          |
| SW-001  | Software    | Event      | Must     | When given valid credentials, the auth service shall issue a signed session token.           | SUB-001          | ↑      | VER-006     | Session issuance       |
| IF-001  | Interface   | Event      | Must     | When a client POSTs credentials to /login, the API shall return a session token or 401.      | SUB-001          | ↑      | VER-007     | Client/service contract|
| HW-001  | Hardware    | Ubiquitous | Should   | The hardware security module shall store the session-signing key and never export it.        | SUB-001          | ↑      | VER-008     | Key protection         |
| CMP-001 | Component   | State      | Must     | While issuing a token, the token generator shall set a 15-minute expiry.                     | SW-001           | ↑      | VER-009     | Session hygiene        |

(↑ = story inherited through Derives-From.)

## Verification & Test Requirements

Method = TAID (Test / Analysis / Inspection / Demonstration). For Test-method
rows, the Evidence column names the rule/scenario/test IDs that fulfil it.

| ID      | Verifies | Level       | Method        | Acceptance / Evidence                                        |
|---------|----------|-------------|---------------|--------------------------------------------------------------|
| VER-001 | BR-001   | Business    | Analysis      | Password-reset support tickets fall ≥ 30% in a quarter       |
| VER-002 | STK-001  | Stakeholder | Demonstration | Returning customer signs in during an acceptance demo        |
| VER-003 | SYS-001  | System      | Test          | Rule SYS-001 → SYS-001-S01 → SYS-001-S01-T01                 |
| VER-004 | SYS-002  | System      | Test          | Rule SYS-002 → SYS-002-S01 → SYS-002-S01-T01, -T02           |
| VER-005 | SUB-001  | Subsystem   | Test          | Rule SUB-001 → SUB-001-S01 → SUB-001-S01-T01 (integration)   |
| VER-006 | SW-001   | Software    | Test          | Rule SW-001 → SW-001-S01 → SW-001-S01-T01                    |
| VER-007 | IF-001   | Interface   | Test          | Rule IF-001 → IF-001-S01 → IF-001-S01-T01 (contract test)    |
| VER-008 | HW-001   | Hardware    | Inspection    | HSM datasheet + config review confirm non-exportable key     |
| VER-009 | CMP-001  | Component   | Test          | Rule CMP-001 → CMP-001-S01 → CMP-001-S01-T01 (unit test)     |
| VER-010 | STK-002  | Stakeholder | Demonstration | Auditor reviews a recorded failed attempt in an acceptance demo |

## Retired
| ID      | Reason | Date |
|---------|--------|------|
```

### 3.6 `features/<level>/<capability>.feature`

A system-level feature delivers user stories directly, so it repeats their narrative:

```gherkin
# features/system/sign-in.feature
@EP-001 @FEAT-001
Feature: FEAT-001: Sign-in
  Epic: EP-001 Secure account access   ·   Level: system

  User stories delivered:
    US-001  As a Returning Customer, I want to sign in with my username and
            password, so that I can reach my account without calling support.
    US-002  As a Security Auditor, I want every failed sign-in attempt
            recorded, so that I can spot credential-stuffing attacks.

  Actors: Returning Customer (ACT-001, persona "alice"),
          Security Auditor (ACT-002, persona "sam")

  Background:
    Given "alice" is a registered Returning Customer with password "Correct-Horse-9"

  @SYS-001 @US-001
  Rule: SYS-001: Valid credentials open an authenticated session
    EARS: When a user submits valid credentials, the system shall create an authenticated session.

    Scenario: SYS-001-S01: Valid login creates a session
      Given "alice" is on the sign-in page
      When she submits username "alice" and password "Correct-Horse-9"
      Then an authenticated session is created for "alice"
      And she is redirected to her dashboard

  @SYS-002 @US-001 @US-002
  Rule: SYS-002: Invalid credentials are rejected and recorded
    EARS: If credentials are invalid, then the system shall reject the attempt and record it.

    Scenario Outline: SYS-002-S01: Invalid credentials are rejected
      Given the sign-in page is open
      When username "<username>" and password "<password>" are submitted
      Then the attempt is rejected with message "Invalid credentials"
      And "sam" can see a failed attempt recorded for username "<username>"

      Examples:
        | username | password        |
        | alice    | wrong-password  |
        | bob      | Correct-Horse-9 |
```

A lower-level feature serves stories indirectly, so it states the chain instead of the narrative:

```gherkin
# features/unit/token-generator.feature
@EP-001 @FEAT-002
Feature: FEAT-002: Session token generation
  Epic: EP-001 Secure account access   ·   Level: component (unit)
  Supports: US-001 via STK-001 → SYS-001 → SUB-001 → SW-001 → CMP-001

  @CMP-001
  Rule: CMP-001: Every issued token expires 15 minutes after issue
    EARS: While issuing a token, the token generator shall set a 15-minute expiry.

    Scenario: CMP-001-S01: Token expiry is 15 minutes after issue
      Given the clock reads "2026-01-01T09:00:00Z"
      When a session token is issued for user "alice"
      Then the token's expiry is "2026-01-01T09:15:00Z"
```

Each `.feature` file sits at exactly one point on the requirements V and belongs to exactly one epic, so its rules, scenarios and the tests they drive are all at the same level.

**Gherkin checklist**
- `Feature:` = one capability, one epic, one level; tagged `@EP-nnn @FEAT-nnn`.
- `Rule:` = one requirement; titled with its ID; EARS sentence as first description line; tagged `@<REQ-ID>` (+ `@US-nnn` where direct).
- `Scenario:` / `Scenario Outline:` = one example of its rule; named `<REQ-ID>-Snn: …`; concrete values; one `When`.
- `Background:` = context shared by every scenario in the file, nothing more.
- People appear only as catalogue roles or personas.
- Story narratives are copied word for word from `stories.md`. Features reference stories by ID and never define new ones.

### 3.7 `traceability.md`

```markdown
# Traceability Matrix — <Project Name>

Spans the full chain: actor → epic → story → requirement level → parent → rule → scenario → test → verification.

## Requirement coverage

| REQ ID  | Level       | Derives-From     | Story          | Feature  | Pattern    | Scenario ID(s) | Test ID(s)                       | VER (method)       | Status          |
|---------|-------------|------------------|----------------|----------|------------|----------------|----------------------------------|--------------------|-----------------|
| BR-001  | Business    | —                | —              | —        | Ubiquitous | —              | —                                | VER-001 (Analysis) | 📊 KPI-tracked  |
| STK-001 | Stakeholder | BR-001           | US-001         | —        | Event      | —              | —                                | VER-002 (Demo)     | 📊 Acceptance   |
| STK-002 | Stakeholder | BR-001           | US-002         | —        | Event      | —              | —                                | VER-010 (Demo)     | 📊 Acceptance   |
| SYS-001 | System      | STK-001          | US-001         | FEAT-001 | Event      | SYS-001-S01    | SYS-001-S01-T01                  | VER-003 (Test)     | ✅ Green        |
| SYS-002 | System      | STK-001, STK-002 | US-001, US-002 | FEAT-001 | Unwanted   | SYS-002-S01    | SYS-002-S01-T01, SYS-002-S01-T02 | VER-004 (Test)     | 🔴 Red          |
| SUB-001 | Subsystem   | SYS-001          | ↑              | —        | Ubiquitous | —              | —                                | VER-005 (Test)     | ⚠ No rule/scenario |
| SW-001  | Software    | SUB-001          | ↑              | FEAT-003 | Event      | SW-001-S01     | SW-001-S01-T01                   | VER-006 (Test)     | 🔴 Red          |
| IF-001  | Interface   | SUB-001          | ↑              | FEAT-004 | Event      | IF-001-S01     | IF-001-S01-T01                   | VER-007 (Test)     | 🔴 Red          |
| HW-001  | Hardware    | SUB-001          | ↑              | —        | Ubiquitous | —              | —                                | VER-008 (Inspect)  | 🔍 Inspection   |
| CMP-001 | Component   | SW-001           | ↑              | FEAT-002 | State      | CMP-001-S01    | —                                | VER-009 (Test)     | 📝 Scenario only|

## Story coverage

Rules = Test-verified requirements tracing to the story, direct + inherited through Derives-From.
A story is Done (in stories.md) exactly when Rules ✅ equals the total.

| Epic   | Realises | Story  | Actor   | Refined by | Feature(s)                              | Rules (direct + inherited)                          | Rules ✅ |
|--------|----------|--------|---------|------------|-----------------------------------------|-----------------------------------------------------|---------|
| EP-001 | BR-001   | US-001 | ACT-001 | STK-001    | FEAT-001 + FEAT-002, FEAT-003, FEAT-004 | SYS-001, SYS-002 + SUB-001, SW-001, IF-001, CMP-001 | 1 of 6  |
| EP-001 | BR-001   | US-002 | ACT-002 | STK-002    | FEAT-001                                | SYS-002                                             | 0 of 1  |

## Actor coverage

| Actor   | Type     | Stories | Personas used in features |
|---------|----------|---------|---------------------------|
| ACT-001 | Primary  | US-001  | "alice" (FEAT-001, FEAT-002) |
| ACT-002 | Primary  | US-002  | "sam" (FEAT-001)          |
| ACT-003 | Offstage | —       | — (served via BR-001 / VER-001) |

Status legend: ⚠ gap · 📝 scenario only · 🔴 tests failing (expected pre-impl.) · ✅ passing · 📊 non-test verification (Analysis/Demo) · 🔍 Inspection · ⛔ RETIRED
Story and epic status are recorded in stories.md and epics.md, derived from this file. Open work is listed in backlog.md.

Audit rules:
- Epics & stories: any BR with no epic, epic with no story, story with no actor/epic/refining requirement, or Primary actor with no story, is a defect. (Offstage actors may have no story if a BR or STK serves them.)
- Downward: any requirement below Business with no Derives-From, or any parent with no child, is a defect.
- Behaviour: any Test-verified requirement with no Rule, Rule with no scenario, scenario outside a Rule, or feature spanning two epics or two levels, is a defect.
- Across: any functional requirement with no VER, any ⚠ row, or any test with no requirement, is a defect.
- Records & views: any story that isn't Done or retired but is missing from backlog.md Open work, any Done or retired story listed there, any story whose Done status disagrees with its Rules ✅, any Done story or epic without a completion record, or any actor, epic or story defined outside its record file, is a defect.
- Thread check: at least one unbroken line must run Business → Epic → Story → … → passing test.
```

### 3.8 Test naming convention (language-agnostic)

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

### 3.9 Suggested project layout (adapt per language)

```
project/
├── docs/
│   ├── actors.md            # record: every actor and persona
│   ├── epics.md             # record: every epic, status, completion record
│   ├── stories.md           # record: every user story in full, status, completion record
│   ├── requirements.md      # record: typed requirements + VER requirements
│   ├── traceability.md      # ledger: test status + coverage, epic → story → … → test
│   └── backlog.md           # work view: Open work (stories not Done), regenerated
├── features/                # one .feature per capability (FEAT-nnn), filed by level
│   ├── system/              #   Rules @SYS-* + story narratives
│   ├── subsystem/           #   Rules @SUB-*
│   ├── interface/           #   Rules @IF-*  (contract tests)
│   ├── software/            #   Rules @SW-*
│   └── unit/                #   Rules @CMP-*
├── tests/                   # mirrors the levels above (or idiomatic location)
│   ├── system/  interface/  unit/  …
└── src/                     # implementation, written only under Phase 5
```

Not every project needs every level. Keep only the folders whose levels you actually use. A test's location, its feature's level and its ID prefix should all agree on which rung of the requirements V it verifies.
