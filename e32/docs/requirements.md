# Requirements

Record. The problem statement, and the index of the requirement files. The
requirements themselves are in [`requirements/`](requirements/), one file per
type; [`README.md`](README.md#entry-format) gives the entry format.

## Problem statement

*Status: 💡 Proposed (written during the v2.0 migration from the README and the
business requirements; approve or amend at the Phase 0 gate).*

Learners and developers who want to understand or build on the ESP32 at the
lowest level have no small, complete reference: vendor SDKs hide the boot,
vector and interrupt paths behind hundreds of thousands of lines and ROM
calls. e32 is a bare-metal firmware package for a plain ESP32 (Xtensa LX6,
e.g. an ESP32-WROOM-32 DevKit) that builds with only a bare cross-compiler,
`make` and a host C compiler, uses no SDK, no C library and no ROM code at
run time, boots from flash or over the serial port, and gives an operator a
serial memory monitor with GPIO control, interrupts, a timer tick, fault
reports and a self test.

It is used by the actors in [`actors.md`](actors.md): firmware developers,
learners, bench operators and testers, and the maintainer. Inputs are the
sources and a serial terminal; outputs are a ROM-loadable image and the
console behaviour. It succeeds when the business requirements' KPIs are met
(at most 2,500 source lines, no vendor code, runs on the cheapest boards,
most requirements verifiable in QEMU) and every story in
[`stories.md`](stories.md) is Done.

## Requirement files

| Level | Type | File | Count |
|---|---|---|---|
| 1 | Business | [BR.md](requirements/BR.md) | 6 |
| 2 | Stakeholder | [STK.md](requirements/STK.md) | 20 |
| 3 | System | [SYS.md](requirements/SYS.md) | 32 |
| 4 | Subsystem | [SUB.md](requirements/SUB.md) | 35 |
| 5 | Hardware | [HW.md](requirements/HW.md) | 14 |
| 5 | Software | [SW.md](requirements/SW.md) | 63 |
| 5 | Interface | [IF.md](requirements/IF.md) | 16 |
| 6 | Component | [CMP.md](requirements/CMP.md) | 40 |
| — | Verification | [VER.md](requirements/VER.md) | 128 |

Every requirement has a priority (all Must in the migrated baseline), a
rationale, its parent (Derives from), and its VER entry (Verified by).
Stakeholder requirements, and system requirements that formalise an
acceptance criterion directly, name the user story they refine (Story).

## Retired

| ID | Reason | Date |
|---|---|---|
