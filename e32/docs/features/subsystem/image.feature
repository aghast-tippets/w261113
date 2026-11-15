@EP-01 @FEAT-006
Feature: FEAT-006: Boot image generation
  Epic: EP-01 Build from source without an SDK   ·   Level: subsystem

  Supports: US-01 via STK-01 → SYS-03 → SUB-BLD-04
  Supports: US-02 via STK-01 → SYS-03 → SUB-BLD-04
  Supports: US-03 via STK-03 → SYS-03 → SUB-BLD-04
  Supports: US-05 via STK-03 → SYS-03 → SUB-BLD-04
  Supports: US-06 via STK-04 → SYS-03 → SUB-BLD-04

  @SUB-BLD-04
  Rule: SUB-BLD-04: Image conversion
    EARS: When `e32.elf` has been linked, the build subsystem shall convert it into an ESP32 boot image (IF-01), with one image segment per loadable ELF segment that has file contents.
