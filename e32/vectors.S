/*
 * vectors.S -- our own exception vectors, replacing the ROM's.
 *
 * VECBASE points at _vector_table (start of IRAM, 1kB aligned).  The
 * offsets are fixed by the ESP32 core configuration:
 *
 *   0x000..0x17f  window overflow/underflow for call4, call8, call12
 *   0x180..0x2bf  level 2..5 interrupts, debug (6), NMI (7): fatal
 *   0x300         kernel exception: fatal (we always run with PS.UM=1)
 *   0x340         user exception: level-1 interrupts, alloca, faults
 *   0x3c0         double exception: fatal
 *
 * Vector slots are tiny and can't use literals, so each one saves a0 in
 * EXCSAVE_1 and jumps to the real handler in .text.
 */
#include "xtensa.h"

	.section .vectors, "ax"
	.align	4
	.global	_vector_table
_vector_table:

/*
 * Window spill and fill.  The register file is a ring of 64 registers;
 * when a call needs registers still held by an older frame, the CPU
 * jumps here to store that frame below its callee's stack pointer
 * (overflow), and the reverse on return (underflow).  These sequences
 * follow the Xtensa ISA: a0..a3 go in the 16 bytes below the callee's
 * sp, the extra registers of call8/call12 frames at the bottom of the
 * frame's caller (whose sp is found at [sp - 12]).
 */
	.org	0x000
	.global	_WindowOverflow4
_WindowOverflow4:
	s32e	a0, a5, -16
	s32e	a1, a5, -12
	s32e	a2, a5, -8
	s32e	a3, a5, -4
	rfwo

	.org	0x040
	.global	_WindowUnderflow4
_WindowUnderflow4:
	l32e	a0, a5, -16
	l32e	a1, a5, -12
	l32e	a2, a5, -8
	l32e	a3, a5, -4
	rfwu

	.org	0x080
	.global	_WindowOverflow8
_WindowOverflow8:
	s32e	a0, a9, -16
	l32e	a0, a1, -12		/* a0 = caller's sp */
	s32e	a1, a9, -12
	s32e	a2, a9, -8
	s32e	a3, a9, -4
	s32e	a4, a0, -32
	s32e	a5, a0, -28
	s32e	a6, a0, -24
	s32e	a7, a0, -20
	rfwo

	.org	0x0c0
	.global	_WindowUnderflow8
_WindowUnderflow8:
	l32e	a1, a9, -12
	l32e	a0, a9, -16
	l32e	a7, a1, -12		/* a7 = caller's sp, for now */
	l32e	a2, a9, -8
	l32e	a4, a7, -32
	l32e	a3, a9, -4
	l32e	a5, a7, -28
	l32e	a6, a7, -24
	l32e	a7, a7, -20
	rfwu

	.org	0x100
	.global	_WindowOverflow12
_WindowOverflow12:
	s32e	a0, a13, -16
	l32e	a0, a1, -12		/* a0 = caller's sp */
	s32e	a1, a13, -12
	s32e	a2, a13, -8
	s32e	a3, a13, -4
	s32e	a4, a0, -48
	s32e	a5, a0, -44
	s32e	a6, a0, -40
	s32e	a7, a0, -36
	s32e	a8, a0, -32
	s32e	a9, a0, -28
	s32e	a10, a0, -24
	s32e	a11, a0, -20
	rfwo

	.org	0x140
	.global	_WindowUnderflow12
_WindowUnderflow12:
	l32e	a1, a13, -12
	l32e	a0, a13, -16
	l32e	a11, a1, -12		/* a11 = caller's sp, for now */
	l32e	a2, a13, -8
	l32e	a4, a11, -48
	l32e	a8, a11, -32
	l32e	a3, a13, -4
	l32e	a5, a11, -44
	l32e	a6, a11, -40
	l32e	a7, a11, -36
	l32e	a9, a11, -28
	l32e	a10, a11, -24
	l32e	a11, a11, -20
	rfwu

/* Interrupt levels we never enable: if one fires, it's a bug */
	.macro	fatal_vector kind
	wsr	a0, EXCSAVE1
	movi	a0, \kind
	j	_panic
	.endm

	.org	0x180
	fatal_vector KIND_LEVEL(2)
	.org	0x1c0
	fatal_vector KIND_LEVEL(3)
	.org	0x200
	fatal_vector KIND_LEVEL(4)
	.org	0x240
	fatal_vector KIND_LEVEL(5)
	.org	0x280
	fatal_vector KIND_LEVEL(6)	/* debug: break instruction etc. */
	.org	0x2c0
	fatal_vector KIND_LEVEL(7)	/* NMI */
	.org	0x300
	fatal_vector KIND_KERNEL

	.org	0x340
_UserExceptionVector:
	wsr	a0, EXCSAVE1
	rsr	a0, EXCCAUSE
	beqi	a0, EXCCAUSE_LEVEL1_INT, 1f
	beqi	a0, EXCCAUSE_ALLOCA, 2f
	movi	a0, KIND_USER
	j	_panic
1:	j	_level1_handler
2:	j	_alloca_handler

	.org	0x3c0
	fatal_vector KIND_DOUBLE


	.text
	.literal_position

/*
 * Alloca (MOVSP) exception: a function adjusted its stack pointer
 * (alloca or a variable-length array) while its caller's registers were
 * spilled to memory.  Bring the caller back with the matching underflow
 * handler; its "rfwu" then returns to PS.OWB's window and retries the
 * movsp.  The call size is in the top two bits of the function's a0.
 */
	.align	4
_alloca_handler:
	rsr	a0, WINDOWBASE		/* the faulting function's window */
	rotw	-1			/* that value is now in a4 */
	rsr	a2, PS
	extui	a3, a2, PS_OWB_SHIFT, 4
	xor	a3, a3, a4
	rsr	a4, EXCSAVE1		/* the function's own a0, back in place */
	slli	a3, a3, PS_OWB_SHIFT
	xor	a2, a2, a3		/* PS.OWB = faulting window */
	wsr	a2, PS
	rsync

	bbsi.l	a4, 31, 1f		/* 01: called with call4 */
	j	_WindowUnderflow4
1:	rotw	-1			/* a0 is now a8 */
	bbsi.l	a8, 30, 2f		/* 10: called with call8 */
	j	_WindowUnderflow8
2:	rotw	-1			/* 11: call12 */
	j	_WindowUnderflow12

/*
 * Level-1 interrupt: save the interrupted context, call irq_dispatch()
 * in C, restore and return.
 *
 * Before moving the stack pointer we spill every other register window
 * to memory.  Otherwise an older frame could be spilled later, while we
 * are on our own frame, and the CPU would store it relative to the
 * wrong stack pointer.  With only the current window live, the C call
 * below is an ordinary windowed call.
 */
	.align	4
_level1_handler:
	addi	a0, a1, -(16 + IF_SIZE)	/* frame base */
	s32i	a1, a0, IF_A(1)
	s32i	a2, a0, IF_A(2)
	rsr	a2, EXCSAVE1
	s32i	a2, a0, IF_A(0)
	s32i	a3, a0, IF_A(3)
	s32i	a4, a0, IF_A(4)
	s32i	a5, a0, IF_A(5)
	s32i	a6, a0, IF_A(6)
	s32i	a7, a0, IF_A(7)
	s32i	a8, a0, IF_A(8)
	s32i	a9, a0, IF_A(9)
	s32i	a10, a0, IF_A(10)
	s32i	a11, a0, IF_A(11)
	s32i	a12, a0, IF_A(12)
	s32i	a13, a0, IF_A(13)
	s32i	a14, a0, IF_A(14)
	s32i	a15, a0, IF_A(15)
	rsr	a2, EPC1
	s32i	a2, a0, IF_PC
	rsr	a2, PS
	s32i	a2, a0, IF_PS
	rsr	a2, SAR
	s32i	a2, a0, IF_SAR
	rsr	a2, LBEG
	s32i	a2, a0, IF_LBEG
	rsr	a2, LEND
	s32i	a2, a0, IF_LEND
	rsr	a2, LCOUNT
	s32i	a2, a0, IF_LCOUNT
	movi	a2, 0
	wsr	a2, LCOUNT		/* no zero-overhead loop in progress */

	/* Leave exception mode, keeping level-1 interrupts masked */
	movi	a2, PS_WOE | PS_UM | PS_INTLEVEL(1)
	wsr	a2, PS
	rsync

	/*
	 * Spill all other windows: touching a12 in each group of three
	 * windows makes the CPU overflow any older frame living there.
	 * 3+3+3+3+4 = 16 rotations of 4 registers brings us back home.
	 */
	and	a12, a12, a12
	rotw	3
	and	a12, a12, a12
	rotw	3
	and	a12, a12, a12
	rotw	3
	and	a12, a12, a12
	rotw	3
	and	a12, a12, a12
	rotw	4

	mov	a1, a0			/* now it's safe to move sp */
	mov	a6, a1			/* argument: the frame */
	call4	irq_dispatch

	/* Back to exception mode (masks interrupts), then restore */
	l32i	a2, a1, IF_PS
	wsr	a2, PS
	rsync
	l32i	a2, a1, IF_PC
	wsr	a2, EPC1
	l32i	a2, a1, IF_SAR
	wsr	a2, SAR
	l32i	a2, a1, IF_LBEG
	wsr	a2, LBEG
	l32i	a2, a1, IF_LEND
	wsr	a2, LEND
	l32i	a2, a1, IF_LCOUNT
	wsr	a2, LCOUNT
	l32i	a0, a1, IF_A(0)
	l32i	a2, a1, IF_A(2)
	l32i	a3, a1, IF_A(3)
	l32i	a4, a1, IF_A(4)
	l32i	a5, a1, IF_A(5)
	l32i	a6, a1, IF_A(6)
	l32i	a7, a1, IF_A(7)
	l32i	a8, a1, IF_A(8)
	l32i	a9, a1, IF_A(9)
	l32i	a10, a1, IF_A(10)
	l32i	a11, a1, IF_A(11)
	l32i	a12, a1, IF_A(12)
	l32i	a13, a1, IF_A(13)
	l32i	a14, a1, IF_A(14)
	l32i	a15, a1, IF_A(15)
	l32i	a1, a1, IF_A(1)
	rsync
	rfe

/*
 * Fatal path.  a0 = KIND_*, the original a0 is in EXCSAVE_1.  Save
 * everything in a static frame (the stack may be the problem), then
 * rebuild a minimal C environment on a private stack and call
 * panic_handler(), which never returns.
 */
	.align	4
	.global	_panic
_panic:
	wsr	a0, MISC0		/* kind */
	rsr	a0, PS
	wsr	a0, MISC1		/* PS when we got here */
	movi	a0, PS_EXCM | PS_UM | PS_WOE | PS_INTLEVEL(15)
	wsr	a0, PS			/* no window exceptions, no irqs */
	rsync

	movi	a0, panic_frame
	s32i	a1, a0, PF_A(1)
	s32i	a2, a0, PF_A(2)
	s32i	a3, a0, PF_A(3)
	s32i	a4, a0, PF_A(4)
	s32i	a5, a0, PF_A(5)
	s32i	a6, a0, PF_A(6)
	s32i	a7, a0, PF_A(7)
	s32i	a8, a0, PF_A(8)
	s32i	a9, a0, PF_A(9)
	s32i	a10, a0, PF_A(10)
	s32i	a11, a0, PF_A(11)
	s32i	a12, a0, PF_A(12)
	s32i	a13, a0, PF_A(13)
	s32i	a14, a0, PF_A(14)
	s32i	a15, a0, PF_A(15)
	rsr	a2, EXCSAVE1
	s32i	a2, a0, PF_A(0)
	rsr	a2, MISC0
	s32i	a2, a0, PF_KIND
	rsr	a2, MISC1
	s32i	a2, a0, PF_PS
	rsr	a2, EXCCAUSE
	s32i	a2, a0, PF_EXCCAUSE
	rsr	a2, EXCVADDR
	s32i	a2, a0, PF_EXCVADDR
	rsr	a2, SAR
	s32i	a2, a0, PF_SAR
	rsr	a2, DEPC
	s32i	a2, a0, PF_DEPC
	rsr	a2, LBEG
	s32i	a2, a0, PF_LBEG
	rsr	a2, LEND
	s32i	a2, a0, PF_LEND
	rsr	a2, LCOUNT
	s32i	a2, a0, PF_LCOUNT
	rsr	a2, WINDOWBASE
	s32i	a2, a0, PF_WINDOWBASE
	rsr	a2, WINDOWSTART
	s32i	a2, a0, PF_WINDOWSTART
	rsr	a2, EPC1
	s32i	a2, a0, PF_EPC(1)
	rsr	a2, EPC2
	s32i	a2, a0, PF_EPC(2)
	rsr	a2, EPC3
	s32i	a2, a0, PF_EPC(3)
	rsr	a2, EPC4
	s32i	a2, a0, PF_EPC(4)
	rsr	a2, EPC5
	s32i	a2, a0, PF_EPC(5)
	rsr	a2, EPC6
	s32i	a2, a0, PF_EPC(6)
	rsr	a2, EPC7
	s32i	a2, a0, PF_EPC(7)
	rsr	a2, EPS2
	s32i	a2, a0, PF_EPS(2)
	rsr	a2, EPS3
	s32i	a2, a0, PF_EPS(3)
	rsr	a2, EPS4
	s32i	a2, a0, PF_EPS(4)
	rsr	a2, EPS5
	s32i	a2, a0, PF_EPS(5)
	rsr	a2, EPS6
	s32i	a2, a0, PF_EPS(6)
	rsr	a2, EPS7
	s32i	a2, a0, PF_EPS(7)

	/* Same reset of the register window as in boot.S */
	movi	a2, 0
	wsr	a2, LCOUNT
	movi	a2, 1
	wsr	a2, WINDOWSTART
	movi	a2, 0
	wsr	a2, WINDOWBASE
	rsync
	movi	a0, 0
	movi	a1, _panic_stack_top
	movi	a2, PS_UM | PS_WOE | PS_INTLEVEL(15)
	wsr	a2, PS
	rsync
	movi	a6, panic_frame
	call4	panic_handler
3:	j	3b

	.section .bss
	.align	16
	.global	panic_frame
panic_frame:
	.space	PF_SIZE
	.align	16
	.space	2048
_panic_stack_top:
