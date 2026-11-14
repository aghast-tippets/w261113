#ifndef __IO_H__
#define __IO_H__
#include "types.h"

/* io.c */
extern void serial_setup(void);
extern void putc(int c);
extern void puts(const char *s);	/* no trailing newline is added */
extern int getc(void);
extern int gets(char *s, int size);	/* echoes, returns length */

/* wdt.c */
extern void wdt_disable(void);

/* lib.c */
extern void *memset(void *s, int c, unsigned int n);
extern void *memcpy(void *d, const void *s, unsigned int n);
extern unsigned int strlen(const char *s);
extern void udelay(u32 usecs);

/* pp_printf.c -- "printf" is an alias provided by the linker script */
extern int pp_printf(const char *fmt, ...)
	__attribute__((format(printf, 1, 2)));
extern int pp_sprintf(char *buf, const char *fmt, ...)
	__attribute__((format(printf, 2, 3)));
extern int printf(const char *fmt, ...)
	__attribute__((format(printf, 1, 2)));

/* mimmo.c */
extern void mimmo(void);

/*
 * Clock assumption: the ROM leaves the CPU running from the 40MHz crystal.
 * Only udelay() depends on this; the UART divisor is left as the ROM set it.
 */
#ifndef CPU_HZ
#define CPU_HZ 40000000
#endif

#endif /* __IO_H__ */
