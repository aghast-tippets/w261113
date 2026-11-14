/*
 * types.h -- the few types and accessors everything else uses
 */
#ifndef __TYPES_H__
#define __TYPES_H__

typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef signed int s32;

/*
 * Linux-style accessors: value first, address second.  The Xtensa
 * compiler already puts a "memw" barrier around volatile accesses.
 */
static inline u32 readl(u32 addr)
{
	return *(volatile u32 *)addr;
}

static inline void writel(u32 val, u32 addr)
{
	*(volatile u32 *)addr = val;
}

/* The cycle counter: one tick per CPU clock */
static inline u32 get_ccount(void)
{
	u32 r;
	asm volatile ("rsr.ccount %0" : "=a" (r));
	return r;
}

#endif /* __TYPES_H__ */
