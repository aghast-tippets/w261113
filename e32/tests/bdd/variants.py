"""
Build variants: source patches applied to a scenario's private copy of the
e32 tree (never to the working tree).  The next build step picks them up.

UNTESTED on the target: the cross compiler was not available when these
were written.  Each patch asserts that the text it replaces exists, so a
source change makes the scenario fail loudly instead of testing the wrong
thing.
"""
import re
from pathlib import Path


def _replace(tree, rel, old, new, count=1):
    path = Path(tree) / rel
    src = path.read_text()
    assert old in src, f"build variant: {old!r} not found in {rel}"
    path.write_text(src.replace(old, new, count))


def _append(tree, rel, text):
    path = Path(tree) / rel
    path.write_text(path.read_text() + "\n" + text + "\n")


def replace_text(tree, rel, old, new):
    _replace(tree, rel, old, new)


def add_text(tree, rel, text):
    _append(tree, rel, text)


def timer_hz(tree, hz):
    _replace(tree, "main.c", "timer_init(HZ);", f"timer_init({int(hz)});")


def rxbuf_size(tree, n):
    path = Path(tree) / "io.c"
    src = path.read_text()
    new, k = re.subn(r"#define RXBUF_SIZE \d+", f"#define RXBUF_SIZE {int(n)}", src)
    assert k == 1, "build variant: RXBUF_SIZE not found in io.c"
    path.write_text(new)


def blink(tree):
    _replace(tree, "main.c", "if (1)\n\t\tmimmo();", "if (0)\n\t\tmimmo();")


# --- stress command "S" and the alloca counter -----------------------------

ALLOCA_COUNTER_ASM = """\
	rsync
	movi	a2, alloca_count	/* test variant: count alloca exceptions */
	l32i	a3, a2, 0		/* a2, a3 belong to the spilled caller, */
	addi	a3, a3, 1		/* which the underflow handler reloads */
	s32i	a3, a2, 0
"""

STRESS_C = r"""
/* --- test variant: stress command "S" --- */
volatile u32 alloca_count;

static void stress(void)
{
	int i, bad = 0;
	u32 t0 = jiffies, a0 = alloca_count;

	for (i = 0; i < 2000; i++) {
		int n = 100 + i % 16;

		if (recurse(200) != 20100)
			bad++;
		if (vla_after_spill(n) != 820 + (n - 1))
			bad++;
	}
	printf("stress: %i bad, %u ticks, %u alloca exceptions\n", bad,
	       jiffies - t0, alloca_count - a0);
}
"""


def stress_command(tree, count_alloca=True):
    """Add mimmo command "S": 2000 rounds of recurse(200) and
    vla_after_spill(100 + i % 16), printing
    "stress: <bad> bad, <ticks> ticks, <n> alloca exceptions"."""
    _replace(tree, "mimmo.c", "static void irq_stats(void)", STRESS_C + "\nstatic void irq_stats(void)")
    _replace(tree, "mimmo.c", "\t\tcase 'h':\n", "\t\tcase 'S':\n\t\t\tstress();\n\t\t\tbreak;\n\n\t\tcase 'h':\n")
    if count_alloca:
        path = Path(tree) / "vectors.S"
        src = path.read_text()
        anchor = "\twsr\ta2, PS\n\trsync\n"
        assert src.count(anchor) >= 1 and "_alloca_handler:" in src, "alloca handler not found"
        head, tail = src.split("_alloca_handler:", 1)
        assert anchor in tail, "alloca handler layout changed"
        tail = tail.replace(anchor, "\twsr\ta2, PS\n" + ALLOCA_COUNTER_ASM, 1)
        path.write_text(head + "_alloca_handler:" + tail)
    else:
        # keep alloca_count defined but never incremented
        pass


# --- watchdog ---------------------------------------------------------------

WDT_ARM_C = r"""
/* --- test variant: arm the timer-group-0 watchdog like the ROM does --- */
#define TIMG_WDTCONFIG1		0x4c
#define TIMG_WDTCONFIG2		0x50
#define TIMG_WDTFEED		0x60

static void wdt_arm_tg0(void)
{
	writel(WDT_WKEY, TIMG0_BASE + TIMG_WDTWPROTECT);
	writel(1 << 16, TIMG0_BASE + TIMG_WDTCONFIG1);		/* prescale 1: APB cycles */
	writel(26000000, TIMG0_BASE + TIMG_WDTCONFIG2);		/* stage 0 timeout */
	writel((1u << 31) | (3 << 29) | (7 << 18) | (7 << 15),	/* EN, stage 0 = reset system */
	       TIMG0_BASE + TIMG_WDTCONFIG0);
	writel(1, TIMG0_BASE + TIMG_WDTFEED);
	writel(0, TIMG0_BASE + TIMG_WDTWPROTECT);
}
"""


def wdt_armed(tree, call_disable=True):
    """Arm TG0's watchdog at the start of wdt_disable(), which boot.S calls
    first; without call_disable, wdt_disable() returns right after arming."""
    _replace(tree, "wdt.c", "void wdt_disable(void)\n{\n",
             WDT_ARM_C + "\nvoid wdt_disable(void)\n{\n\twdt_arm_tg0();\n"
             + ("" if call_disable else "\treturn;\n"))
