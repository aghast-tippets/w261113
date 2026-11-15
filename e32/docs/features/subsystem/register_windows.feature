@EP-06 @FEAT-051
Feature: FEAT-051: Register windows and alloca
  Epic: EP-06 Exception and interrupt handling   ·   Level: subsystem

  Supports: US-18 via STK-11 → SYS-15 → SUB-EXC-01

  @SUB-EXC-01
  Rule: SUB-EXC-01: Register-window spill and fill
    EARS: When the CPU raises a window overflow or underflow exception for a call4, call8 or call12 frame, the exception subsystem shall store or reload that frame's registers in the stack areas defined by the windowed ABI (IF-15), and resume.

  @SUB-EXC-02
  Rule: SUB-EXC-02: Alloca fix-up
    EARS: When a `movsp` raises the alloca exception because the caller's frame is spilled, the exception subsystem shall reload the caller's frame and re-execute the `movsp`.
