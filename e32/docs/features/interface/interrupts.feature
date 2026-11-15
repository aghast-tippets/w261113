@EP-06 @FEAT-058
Feature: FEAT-058: Interrupts
  Epic: EP-06 Exception and interrupt handling   ·   Level: interface

  Supports: US-10 via STK-19 → SYS-18 → SUB-EXC-04 → IF-09
  Supports: US-19 via STK-08 → SYS-16 → IF-09
  Supports: US-20 via STK-09 → SYS-17 → IF-09
  Supports: US-21 via STK-08 → SYS-16 → IF-09
  Supports: US-29 via STK-08 → SYS-16 → IF-09

  @IF-09
  Rule: IF-09: Interrupt API
    EARS: `include/irq.h` shall offer:
      - `irq_init(void)`;
      - `irq_map(int source, int irq)`;
      - `irq_request(int irq, irq_handler_t fn, void *arg)`, which returns 0 or −1;
      - `irq_enable(int)` and `irq_disable(int)`;
      - `irq_count(int)`;
      - `irq_save()` and `irq_restore(u32)`;
      - `timer_init(int hz)`, `jiffies` and `HZ`;
      - `serial_irq_init(int irq)`;
      - `reboot(void)`.
      Handlers have the signature `void fn(int irq, void *arg)`, run with level-1 interrupts masked, and must not use floating point.

  @IF-12
  Rule: IF-12: Interrupt matrix registers
    EARS: The firmware shall route peripheral source `s` (0–68) to the PRO CPU by writing a CPU line number (0–31) to `0x3FF00104 + 4·s`. UART0 is source 34. Writing an internal line (6, 7, 11, 15, 16 or 29) disconnects the source.
