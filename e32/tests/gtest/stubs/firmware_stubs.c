/*
 * firmware_stubs.c -- the firmware's public functions with no behaviour.
 *
 * Built only with -DE32_RED=ON, to show (Phase 3 of docs/bdd-framework.md)
 * that every GoogleTest test fails for want of an implementation rather
 * than for a build or harness error.  Never linked into the firmware.
 */
#include "types.h"
#include "xtensa.h"
#include "irq.h"
#include "gpio.h"
#include "io.h"

volatile u32 jiffies;

void *memset(void *s, int c, unsigned int n) { return s; }
void *memcpy(void *d, const void *s, unsigned int n) { return d; }
unsigned int strlen(const char *s) { return 0; }
void udelay(u32 usecs) { }

int pp_printf(const char *fmt, ...) { return 0; }
int pp_sprintf(char *buf, const char *fmt, ...) { buf[0] = 0; return 0; }

void gpio_init(void) { }
int gpio_dir_af(int gpio, int output, int value, int afnum) { return 0; }
int gpio_dir(int gpio, int output, int value) { return 0; }
u32 __gpio_get(int gpio) { return 0; }
void __gpio_set(int gpio, u32 value) { }

void wdt_disable(void) { }

void irq_init(void) { }
int irq_request(int irq, irq_handler_t fn, void *arg) { return 0; }
void irq_enable(int irq) { }
void irq_disable(int irq) { }
void irq_map(int source, int irq) { }
u32 irq_count(int irq) { return 0; }
void irq_dispatch(struct irq_frame *f) { }

void timer_init(int hz) { }

void serial_setup(void) { }
void putc(int c) { }
void puts(const char *s) { }
int getc(void) { return 0; }
int gets(char *s, int size) { s[0] = 0; return 0; }
void serial_irq_init(int irq) { }

void mimmo(void) { }
void panic_handler(struct panic_frame *f) { }
void reboot(void) { }
int main(void) { return 0; }
