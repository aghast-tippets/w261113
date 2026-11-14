/*
 * gpio.c -- GPIO for the ESP32, same API as the LPC1343 version.
 *
 * Each pad has an IO_MUX register, and their placement in the memory
 * map is absolutely random.  As in the LPC code, a table of one byte
 * per GPIO stores the register index (offset / 4); it is built from
 * the full hex address, so you can grep the TRM for what you see here.
 * Zero means "no such pad" (the first IO_MUX register is not a pad).
 */
#include "types.h"
#include "regs.h"
#include "gpio.h"

#define MUX(addr)	(((addr) - IO_MUX_BASE) / 4)

static const u8 gpio_mux[GPIO_MAX] = {
	[0]  = MUX(0x3ff49044),	[1]  = MUX(0x3ff49088),	/* U0TXD */
	[2]  = MUX(0x3ff49040),	[3]  = MUX(0x3ff49084),	/* U0RXD */
	[4]  = MUX(0x3ff49048),	[5]  = MUX(0x3ff4906c),
	[6]  = MUX(0x3ff49060),	[7]  = MUX(0x3ff49064),	/* 6..11: flash */
	[8]  = MUX(0x3ff49068),	[9]  = MUX(0x3ff49054),
	[10] = MUX(0x3ff49058),	[11] = MUX(0x3ff4905c),
	[12] = MUX(0x3ff49034),	[13] = MUX(0x3ff49038),
	[14] = MUX(0x3ff49030),	[15] = MUX(0x3ff4903c),
	[16] = MUX(0x3ff4904c),	[17] = MUX(0x3ff49050),
	[18] = MUX(0x3ff49070),	[19] = MUX(0x3ff49074),
	[20] = MUX(0x3ff49078),	[21] = MUX(0x3ff4907c),	/* 20: few chips */
	[22] = MUX(0x3ff49080),	[23] = MUX(0x3ff4908c),
	[25] = MUX(0x3ff49024),	[26] = MUX(0x3ff49028),
	[27] = MUX(0x3ff4902c),
	[32] = MUX(0x3ff4901c),	[33] = MUX(0x3ff49020),
	[34] = MUX(0x3ff49014),	[35] = MUX(0x3ff49018),	/* 34..39: input */
	[36] = MUX(0x3ff49004),	[37] = MUX(0x3ff49008),
	[38] = MUX(0x3ff4900c),	[39] = MUX(0x3ff49010),
};

/* Per-port registers: index 0 is GPIO 0..31, index 1 is GPIO 32..39 */
static const u16 reg_set[2] = { GPIO_OUT_W1TS, GPIO_OUT1_W1TS };
static const u16 reg_clr[2] = { GPIO_OUT_W1TC, GPIO_OUT1_W1TC };
static const u16 reg_oe_set[2] = { GPIO_ENABLE_W1TS, GPIO_ENABLE1_W1TS };
static const u16 reg_oe_clr[2] = { GPIO_ENABLE_W1TC, GPIO_ENABLE1_W1TC };
static const u16 reg_in[2] = { GPIO_IN, GPIO_IN1 };

static int gpio_valid(int gpio)
{
	if (gpio < 0 || gpio >= GPIO_MAX || !gpio_mux[gpio])
		return 0;
	if (gpio >= 6 && gpio <= 11)	/* the flash chip is wired here */
		return 0;
	return 1;
}

/* GPIO clocks are always on in the ESP32: nothing to do, kept for API */
void gpio_init(void)
{
}

/* AF0 is GPIO for portability; the hardware has GPIO at function 2 */
static int af_to_hw(int afnum)
{
	if (afnum == 0)
		return IO_MUX_FUNC_GPIO;
	if (afnum == IO_MUX_FUNC_GPIO)
		return 0;
	return afnum;
}

int gpio_dir(int gpio, int output, int value)
{
	int port = GPIO_PORT(gpio);
	u32 bit = 1 << GPIO_BIT(gpio);

	if (output) {
		/* Here the value can be set before enabling: no glitch */
		__gpio_set(gpio, value);
		writel(bit, GPIO_BASE + reg_oe_set[port]);
	} else {
		writel(bit, GPIO_BASE + reg_oe_clr[port]);
	}
	return 0;
}

/* The only function that checks its arguments: call it once per pin */
int gpio_dir_af(int gpio, int output, int value, int afnum)
{
	u32 mux, v;

	if (!gpio_valid(gpio) || afnum < 0 || afnum > 5)
		return -1;
	if (output && gpio >= 34)
		return -1;

	mux = IO_MUX_BASE + 4 * gpio_mux[gpio];
	v = readl(mux) & ~IO_MUX_MCU_SEL_MASK;
	v |= af_to_hw(afnum) << IO_MUX_MCU_SEL_SHIFT;
	v |= IO_MUX_FUN_IE;		/* input on, so outputs read back */
	writel(v, mux);

	if (afnum != 0)
		return 0;

	/* Route the pad to the GPIO block, push-pull, no interrupts */
	writel(0, GPIO_BASE + GPIO_PIN(gpio));
	writel(GPIO_OUT_SEL_GPIO | GPIO_OEN_SEL,
	       GPIO_BASE + GPIO_FUNC_OUT_SEL(gpio));
	return gpio_dir(gpio, output, value);
}

u32 __gpio_get(int gpio)
{
	return readl(GPIO_BASE + reg_in[GPIO_PORT(gpio)])
		& (1 << GPIO_BIT(gpio));
}

void __gpio_set(int gpio, u32 value)
{
	int port = GPIO_PORT(gpio);

	writel(1 << GPIO_BIT(gpio),
	       GPIO_BASE + (value ? reg_set[port] : reg_clr[port]));
}
