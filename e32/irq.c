/*
 * irq.c -- level-1 interrupt dispatch.  The assembly in vectors.S
 * saves the interrupted context and calls irq_dispatch() with level-1
 * interrupts masked; we run every pending, enabled handler.
 */
#include "types.h"
#include "regs.h"
#include "io.h"
#include "irq.h"

static struct irq_desc {
	irq_handler_t fn;
	void *arg;
	u32 count;
} irq_desc[32];

/* Interrupt lines 6, 7, 11, 15, 16, 29 are internal: matrix inputs are ignored */
#define INT_UNUSED	INT_TIMER0

void irq_init(void)
{
	int i;

	/* Disconnect whatever the ROM routed, so only our choices fire */
	for (i = 0; i < INTR_SOURCES; i++)
		writel(INT_UNUSED, DPORT_PRO_INTR_MAP(i));
	WSR(intenable, 0);
	WSR(intclear, 0xffffffff);
}

void irq_map(int source, int irq)
{
	writel(irq, DPORT_PRO_INTR_MAP(source));
}

void irq_enable(int irq)
{
	u32 flags = irq_save();

	WSR(intenable, RSR(intenable) | (1 << irq));
	irq_restore(flags);
}

void irq_disable(int irq)
{
	u32 flags = irq_save();

	WSR(intenable, RSR(intenable) & ~(1 << irq));
	irq_restore(flags);
}

int irq_request(int irq, irq_handler_t fn, void *arg)
{
	if (irq < 0 || irq > 31 || !(LEVEL1_INT_MASK & (1 << irq)))
		return -1;
	irq_desc[irq].fn = fn;
	irq_desc[irq].arg = arg;
	irq_enable(irq);
	return 0;
}

u32 irq_count(int irq)
{
	return irq_desc[irq & 31].count;
}

void irq_dispatch(struct irq_frame *f)
{
	struct irq_desc *d;
	u32 pending, bit;
	int irq;

	while ((pending = RSR(interrupt) & RSR(intenable) & LEVEL1_INT_MASK)) {
		irq = __builtin_ctz(pending);
		bit = 1 << irq;
		if (bit & LEVEL1_LATCHED_MASK)
			WSR(intclear, bit);
		d = irq_desc + irq;
		d->count++;
		if (d->fn) {
			d->fn(irq, d->arg);
		} else {
			WSR(intenable, RSR(intenable) & ~bit);
			printf("irq %i: no handler, disabled\n", irq);
		}
	}
}
