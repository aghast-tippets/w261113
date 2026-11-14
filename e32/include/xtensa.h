/*
 * xtensa.h -- CPU-level definitions shared by assembly and C:
 * PS bits, exception causes and the layout of the two saved frames.
 */
#ifndef __XTENSA_H__
#define __XTENSA_H__

/* Processor State register */
#define PS_INTLEVEL(n)		((n) & 0xf)
#define PS_EXCM			0x00000010
#define PS_UM			0x00000020
#define PS_OWB_SHIFT		8
#define PS_WOE			0x00040000

/* EXCCAUSE values handled in the user exception vector */
#define EXCCAUSE_LEVEL1_INT	4
#define EXCCAUSE_ALLOCA		5

/*
 * The ESP32 core: which CPU interrupts are level 1 (all we dispatch),
 * which of those are latched (edge/software) and must be cleared with
 * INTCLEAR, and the internal timer interrupt.
 */
#define LEVEL1_INT_MASK		0x000637ff
#define LEVEL1_LATCHED_MASK	0x00000480	/* 7: software, 10: edge */
#define INT_TIMER0		6		/* CCOMPARE0 */
#define INT_SOFTWARE		7

/* Why _panic was entered: which vector */
#define KIND_USER		1	/* user exception, not an interrupt */
#define KIND_KERNEL		2
#define KIND_DOUBLE		3
#define KIND_LEVEL(n)		(0x10+(n))	/* level 2..5, 6 = debug, 7 = NMI */
					/* (no spaces: it's a gas macro arg) */

/*
 * Level-1 interrupt frame, built on the interrupted stack, 16 bytes
 * below its stack pointer (those 16 bytes may hold its caller's spilled
 * a0..a3, so we leave them alone).
 */
#define IF_A(n)			((n) * 4)
#define IF_PC			0x40
#define IF_PS			0x44
#define IF_SAR			0x48
#define IF_LBEG			0x4c
#define IF_LEND			0x50
#define IF_LCOUNT		0x54
#define IF_SIZE			0x60	/* multiple of 16 */

/* Panic frame: a static area, since the stack may be what broke */
#define PF_KIND			0x00
#define PF_A(n)			(0x04 + (n) * 4)
#define PF_EXCCAUSE		0x44
#define PF_EXCVADDR		0x48
#define PF_PS			0x4c
#define PF_SAR			0x50
#define PF_DEPC			0x54
#define PF_LBEG			0x58
#define PF_LEND			0x5c
#define PF_LCOUNT		0x60
#define PF_WINDOWBASE		0x64
#define PF_WINDOWSTART		0x68
#define PF_EPC(n)		(0x6c + ((n) - 1) * 4)	/* n = 1..7 */
#define PF_EPS(n)		(0x88 + ((n) - 2) * 4)	/* n = 2..7 */
#define PF_SIZE			0xa0

#ifndef __ASSEMBLER__
#include "types.h"

struct irq_frame {
	u32 a[16];
	u32 pc, ps, sar, lbeg, lend, lcount;
	u32 pad[2];
};

struct panic_frame {
	u32 kind;
	u32 a[16];
	u32 exccause, excvaddr, ps, sar, depc;
	u32 lbeg, lend, lcount, windowbase, windowstart;
	u32 epc[7];		/* epc[0] is EPC1 */
	u32 eps[6];		/* eps[0] is EPS2 */
};

/* Special register access: the register name must be a constant */
#define RSR(sr) ({ u32 __v; asm volatile ("rsr %0, " #sr : "=a" (__v)); __v; })
#define WSR(sr, v) asm volatile ("wsr %0, " #sr "; rsync" :: "a" (v) : "memory")

/* Mask level-1..3 interrupts, returning the old PS for irq_restore() */
static inline u32 irq_save(void)
{
	u32 ps;

	asm volatile ("rsil %0, 3" : "=a" (ps) :: "memory");
	return ps;
}

static inline void irq_restore(u32 ps)
{
	asm volatile ("wsr %0, ps; rsync" :: "a" (ps) : "memory");
}
#endif /* __ASSEMBLER__ */

#endif /* __XTENSA_H__ */
