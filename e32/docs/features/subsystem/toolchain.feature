@EP-01 @FEAT-011
Feature: FEAT-011: Toolchain from source
  Epic: EP-01 Build from source without an SDK   ·   Level: subsystem

  Supports: US-04 via STK-02 → SYS-25 → SUB-BLD-06

  @SUB-BLD-06
  Rule: SUB-BLD-06: Toolchain build
    EARS: When run, the toolchain script shall fetch pinned binutils and GCC sources, apply the ESP32 core-configuration overlay, and build and install binutils, a C-only GCC and libgcc for the target `xtensa-esp32-elf`.
