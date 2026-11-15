# Stakeholder requirements (STK)

Level 2. What do the users and stakeholders *need*? Each derives from one or
more business requirements, and is verified by acceptance demonstration
(`features/acceptance.feature`). Roles are defined in
[`../actors-and-roles.md`](../actors-and-roles.md).

---

### STK-01 — Build with a bare toolchain
- **Type:** Stakeholder
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The developer needs to build the firmware from source with only a bare cross-compiler, GNU make and a host C compiler.
- **Derives from:** BR-02
- **Story:** US-01, US-02
- **Role:** Developer
- **Rationale:** Needed to meet BR-02 (Independence from vendor SDKs and run-time ROM code).
- **Verified by:** VER-STK-01

### STK-02 — Reproduce the toolchain
- **Type:** Stakeholder
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The maintainer needs to rebuild the cross-compiler from pinned sources when a prebuilt one is unavailable or untrusted.
- **Derives from:** BR-02
- **Story:** US-04
- **Role:** Maintainer
- **Rationale:** Needed to meet BR-02 (Independence from vendor SDKs and run-time ROM code).
- **Verified by:** VER-STK-02

### STK-03 — Run without writing flash
- **Type:** Stakeholder
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When iterating, the developer needs to load and run the firmware in RAM over the serial port without writing flash.
- **Derives from:** BR-01, BR-05
- **Story:** US-03, US-05
- **Role:** Developer
- **Rationale:** Needed to meet BR-01 (A complete, learnable bare-metal reference); BR-05 (Verifiable largely without hardware).
- **Verified by:** VER-STK-03

### STK-04 — Run at every reset
- **Type:** Stakeholder
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When the work is done, the developer needs to store the firmware in flash, so that it starts by itself at every reset.
- **Derives from:** BR-04
- **Story:** US-03, US-06
- **Role:** Developer
- **Rationale:** Needed to meet BR-04 (A foundation for application projects).
- **Verified by:** VER-STK-03

### STK-05 — Serial console
- **Type:** Stakeholder
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The operator needs a serial console at 115200 8N1 that shows a start-up banner and a prompt.
- **Derives from:** BR-01
- **Story:** US-09, US-11
- **Role:** Operator
- **Rationale:** Needed to meet BR-01 (A complete, learnable bare-metal reference).
- **Verified by:** VER-STK-04

### STK-06 — Inspect and modify memory interactively
- **Type:** Stakeholder
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The operator needs to read, write and dump memory and registers, and to call code, from the console, with typing errors rejected harmlessly.
- **Derives from:** BR-01
- **Story:** US-10, US-12, US-13, US-14
- **Role:** Operator
- **Rationale:** Needed to meet BR-01 (A complete, learnable bare-metal reference).
- **Verified by:** VER-STK-05

### STK-07 — Drive and read pins safely
- **Type:** Stakeholder
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The operator needs to drive and read GPIO pins and select pin functions from the console, without being able to disturb the flash pins or drive input-only pins.
- **Derives from:** BR-01, BR-04
- **Story:** US-15, US-16
- **Role:** Operator
- **Rationale:** Needed to meet BR-01 (A complete, learnable bare-metal reference); BR-04 (A foundation for application projects).
- **Verified by:** VER-STK-06

### STK-08 — Attach code to interrupts
- **Type:** Stakeholder
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The integrator needs to route peripheral interrupts to the CPU and attach C handlers to them, and to protect shared data with critical sections.
- **Derives from:** BR-04
- **Story:** US-19, US-21, US-29
- **Role:** Integrator
- **Rationale:** Needed to meet BR-04 (A foundation for application projects).
- **Verified by:** VER-STK-07

### STK-09 — Time base
- **Type:** Stakeholder
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The integrator needs a periodic tick with an uptime counter, and a microsecond busy-wait delay.
- **Derives from:** BR-04
- **Story:** US-20, US-29
- **Role:** Integrator
- **Rationale:** Needed to meet BR-04 (A foundation for application projects).
- **Verified by:** VER-STK-07

### STK-10 — Understand and recover from crashes
- **Type:** Stakeholder
- **EARS:** Unwanted behaviour
- **Priority:** Must
- **Statement:** If the firmware crashes, then the developer needs a report giving the cause, the location and the registers, and a way to reboot without touching the board.
- **Derives from:** BR-01, BR-04
- **Story:** US-22, US-23, US-26
- **Role:** Developer
- **Rationale:** Needed to meet BR-01 (A complete, learnable bare-metal reference); BR-04 (A foundation for application projects).
- **Verified by:** VER-STK-08

### STK-11 — Ordinary C semantics
- **Type:** Stakeholder
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The developer needs deep call chains and variable-length arrays to work as in ordinary hosted C, without knowing the CPU's register-window scheme.
- **Derives from:** BR-04
- **Story:** US-18
- **Role:** Developer
- **Rationale:** Needed to meet BR-04 (A foundation for application projects).
- **Verified by:** VER-STK-09

### STK-12 — No spontaneous resets
- **Type:** Stakeholder
- **EARS:** State-driven
- **Priority:** Must
- **Statement:** While the firmware is running, the operator needs the board not to reset by itself.
- **Derives from:** BR-04
- **Story:** US-07
- **Role:** Operator
- **Rationale:** Needed to meet BR-04 (A foundation for application projects).
- **Verified by:** VER-STK-10

### STK-13 — Verify in an emulator
- **Type:** Stakeholder
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The tester needs to run the firmware in an emulator that uses the real ESP32 boot ROM, in both boot modes.
- **Derives from:** BR-05
- **Story:** US-25
- **Role:** Tester
- **Rationale:** Needed to meet BR-05 (Verifiable largely without hardware).
- **Verified by:** VER-STK-11

### STK-14 — Built-in self test
- **Type:** Stakeholder
- **EARS:** Event-driven
- **Priority:** Must
- **Statement:** When a board or a build is in doubt, the operator needs one command that checks the core mechanisms and reports pass or fail, and commands that raise each fault type on purpose.
- **Derives from:** BR-04, BR-05
- **Story:** US-24, US-26
- **Role:** Operator, Tester
- **Rationale:** Needed to meet BR-04 (A foundation for application projects); BR-05 (Verifiable largely without hardware).
- **Verified by:** VER-STK-11

### STK-15 — Explanatory documentation
- **Type:** Stakeholder
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The learner needs documentation that explains the boot, interrupt and fault paths, the memory map and the APIs, and maps each file to Rubini's LPC1343 original.
- **Derives from:** BR-01
- **Story:** US-27
- **Role:** Learner
- **Rationale:** Needed to meet BR-01 (A complete, learnable bare-metal reference).
- **Verified by:** VER-STK-12

### STK-16 — Sign of life without a console
- **Type:** Stakeholder
- **EARS:** Optional feature
- **Priority:** Must
- **Statement:** Where no serial console is available, the operator needs a visible sign that the firmware runs.
- **Derives from:** BR-03
- **Story:** US-17
- **Role:** Operator
- **Rationale:** Needed to meet BR-03 (Runs on the cheapest commodity boards).
- **Verified by:** VER-STK-06

### STK-17 — Basic board is enough
- **Type:** Stakeholder
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The developer needs the firmware to fit and run on a basic ESP32 module with no PSRAM.
- **Derives from:** BR-03
- **Story:** US-08
- **Role:** Developer
- **Rationale:** Needed to meet BR-03 (Runs on the cheapest commodity boards).
- **Verified by:** VER-STK-13

### STK-18 — Nothing from vendors inside
- **Type:** Stakeholder
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The maintainer needs the firmware to contain no vendor or third-party code and to call no boot-ROM routines once running.
- **Derives from:** BR-02, BR-06
- **Story:** US-01
- **Role:** Maintainer
- **Rationale:** Needed to meet BR-02 (Independence from vendor SDKs and run-time ROM code); BR-06 (Original, freely distributable work).
- **Verified by:** VER-STK-01

### STK-19 — No lost input
- **Type:** Stakeholder
- **EARS:** State-driven
- **Priority:** Must
- **Statement:** While the firmware is busy, the operator needs typed or pasted input to be kept until it is read.
- **Derives from:** BR-04
- **Story:** US-10
- **Role:** Operator
- **Rationale:** Needed to meet BR-04 (A foundation for application projects).
- **Verified by:** VER-STK-04

### STK-20 — Traceable, checkable requirements
- **Type:** Stakeholder
- **EARS:** Ubiquitous
- **Priority:** Must
- **Statement:** The maintainer needs every requirement linked to its parent and its verification, with an automatic check for broken links and missing verification.
- **Derives from:** BR-02, BR-05
- **Story:** US-28
- **Role:** Maintainer
- **Rationale:** Needed to meet BR-02 (Independence from vendor SDKs and run-time ROM code); BR-05 (Verifiable largely without hardware).
- **Verified by:** VER-STK-12
