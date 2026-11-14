/*
 * wdt.c -- turn off the watchdogs the ROM armed for us.
 *
 * On a flash boot the ROM enables the RTC watchdog and the one in timer
 * group 0, so that a broken bootloader resets the chip.  We are the
 * bootloader now, so unless we stop them the board resets every few
 * seconds.  Each watchdog has a write-protect register that must be
 * unlocked with a magic key before its configuration can change.
 */
#include "types.h"
#include "regs.h"
#include "io.h"

static void wdt_off(u32 wprotect, u32 config0)
{
	writel(WDT_WKEY, wprotect);
	writel(0, config0);		/* enable bit and all stages off */
	writel(0, wprotect);		/* lock it again */
}

void wdt_disable(void)
{
	wdt_off(RTCCNTL_BASE + RTC_WDTWPROTECT, RTCCNTL_BASE + RTC_WDTCONFIG0);
	wdt_off(TIMG0_BASE + TIMG_WDTWPROTECT, TIMG0_BASE + TIMG_WDTCONFIG0);
	wdt_off(TIMG1_BASE + TIMG_WDTWPROTECT, TIMG1_BASE + TIMG_WDTCONFIG0);
}
