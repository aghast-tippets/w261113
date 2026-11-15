@EP-05 @FEAT-047
Feature: FEAT-047: Blink mode
  Epic: EP-05 GPIO control   ·   Level: software

  Supports: US-09 via STK-05 → SYS-06 → SUB-MON-03 → SW-MON-07
  Supports: US-10 via STK-19 → SYS-18 → SUB-MON-03 → SW-MON-07
  Supports: US-11 via STK-05 → SYS-06 → SUB-MON-03 → SW-MON-07
  Supports: US-17 via STK-16 → SYS-22 → SUB-MON-03 → SW-MON-07
  Supports: US-19 via STK-08 → SYS-16 → SUB-MON-03 → SW-MON-07
  Supports: US-20 via STK-09 → SYS-17 → SUB-MON-03 → SW-MON-07
  Supports: US-21 via STK-08 → SYS-16 → SUB-MON-03 → SW-MON-07
  Supports: US-29 via STK-08 → SYS-16 → SUB-MON-03 → SW-MON-07

  @SW-MON-07
  Rule: SW-MON-07: main
    EARS: When `main` runs, it shall:
      1. print the banner and the memory line;
      2. call `irq_init`, `timer_init(HZ)` and `serial_irq_init(17)`;
      3. run `mimmo`, or, in blink mode, configure `LED_GPIO` as an output and toggle it every 500 ms, printing `led N`.
