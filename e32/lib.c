/*
 * lib.c -- the few library functions we need (gcc may call memset and
 * memcpy on its own, even with -ffreestanding)
 */
#include "types.h"
#include "io.h"

void *memset(void *s, int c, unsigned int n)
{
	u8 *p = s;

	while (n--)
		*p++ = c;
	return s;
}

void *memcpy(void *d, const void *s, unsigned int n)
{
	u8 *dp = d;
	const u8 *sp = s;

	while (n--)
		*dp++ = *sp++;
	return d;
}

unsigned int strlen(const char *s)
{
	const char *p = s;

	while (*p)
		p++;
	return p - s;
}

/* Busy wait on the cycle counter; wraps correctly thanks to u32 math */
void udelay(u32 usecs)
{
	u32 start = get_ccount();
	u32 ticks = usecs * (CPU_HZ / 1000000);

	while (get_ccount() - start < ticks)
		;
}
