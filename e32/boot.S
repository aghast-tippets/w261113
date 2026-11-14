/*
 * boot.S -- the first code that runs after the ESP32 ROM loader.
 *
 * The ROM has already copied our IRAM and DRAM segments into place,
 * either from flash at 0x1000 or over the UART ("load_ram"), so there
 * is no .data to copy.  We need a clean register window, our own stack,
 * a zeroed BSS and the watchdogs turned off; then we can run C.
 *
 * We also take over the exception vectors (vectors.S) from the ROM,
 * before the first call: from then on window spills, interrupts and
 * faults are all handled by our code.
 */
#include "xtensa.h"

	.section .text.boot, "ax"
	.literal_position
	.align	4
	.global	call_start
	.type	call_start, @function
call_start:
	/* We use no interrupts: disable whatever the ROM enabled */
	movi	a2, 0
	wsr	a2, INTENABLE

	/*
	 * Forget the ROM call frames: only window 0 is live after this,
	 * so the ROM stack is never touched again.  Once WINDOWBASE
	 * changes, a0..a15 name different physical registers, so
	 * everything is reloaded after the rsync.
	 */
	movi	a2, 1
	wsr	a2, WINDOWSTART
	movi	a2, 0
	wsr	a2, WINDOWBASE
	rsync

	/* From now on exceptions and window spills use our vectors.S */
	movi	a2, _vector_table
	wsr	a2, VECBASE
	rsync

	movi	a0, 0			/* ends backtraces in gdb */
	movi	a1, _stack_top
	/* INTLEVEL 0: each interrupt is still off in INTENABLE */
	movi	a2, PS_WOE | PS_UM | PS_INTLEVEL(0)
	wsr	a2, PS
	rsync

	/* Clear BSS (the ROM only loads what is in the image) */
	movi	a2, __bss_start
	movi	a3, __bss_end
	movi	a4, 0
1:	bgeu	a2, a3, 2f
	s32i	a4, a2, 0
	addi	a2, a2, 4
	j	1b
2:
	call4	wdt_disable
	call4	serial_setup
	call4	main
3:	j	3b

	.size	call_start, . - call_start
