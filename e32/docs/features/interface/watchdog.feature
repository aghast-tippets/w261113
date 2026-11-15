@EP-02 @FEAT-023
Feature: FEAT-023: Watchdog control
  Epic: EP-02 Boot and run on the ESP32   ·   Level: interface

  Supports: US-07 via SYS-09 → SUB-BOOT-02 → IF-14

  @IF-14
  Rule: IF-14: Watchdog write-protect protocol
    EARS: When software changes a watchdog's configuration, it shall first write `0x50D83AA1` to that watchdog's `WPROTECT` register, then write the configuration, then write any other value (0) to `WPROTECT` to lock it again.
