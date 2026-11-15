@EP-06 @FEAT-052
Feature: FEAT-052: Register windows and alloca
  Epic: EP-06 Exception and interrupt handling   ·   Level: software

  Supports: US-18 via STK-11 → SYS-15 → SUB-EXC-01 → SW-EXC-01

  @SW-EXC-01
  Rule: SW-EXC-01: Window handler sequences
    EARS: When a window overflow or underflow exception is taken, its handler shall store or reload:
      - `a0`–`a3` at callee-SP −16 to −4;
      - for call8 frames, also `a4`–`a7` at caller-SP −32 to −20;
      - for call12 frames, also `a4`–`a11` at caller-SP −48 to −20.
      It shall then return with `rfwo` or `rfwu`.

  @SW-EXC-04
  Rule: SW-EXC-04: Alloca handler sequence
    EARS: When the alloca exception is dispatched, the handler shall:
      1. set `PS.OWB` to the faulting window;
      2. restore the faulting function's `a0` from `EXCSAVE1`;
      3. rotate to the caller's window according to `a0` bits 31–30 (01: call4, 10: call8, 11: call12);
      4. jump to the matching underflow handler.
