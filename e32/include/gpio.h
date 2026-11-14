/*
 * gpio.h -- the same API as the LPC1343 code, on the ESP32.
 *
 * GPIO numbers are just numbers.  The ESP32 already counts its pins
 * 0..39, with the output/enable/input registers split in two "ports"
 * (0..31 and 32..39), so the macros below are a formality.
 *
 * Alternate function 0 is always GPIO, whatever the hardware says:
 * on the ESP32 the IO_MUX has GPIO at function 2, so 0 and 2 are swapped.
 */
#ifndef __GPIO_H__
#define __GPIO_H__
#include "types.h"

#define GPIO_NR(port, bit)	(((port) * 32) + (bit))
#define GPIO_PORT(nr)		((nr) / 32)
#define GPIO_BIT(nr)		((nr) % 32)

#define GPIO_MAX		40

extern void gpio_init(void);
extern int gpio_dir_af(int gpio, int output, int value, int afnum);
extern int gpio_dir(int gpio, int output, int value);

extern u32 __gpio_get(int gpio);
extern void __gpio_set(int gpio, u32 value);

static inline int gpio_get(int gpio)
{
	return __gpio_get(gpio) != 0;
}

static inline void gpio_set(int gpio, int value)
{
	__gpio_set(gpio, value);
}

#endif /* __GPIO_H__ */
