@EP-01 @FEAT-013
Feature: FEAT-013: Stakeholder acceptance: Build from source without an SDK
  Epic: EP-01 Build from source without an SDK   ·   Level: acceptance

  User stories delivered:
    US-01  As a developer, I want to build the firmware with a single `make`
           using only a bare cross-compiler, so that I depend on no vendor SDK or
           C library.
    US-02  As a developer, I want a warning-free build that reports the section
           sizes, so that I notice regressions immediately.
    US-04  As a maintainer, I want a script that builds the cross-compiler from
           pinned sources, so that anyone can reproduce the exact toolchain.

  Actors: Firmware developer (ACT-H1, persona "dana"), Maintainer (ACT-H4,
    persona "max")

  @STK-01 @US-01 @US-02
  Rule: STK-01: Build with a bare toolchain
    EARS: The developer needs to build the firmware from source with only a bare cross-compiler, GNU make and a host C compiler.

    @host @STK-18 @VER-STK-01
    Scenario: STK-01-S01: Developer builds with nothing but a bare toolchain
      Given a host with xtensa-esp32-elf-gcc, make and cc only
      When the developer runs "make clean all"
      Then e32.elf and e32.bin are produced without warnings
      And the inspection shows no SDK, no libc and no ROM routine in use

  @STK-02 @US-04
  Rule: STK-02: Reproduce the toolchain
    EARS: The maintainer needs to rebuild the cross-compiler from pinned sources when a prebuilt one is unavailable or untrusted.

    @host @pending @VER-STK-02
    Scenario: STK-02-S01: Maintainer reproduces the toolchain
      When the maintainer runs "tools/build-toolchain.sh" in an empty directory
      Then the resulting compiler builds e32 without warnings
