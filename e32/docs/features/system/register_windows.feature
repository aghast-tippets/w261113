@EP-06 @FEAT-050
Feature: FEAT-050: Register windows and alloca
  Epic: EP-06 Exception and interrupt handling   ·   Level: system

  User stories delivered:
    US-18  As a developer, I want deep recursion and variable-length arrays to
           work as in hosted C, so that I don't have to know about register
           windows.

  Actors: Firmware developer (ACT-H1, persona "dana")

  @SYS-15
  Rule: SYS-15: Deep calls and variable-length arrays
    EARS: The e32 firmware shall support nested C calls at least 200 frames deep, and variable-length arrays or `alloca` at any call depth, limited only by stack space.
