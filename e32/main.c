/*
 * main.c -- run the memory monitor, or blink a LED if you have no serial
 */
#include "types.h"
#include "io.h"
#include "gpio.h"
#include "irq.h"

#ifndef LED_GPIO
#define LED_GPIO 2	/* the blue LED on most cheap ESP32 boards */
#endif

extern char __bss_start[], __bss_end[], _stack_top[];

int main(void)
{
	int i;

	printf("\ne32: bare-metal ESP32, built " __DATE__ " " __TIME__ "\n");
	printf("bss %p-%p, stack top %p\n", __bss_start, __bss_end,
	       _stack_top);

	irq_init();
	timer_init(HZ);		/* 100 Hz tick on CPU interrupt 6 */
	serial_irq_init(17);		/* UART0 receive on CPU interrupt 17 */

	if (1)
		mimmo();	/* never returns */

	gpio_init();
	gpio_dir_af(LED_GPIO, 1, 0, 0);
	for (i = 0; ; i++) {
		gpio_set(LED_GPIO, i & 1);
		printf("led %i\n", i & 1);
		udelay(500 * 1000);
	}
}
