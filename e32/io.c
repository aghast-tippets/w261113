/*
 * io.c -- polled serial I/O on UART0
 */
#include "types.h"
#include "regs.h"
#include "io.h"
#include "irq.h"

static inline u32 uart_status(void)
{
	return readl(UART0_BASE + UART_STATUS);
}

/*
 * Unlike the LPC1343, the ESP32 ROM configures UART0 at 115200 8N1 in
 * both boot paths (it prints its boot messages there), so we keep its
 * divisor rather than guessing the APB clock.  We only wait for the
 * ROM's last characters to leave, so they don't mix with ours.
 */
void serial_setup(void)
{
	while (UART_TXCNT(uart_status()))
		;
}

void putc(int c)
{
	if (c == '\n')
		putc('\r');
	/*
	 * Wait for room.  Reading the status between FIFO writes also
	 * keeps us clear of the ESP32 errata on back-to-back writes to
	 * the same peripheral address.
	 */
	while (UART_TXCNT(uart_status()) >= UART_FIFO_SIZE - 2)
		;
	writel(c & 0xff, UART0_BASE + UART_FIFO);
}

void puts(const char *s)
{
	while (*s)
		putc(*s++);
}

/*
 * Receive: polled until serial_irq_init(), then from a ring buffer that
 * the interrupt handler fills.  The 128-byte hardware FIFO is then no
 * longer a limit (e.g. when pasting into mimmo), and getc() sleeps.
 */
#define RXBUF_SIZE 256			/* power of two */
static volatile u8 rxbuf[RXBUF_SIZE];
static volatile u32 rx_head, rx_tail, rx_overruns;
static int rx_irq_mode;

static void uart_rx_irq(int irq, void *arg)
{
	u32 c;

	while (UART_RXCNT(uart_status())) {
		c = readl(UART0_BASE + UART_FIFO) & 0xff;
		if (rx_head - rx_tail < RXBUF_SIZE)
			rxbuf[rx_head++ % RXBUF_SIZE] = c;
		else
			rx_overruns++;
	}
	writel(UART_INT_RXFIFO_FULL, UART0_BASE + UART_INT_CLR);
}

void serial_irq_init(int irq)
{
	u32 conf1 = readl(UART0_BASE + UART_CONF1);

	/* Interrupt as soon as one byte is in the FIFO */
	conf1 = (conf1 & ~UART_CONF1_RXFULL_MASK) | 1;
	writel(conf1, UART0_BASE + UART_CONF1);
	writel(0xffffffff, UART0_BASE + UART_INT_CLR);
	writel(UART_INT_RXFIFO_FULL, UART0_BASE + UART_INT_ENA);

	irq_map(INTR_SRC_UART0, irq);
	rx_irq_mode = 1;
	irq_request(irq, uart_rx_irq, 0);
}

int getc(void)
{
	u32 flags;
	int c;

	if (!rx_irq_mode) {
		while (UART_RXCNT(uart_status()) == 0)
			;
		return readl(UART0_BASE + UART_FIFO) & 0xff;
	}
	/*
	 * Check the buffer with interrupts masked; if empty, "waiti 0"
	 * unmasks and sleeps in one step, so no interrupt can slip in
	 * between the check and the sleep.
	 */
	while (1) {
		flags = irq_save();
		if (rx_head != rx_tail)
			break;
		cpu_waiti0();
	}
	c = rxbuf[rx_tail++ % RXBUF_SIZE];
	irq_restore(flags);
	return c;
}

/* Read a line with echo and backspace; the newline is not stored */
int gets(char *s, int size)
{
	int c, i = 0;

	while (1) {
		c = getc();
		if (c == '\r' || c == '\n') {
			putc('\n');
			break;
		}
		if (c == '\b' || c == 0x7f) {
			if (i) {
				i--;
				puts("\b \b");
			}
			continue;
		}
		if (c < ' ' || i >= size - 1)
			continue;
		s[i++] = c;
		putc(c);
	}
	s[i] = '\0';
	return i;
}
