@EP-01 @FEAT-010
Feature: FEAT-010: Toolchain from source
  Epic: EP-01 Build from source without an SDK   ·   Level: system

  User stories delivered:
    US-04  As a maintainer, I want a script that builds the cross-compiler from
           pinned sources, so that anyone can reproduce the exact toolchain.

  Actors: Maintainer (ACT-H4, persona "max")

  @SYS-25
  Rule: SYS-25: Toolchain from source
    EARS: When `tools/build-toolchain.sh` is run on a Linux host with the build prerequisites and access to the pinned source repositories, it shall build and install a C-only xtensa-esp32-elf toolchain with libgcc under `PREFIX`.
