@EP-06 @FEAT-054
Feature: FEAT-054: Register windows and alloca
  Epic: EP-06 Exception and interrupt handling   ·   Level: unit

  Supports: US-18 via CMP-03

  @CMP-03
  Rule: CMP-03: vectors.S: window overflow/underflow 8
    EARS: When entered at `+0x080`, the overflow-8 handler shall store `a0`–`a3` at `[a9−16..a9−4]`, and `a4`–`a7` at `[[a1−12]−32..−20]`. When entered at `+0x0C0`, the underflow-8 handler shall reload them from the same addresses. Each handler fits in 64 bytes.

    @qemu @SYS-15 @SUB-EXC-01 @SW-EXC-01 @VER-SYS-11 @VER-STK-09
    Scenario: CMP-03-S01: Recursion 200 frames deep
      Given the firmware is booted in QEMU from flash
      When I enter "s"
      Then the console shows "recursion 200 deep: 20100 (ok)"

  @CMP-04
  Rule: CMP-04: vectors.S: window overflow/underflow 12
    EARS: When entered at `+0x100`, the overflow-12 handler shall store `a0`–`a3` at `[a13−16..a13−4]`, and `a4`–`a11` at `[[a1−12]−48..−20]`. When entered at `+0x140`, the underflow-12 handler shall reload them from the same addresses. Each handler fits in 64 bytes.

    @qemu @pending @VER-CMP-02
    Scenario: CMP-04-S01: call12 frames are spilled and filled
      Given a build variant with an assembly routine that calls recurse(100) with call12 from a frame reserving the 32-byte extra save area
      When the routine runs
      Then it returns 5050

  @CMP-07
  Rule: CMP-07: vectors.S: _alloca_handler
    EARS: When entered with `EXCCAUSE` = 5, the handler shall:
      1. rotate the window back by one;
      2. copy the faulting `WINDOWBASE` into `PS.OWB`;
      3. restore the faulting function's `a0` from `EXCSAVE1`;
      4. jump to `_WindowUnderflow4` if `a0[31]` = 0, to `_WindowUnderflow8` if `a0[31:30]` = 10, or to `_WindowUnderflow12` if they are 11, rotating one more window before each of the last two choices.

    @qemu @SYS-15 @SUB-EXC-02 @SW-EXC-04 @VER-SYS-11 @VER-STK-09
    Scenario: CMP-07-S01: A variable-length array with its caller spilled
      Given the firmware is booted in QEMU from flash
      When I enter "s"
      Then the console shows "VLA after spill:   919 (ok)"
