# Business requirements (BR)

Level 1. *Why* are we building this? These requirements are the top of the
derivation chain, so they derive from nothing. They are verified by analysis
of KPIs, or by inspection.

Context: e32 continues Alessandro Rubini's teaching material. His *bbfs*
notes argue for a minimal dependency surface ("the only dependency you get
is with busybox"), and his *cortex-m3* notes build an LPC1343 system from
scratch for his students. e32 applies both ideas to the ESP32.

---

### BR-01 — A complete, learnable bare-metal reference
- **Type:** Business
- **EARS:** Ubiquitous
- **Statement:** The project shall provide a bare-metal ESP32 code base that a learner with C and Unix experience can read and understand end to end, from reset to interrupts and faults.
- **Derives from:** —
- **Rationale:** Rubini's packages exist to give students a working base they fully understand. Vendor SDKs hide the boot, the vector and the interrupt paths behind hundreds of thousands of lines.
- **KPI:** Total firmware, tool and build source of at most 2,500 lines including comments, with every source file mapped to a purpose in the README.
- **Verified by:** VER-BR-01

### BR-02 — Independence from vendor SDKs and run-time ROM code
- **Type:** Business
- **EARS:** Ubiquitous
- **Statement:** The project shall depend on no vendor SDK, C library or boot-ROM routine at run time, so that it stays buildable and maintainable for years without tracking vendor releases.
- **Derives from:** —
- **Rationale:** Rubini's bbfs argument: every dependency is a future upgrade cost. A package that needs only a compiler is cheap to keep alive.
- **KPI:** The dependency inventory contains only the cross toolchain (with the ESP32 core-configuration overlay), a host C compiler, GNU make, and esptool as a byte transport.
- **Verified by:** VER-BR-02

### BR-03 — Runs on the cheapest commodity boards
- **Type:** Business
- **EARS:** Ubiquitous
- **Statement:** The firmware shall run on a basic ESP32 module (for example ESP32-WROOM-32 on a DevKit board) without PSRAM or extra hardware.
- **Derives from:** —
- **Rationale:** Students and hobbyists use boards costing a few euros. Rubini's original target was a 13 EUR Olimex board.
- **KPI:** The memory budget uses at most 50 % of internal IRAM and DRAM; no external memory.
- **Verified by:** VER-BR-03

### BR-04 — A foundation for application projects
- **Type:** Business
- **EARS:** Ubiquitous
- **Statement:** The project shall provide the mechanisms an application needs (console, GPIO, interrupts, time base and fault reporting) so that applications can be added without modifying startup or vector code.
- **Derives from:** —
- **Rationale:** The value of a base is measured by what can be built on it.
- **KPI:** A new interrupt-driven feature can be added through the public APIs only, as demonstrated by the self test's software-interrupt check.
- **Verified by:** VER-BR-04

### BR-05 — Verifiable largely without hardware
- **Type:** Business
- **EARS:** Ubiquitous
- **Statement:** The project shall be verifiable for most of its system requirements in an emulator that runs the real ESP32 boot ROM.
- **Derives from:** —
- **Rationale:** Emulation cuts test cost and cycle time, and allows automated regression testing.
- **KPI:** At least 80 % of system (`SYS`) requirements have a verification executable in QEMU.
- **Verified by:** VER-BR-05

### BR-06 — Original, freely distributable work
- **Type:** Business
- **EARS:** Ubiquitous
- **Statement:** The project's firmware and tools shall consist of original work containing no source copied from ESP-IDF, Arduino, newlib or other third-party firmware, so that the maintainer can license it freely.
- **Derives from:** —
- **Rationale:** Licensing freedom for teaching and reuse. The register-window spill and fill sequences follow the Xtensa ISA's architecturally defined form, which is a specification rather than borrowed code.
- **KPI:** An inspection finds no third-party source in the tree, apart from the toolchain overlay that the build script fetches and that is never compiled into the firmware.
- **Verified by:** VER-BR-06
