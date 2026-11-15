@EP-08 @FEAT-074
Feature: FEAT-074: Self test
  Epic: EP-08 Verification and emulation   ·   Level: unit

  Supports: US-24 via CMP-26

  @CMP-26
  Rule: CMP-26: mimmo.c: self_test
    EARS: When `self_test()` is called, it shall evaluate the four SW-MON-04 checks. `recurse(n)` shall be a genuinely recursive, non-inlined function that returns n(n+1)/2. `vla_after_spill(n)` shall call `recurse(40)` before declaring `char buf[n]`, and return 820 + (n−1) mod 256. It shall leave line 7 disabled afterwards.

    @qemu @SYS-21 @SW-MON-04 @VER-SYS-17 @VER-STK-11
    Scenario: CMP-26-S01: Self test passes after a flash boot
      Given the firmware is booted in QEMU from flash
      When I enter "s"
      Then the console shows each of:
        | text                           |
        | recursion 200 deep: 20100 (ok) |
        | VLA after spill:   919 (ok)    |
        | software irq:      1 hit (ok)  |
        | (ok)                           |
        | all ok                         |
      And the console does not show "BAD"

    @host @gtest @VER-CMP-13
    Scenario: CMP-26-S02: The self test passes on the simulated CPU
      Given the 100 Hz tick is running
      When the operator enters "s"
      Then the console shows "recursion 200 deep: 20100 (ok)"
      And the console shows "VLA after spill:   919 (ok)"
      And the console shows "software irq:      1 hit (ok)"
      And the console shows "all ok"
      And CPU line 7 is disabled afterwards
