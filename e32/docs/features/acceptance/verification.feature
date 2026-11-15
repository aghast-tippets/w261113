@EP-08 @FEAT-079
Feature: FEAT-079: Stakeholder acceptance: Verification and emulation
  Epic: EP-08 Verification and emulation   ·   Level: acceptance

  User stories delivered:
    US-25  As a tester, I want to run the firmware in QEMU with the real boot
           ROM, so that I can verify most requirements without a board.

  Actors: Bench operator / tester (ACT-H3, persona "olga")

  @STK-13 @US-25
  Rule: STK-13: Verify in an emulator
    EARS: The tester needs to run the firmware in an emulator that uses the real ESP32 boot ROM, in both boot modes.

    @qemu @STK-14 @VER-STK-11
    Scenario: STK-13-S01: Tester verifies without hardware
      When the tester runs "make qemu" and enters "s" and "f 0" to "f 5"
      Then the self test reports "all ok"
      And every fault is reported and followed by a reboot
