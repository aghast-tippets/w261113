/*
 * timer.c -- a periodic tick from the CPU's own CCOMPARE0 comparator.
 * It raises interrupt 6 when CCOUNT matches; writing CCOMPARE0 clears it.
 */
#include "types.h"
#include "io.h"
#include "irq.h"

volatile u32 jiffies;
static u32 tick_cycles;

/*
 * CCOMPARE matches on equality only: if we program a value CCOUNT has
 * already passed, the next match is 2^32 cycles away and the tick
 * stops.  So check *after* writing that the target is still ahead,
 * and skip whole periods (counting them, so uptime stays right) until
 * it is.  Writing CCOMPARE0 also clears the interrupt.
 */
static void timer_tick(int irq, void *arg)
{
	u32 next = RSR(ccompare0);

	do {
		next += tick_cycles;
		jiffies++;
		WSR(ccompare0, next);
	} while ((s32)(next - get_ccount()) <= 0);
}

void timer_init(int hz)
{
	tick_cycles = CPU_HZ / hz;
	WSR(ccompare0, get_ccount() + tick_cycles);
	irq_request(INT_TIMER0, timer_tick, 0);
}
