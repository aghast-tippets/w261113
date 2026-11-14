/*
 * irq.h -- level-1 interrupts on the PRO CPU
 *
 * The Xtensa core has 32 interrupt lines with fixed priority levels.
 * Peripherals reach them through the interrupt matrix: irq_map() routes
 * a peripheral source (e.g. INTR_SRC_UART0) to one of the lines.
 * Lines 6 (timer 0) and 7 (software) are internal to the CPU.
 * Only level-1 lines are dispatched: 0-10, 12, 13, 17, 18.
 */
#ifndef __IRQ_H__
#define __IRQ_H__
#include "types.h"
#include "xtensa.h"

typedef void (*irq_handler_t)(int irq, void *arg);

extern void irq_init(void);
extern int irq_request(int irq, irq_handler_t fn, void *arg);
extern void irq_enable(int irq);
extern void irq_disable(int irq);
extern void irq_map(int source, int irq);
extern u32 irq_count(int irq);
extern void irq_dispatch(struct irq_frame *f);

/* timer.c: tick on CCOMPARE0, HZ times per second */
#define HZ 100
extern volatile u32 jiffies;
extern void timer_init(int hz);

/* io.c: interrupt-driven receive on UART0 */
extern void serial_irq_init(int irq);

/* panic.c */
extern void panic_handler(struct panic_frame *f);
extern void reboot(void);

#endif /* __IRQ_H__ */
