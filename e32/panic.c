/*
 * panic.c -- report a fatal exception and offer a reboot.
 *
 * _panic in vectors.S saved every register into panic_frame and called
 * us on a private stack with interrupts masked, so only polled I/O.
 */
#include <stddef.h>
#include "types.h"
#include "regs.h"
#include "io.h"
#include "irq.h"

/* Keep vectors.S and struct panic_frame in step */
_Static_assert(offsetof(struct panic_frame, exccause) == PF_EXCCAUSE, "pf");
_Static_assert(offsetof(struct panic_frame, epc) == PF_EPC(1), "pf");
_Static_assert(offsetof(struct panic_frame, eps) == PF_EPS(2), "pf");
_Static_assert(sizeof(struct panic_frame) == PF_SIZE, "pf");
_Static_assert(offsetof(struct irq_frame, lcount) == IF_LCOUNT, "if");
_Static_assert(sizeof(struct irq_frame) == IF_SIZE, "if");

static const char *const cause_name[40] = {
	[0]  = "IllegalInstruction",
	[1]  = "Syscall",
	[2]  = "InstructionFetchError",
	[3]  = "LoadStoreError",
	[5]  = "Alloca",
	[6]  = "IntegerDivideByZero",
	[8]  = "Privileged",
	[9]  = "LoadStoreAlignment",
	[12] = "InstrPIFDataError",
	[13] = "LoadStorePIFDataError",
	[14] = "InstrPIFAddrError",
	[15] = "LoadStorePIFAddrError",
	[16] = "InstTLBMiss",
	[17] = "InstTLBMultiHit",
	[18] = "InstFetchPrivilege",
	[20] = "InstFetchProhibited",
	[24] = "LoadStoreTLBMiss",
	[25] = "LoadStoreTLBMultiHit",
	[26] = "LoadStorePrivilege",
	[28] = "LoadProhibited",
	[29] = "StoreProhibited",
	[32] = "Coprocessor0Disabled (FPU)",
};

static int panic_getc(void)
{
	while (UART_RXCNT(readl(UART0_BASE + UART_STATUS)) == 0)
		;
	return readl(UART0_BASE + UART_FIFO) & 0xff;
}

void reboot(void)
{
	writel(RTC_SW_SYS_RST, RTCCNTL_BASE + RTC_OPTIONS0);
	while (1)
		;
}

void panic_handler(struct panic_frame *f)
{
	static int nested;
	const char *name;
	u32 pc, ps, i;
	int level = 0;

	if (nested++)		/* a fault while reporting a fault */
		while (1)
			;

	switch (f->kind) {
	case KIND_USER:
	case KIND_KERNEL:
		pc = f->epc[0];
		ps = f->ps;
		name = f->exccause < 40 ? cause_name[f->exccause] : 0;
		printf("\n*** %s exception %u: %s\n",
		       f->kind == KIND_USER ? "Fatal" : "Kernel",
		       f->exccause, name ? name : "?");
		break;
	case KIND_DOUBLE:
		pc = f->depc;
		ps = f->ps;
		printf("\n*** Double exception (cause %u while handling "
		       "an exception at %08x)\n", f->exccause, f->epc[0]);
		break;
	default:
		level = f->kind - KIND_LEVEL(0);
		pc = f->epc[level - 1];
		ps = f->eps[level - 2];
		printf("\n*** %s\n", level == 6 ? "Debug exception (break?)" :
		       level == 7 ? "NMI" : "Unexpected high-level interrupt");
		printf("    level %i, pending %08x\n", level, RSR(interrupt));
		break;
	}

	printf("pc  %08x  ps  %08x", pc, ps);
	if (f->exccause >= 2 && f->exccause != 4 && f->exccause != 5
	    && f->exccause != 6 && !level)
		printf("  excvaddr %08x", f->excvaddr);
	printf("\n");
	for (i = 0; i < 16; i++)
		printf("%sa%-2u %08x%s", i % 4 ? "  " : "", i, f->a[i],
		       i % 4 == 3 ? "\n" : "");
	printf("sar %08x  lbeg %08x  lend %08x  lcount %08x\n",
	       f->sar, f->lbeg, f->lend, f->lcount);
	printf("windowbase %u  windowstart %04x\n",
	       f->windowbase, f->windowstart);
	/* a0 is the return address: top 2 bits hold the call size */
	printf("called from ~%08x\n", (f->a[0] & 0x3fffffff) | 0x40000000);

	puts("\nPress any key to reboot\n");
	panic_getc();
	reboot();
}
