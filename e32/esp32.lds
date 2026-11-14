/*
 * esp32.lds -- everything lives in internal SRAM.
 *
 * Unlike the LPC1343 there is a single linker script: the ESP32 ROM
 * always copies the image into RAM before jumping to it, whether it
 * comes from flash or from the serial port.  So the same binary works
 * for "make ram" and "make flash".
 *
 * IRAM can only be accessed 32 bits at a time, so strings and other
 * read-only data go to DRAM together with .data.
 */
ENTRY(call_start)

MEMORY
{
	iram (rwx) : ORIGIN = 0x40080000, LENGTH = 128K
	dram (rw)  : ORIGIN = 0x3ffb0000, LENGTH = 176K /* to 0x3ffdc000 */
}

SECTIONS
{
	.text : {
		KEEP(*(.vectors))	/* VECBASE: must be 1kB aligned */
		KEEP(*(.text.boot))
		*(.literal .text .literal.* .text.*)
		. = ALIGN(4);
	} > iram

	.data : {
		*(.rodata .rodata.*)
		*(.data .data.*)
		. = ALIGN(4);
	} > dram

	.bss (NOLOAD) : {
		. = ALIGN(4);
		__bss_start = .;
		*(.bss .bss.* COMMON)
		. = ALIGN(4);
		__bss_end = .;
	} > dram

	/* The stack grows down from the top of our DRAM area */
	_stack_top = ORIGIN(dram) + LENGTH(dram);
	ASSERT(__bss_end + 8K <= _stack_top, "less than 8kB left for stack")
	ASSERT(_vector_table == ORIGIN(iram), "vectors must start IRAM")

	/* Like in the LPC code, the program calls printf, we offer pp_printf */
	PROVIDE(printf = pp_printf);
}
