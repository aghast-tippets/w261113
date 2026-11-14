/*
 * mimmo.c -- MIni Memory MOnitor, ESP32 edition.
 *
 * Addresses and values are hex, GPIO numbers are decimal (as printed on
 * every ESP32 board and in the datasheet).  A bad address raises an
 * exception: panic.c prints the registers and reboots on a key press.
 */
#include "types.h"
#include "io.h"
#include "gpio.h"
#include "irq.h"

static const char *skip_blanks(const char *s)
{
	while (*s == ' ' || *s == '\t')
		s++;
	return s;
}

/* Parse a number in the given base; return 0 on success */
static int get_num(const char **sp, int base, u32 *val)
{
	const char *s = skip_blanks(*sp);
	u32 v = 0;
	int d, n = 0;

	if (base == 16 && s[0] == '0' && (s[1] == 'x' || s[1] == 'X'))
		s += 2;
	for (;; s++, n++) {
		if (*s >= '0' && *s <= '9')
			d = *s - '0';
		else if (*s >= 'a' && *s <= 'f')
			d = *s - 'a' + 10;
		else if (*s >= 'A' && *s <= 'F')
			d = *s - 'A' + 10;
		else
			break;
		if (d >= base)
			return -1;
		v = v * base + d;
	}
	if (!n || (*s && *s != ' ' && *s != '\t'))
		return -1;
	*sp = s;
	*val = v;
	return 0;
}

static void help(void)
{
	puts("r <addr>              read a 32-bit word\n"
	     "w <addr> <value>      write a 32-bit word\n"
	     "d <addr> [<count>]    dump words (default 16)\n"
	     "p <gpio> [0|1]        GPIO: set output, or read as input\n"
	     "a <gpio> <af>         set alternate function (0 = GPIO)\n"
	     "g <addr>              call address (needs an 'entry' insn)\n"
	     "i                     interrupt counts and uptime\n"
	     "s                     self test: windows, alloca, soft irq\n"
	     "f <n>                 fault on purpose: 0 NULL load, 1 illegal\n"
	     "                      insn, 2 divide by zero, 3 break, 4 bad\n"
	     "                      sp (double exc.), 5 level-3 interrupt\n"
	     "h                     this help\n");
}

/* --- self test --- */

static int __attribute__((noinline)) recurse(int n)
{
	volatile int x = n;

	return n ? recurse(n - 1) + x : 0;
}

/*
 * After the deep recursion our caller's registers are spilled; the
 * variable-length array then moves sp with "movsp", which raises the
 * alloca exception that vectors.S must fix up.
 */
static int __attribute__((noinline)) vla_after_spill(int n)
{
	int i, sum = recurse(40);
	volatile char buf[n];

	for (i = 0; i < n; i++)
		buf[i] = i;
	return sum + buf[n - 1];
}

static volatile int soft_hits;

static void soft_irq(int irq, void *arg)
{
	soft_hits++;
}

static void self_test(void)
{
	int r, ok = 1;

	r = recurse(200);
	printf("recursion 200 deep: %i (%s)\n", r, r == 20100 ? "ok" : "BAD");
	ok &= r == 20100;

	r = vla_after_spill(100);
	printf("VLA after spill:   %i (%s)\n", r, r == 919 ? "ok" : "BAD");
	ok &= r == 919;

	irq_request(INT_SOFTWARE, soft_irq, 0);
	soft_hits = 0;
	WSR(intset, 1 << INT_SOFTWARE);
	printf("software irq:      %i hit (%s)\n", soft_hits,
	       soft_hits == 1 ? "ok" : "BAD");
	ok &= soft_hits == 1;
	irq_disable(INT_SOFTWARE);

	r = jiffies;
	udelay(100 * 1000);
	r = jiffies - r;
	printf("ticks in 100ms:    %i (%s)\n", r,
	       r >= HZ / 10 - 1 && r <= HZ / 10 + 1 ? "ok" : "BAD");
	ok &= r >= HZ / 10 - 1 && r <= HZ / 10 + 1;
	puts(ok ? "all ok\n" : "FAILED\n");
}

static void fault(int n)
{
	volatile int zero = 0, hundred = 100;	/* gcc turns 1/x into a compare */

	switch (n) {
	case 0:
		printf("%08x\n", *(volatile u32 *)zero);
		break;
	case 1:
		asm volatile ("ill");
		break;
	case 2:
		printf("%i\n", hundred / zero);
		break;
	case 3:
		asm volatile ("break 1, 15");
		break;
	case 4:
		/*
		 * Point sp at unmapped memory and wait: the next tick's
		 * interrupt entry stores its frame there while PS.EXCM is
		 * set, which is a double exception.
		 */
		asm volatile ("movi a1, 0x100\n1: j 1b");
		break;
	case 5:
		/* Software interrupt 29 is level 3: no handler level exists */
		WSR(intenable, RSR(intenable) | (1 << 29));
		WSR(intset, 1 << 29);
		break;
	}
}

static void irq_stats(void)
{
	int i;

	printf("uptime %u.%02u s (%u ticks)\n", jiffies / HZ,
	       (jiffies % HZ) * 100 / HZ, jiffies);
	for (i = 0; i < 32; i++)
		if (irq_count(i))
			printf("irq %2i: %u\n", i, irq_count(i));
}

void mimmo(void)
{
	char line[80];
	const char *s;
	u32 addr, val, i;
	int cmd, ret;

	puts("mimmo.c: Ready to get input (h for help)\n");
	while (1) {
		puts("> ");
		gets(line, sizeof(line));
		s = skip_blanks(line);
		cmd = *s;
		if (cmd)
			s++;

		switch (cmd) {
		case '\0':
			break;

		case 'r':
			if (get_num(&s, 16, &addr) || (addr & 3))
				goto bad;
			printf("read %08x\n%08x\n", addr, readl(addr));
			break;

		case 'w':
			if (get_num(&s, 16, &addr) || (addr & 3)
			    || get_num(&s, 16, &val))
				goto bad;
			writel(val, addr);
			printf("write %08x = %08x\n", addr, val);
			break;

		case 'd':
			if (get_num(&s, 16, &addr) || (addr & 3))
				goto bad;
			if (get_num(&s, 16, &val))
				val = 16;
			for (i = 0; i < val; i++, addr += 4) {
				if (!(i & 3))
					printf("%s%08x:", i ? "\n" : "", addr);
				printf(" %08x", readl(addr));
			}
			putc('\n');
			break;

		case 'p':
			if (get_num(&s, 10, &addr))
				goto bad;
			if (get_num(&s, 10, &val)) {
				ret = gpio_dir_af(addr, 0, 0, 0);
				if (ret == 0)
					printf("gpio %u = %i\n", addr,
					       gpio_get(addr));
			} else {
				ret = gpio_dir_af(addr, 1, val, 0);
				if (ret == 0)
					printf("gpio %u <- %i\n", addr, !!val);
			}
			if (ret)
				puts("invalid gpio (6..11 are flash, "
				     "34..39 are input only)\n");
			break;

		case 'a':
			if (get_num(&s, 10, &addr) || get_num(&s, 10, &val))
				goto bad;
			if (gpio_dir_af(addr, 0, 0, val))
				puts("invalid gpio or function\n");
			else
				printf("gpio %u: function %u\n", addr, val);
			break;

		case 'g':
			if (get_num(&s, 16, &addr))
				goto bad;
			printf("go %08x\n", addr);
			((void (*)(void))addr)();
			break;

		case 'i':
			irq_stats();
			break;

		case 's':
			self_test();
			break;

		case 'f':
			if (get_num(&s, 10, &val))
				goto bad;
			fault(val);
			break;

		case 'h':
		case '?':
			help();
			break;

		default:
			goto bad;
		}
		continue;
	bad:
		puts("?? (h for help)\n");
	}
}
