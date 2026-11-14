/*
 * regs.h -- the ESP32 registers we touch, from the Technical Reference
 * Manual.  Only what is used is listed: grep the TRM for the rest.
 */
#ifndef __REGS_H__
#define __REGS_H__

/* UART0 (the one wired to the USB-serial chip on every dev board) */
#define UART0_BASE		0x3ff40000
#define UART_FIFO		0x00
#define UART_CLKDIV		0x14
#define UART_STATUS		0x1c
#define UART_CONF0		0x20
#define UART_RXCNT(status)	((status) & 0xff)
#define UART_TXCNT(status)	(((status) >> 16) & 0xff)
#define UART_FIFO_SIZE		128
#define UART_INT_ST		0x08
#define UART_INT_ENA		0x0c
#define UART_INT_CLR		0x10
#define UART_CONF1		0x24
#define UART_INT_RXFIFO_FULL	(1 << 0)
#define UART_CONF1_RXFULL_MASK	0x7f	/* rx threshold, bits 6..0 */

/* Interrupt matrix: one register per peripheral source, for the PRO CPU */
#define DPORT_PRO_INTR_MAP(src)	(0x3ff00104 + 4 * (src))
#define INTR_SOURCES		69
#define INTR_SRC_UART0		34

/* Reset */
#define RTC_OPTIONS0		0x00	/* in RTCCNTL_BASE */
#define RTC_SW_SYS_RST		(1 << 31)

/* GPIO matrix */
#define GPIO_BASE		0x3ff44000
#define GPIO_OUT_W1TS		0x08	/* GPIO 0..31 */
#define GPIO_OUT_W1TC		0x0c
#define GPIO_OUT1_W1TS		0x14	/* GPIO 32..39 */
#define GPIO_OUT1_W1TC		0x18
#define GPIO_ENABLE_W1TS	0x24
#define GPIO_ENABLE_W1TC	0x28
#define GPIO_ENABLE1_W1TS	0x30
#define GPIO_ENABLE1_W1TC	0x34
#define GPIO_IN			0x3c
#define GPIO_IN1		0x40
#define GPIO_PIN(n)		(0x88 + 4 * (n))
#define GPIO_FUNC_OUT_SEL(n)	(0x530 + 4 * (n))
#define GPIO_OUT_SEL_GPIO	256		/* "simple GPIO output" */
#define GPIO_OEN_SEL		(1 << 10)	/* OE comes from ENABLE reg */

/* IO_MUX: one register per pad, placed at random (see gpio.c) */
#define IO_MUX_BASE		0x3ff49000
#define IO_MUX_MCU_SEL_SHIFT	12
#define IO_MUX_MCU_SEL_MASK	(7 << IO_MUX_MCU_SEL_SHIFT)
#define IO_MUX_FUN_IE		(1 << 9)
#define IO_MUX_FUNC_GPIO	2	/* hardware function number of GPIO */

/* Watchdogs: one in the RTC block and one per timer group */
#define RTCCNTL_BASE		0x3ff48000
#define RTC_WDTCONFIG0		0x8c
#define RTC_WDTWPROTECT		0xa4
#define TIMG0_BASE		0x3ff5f000
#define TIMG1_BASE		0x3ff60000
#define TIMG_WDTCONFIG0		0x48
#define TIMG_WDTWPROTECT	0x64
#define WDT_WKEY		0x50d83aa1	/* unlocks a WPROTECT reg */

#endif /* __REGS_H__ */
