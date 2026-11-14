// firmware.h -- the firmware API as seen from C++ tests.
//
// The firmware sources are compiled for the host with the libc-clashing
// names renamed (putc -> e32_putc, printf -> pp_printf, main -> e32_main,
// ...; see CMakeLists.txt), so the test binary keeps the real libc.
#ifndef E32_TESTS_FIRMWARE_H
#define E32_TESTS_FIRMWARE_H

extern "C" {
#include "xtensa.h"  // u32, frames, KIND_*, irq_save()...
#include "gpio.h"
#include "irq.h"

// io.c
void serial_setup(void);
void e32_putc(int c);
void e32_puts(const char* s);
int e32_getc(void);
int e32_gets(char* s, int size);
// wdt.c
void wdt_disable(void);
// lib.c
void* e32_memset(void* s, int c, unsigned int n);
void* e32_memcpy(void* d, const void* s, unsigned int n);
unsigned int e32_strlen(const char* s);
void udelay(u32 usecs);
// pp_printf.c
int pp_printf(const char* fmt, ...);
int pp_sprintf(char* buf, const char* fmt, ...);
// mimmo.c, main.c
void mimmo(void);
int e32_main(void);
}

#endif  // E32_TESTS_FIRMWARE_H
