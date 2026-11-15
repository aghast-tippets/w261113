@EP-05 @FEAT-043
Feature: FEAT-043: GPIO control
  Epic: EP-05 GPIO control   ·   Level: interface

  Supports: US-15 via SUB-GPIO-01 → IF-10
  Supports: US-16 via STK-07 → SYS-12 → IF-10

  @IF-10
  Rule: IF-10: GPIO API
    EARS: `include/gpio.h` shall offer:
      - `GPIO_NR`, `GPIO_PORT` and `GPIO_BIT`;
      - `gpio_init`;
      - `gpio_dir_af(gpio, output, value, afnum)` and `gpio_dir(gpio, output, value)`, which return 0 or −1;
      - `gpio_get` and `gpio_set` (0 or 1);
      - `__gpio_get` and `__gpio_set` (raw bit).
      This matches the LPC1343 package's API, with AF0 meaning GPIO.
