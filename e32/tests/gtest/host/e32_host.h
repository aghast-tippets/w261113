/*
 * e32_host.h -- what the firmware sees instead of hardware in the host
 * test build (compiled with -DE32_HOST, see include/types.h and
 * include/xtensa.h).  Implemented in sim.cpp by the simulated SoC.
 */
#ifndef __E32_HOST_H__
#define __E32_HOST_H__

#ifdef __cplusplus
extern "C" {
#endif

/* Bus: every readl/writel in the firmware lands here */
unsigned int e32_host_readl(unsigned int addr);
void e32_host_writel(unsigned int val, unsigned int addr);

/* CPU: cycle counter, special registers, PS.INTLEVEL, waiti, traps */
unsigned int e32_host_ccount(void);
unsigned int e32_host_rsr(const char *sr);
void e32_host_wsr(const char *sr, unsigned int v);
unsigned int e32_host_irq_save(void);
void e32_host_irq_restore(unsigned int ps);
void e32_host_waiti0(void);
void e32_host_trap(const char *what);

#ifdef __cplusplus
}
#else
static inline u32 readl(u32 addr)
{
	return e32_host_readl(addr);
}

static inline void writel(u32 val, u32 addr)
{
	e32_host_writel(val, addr);
}

static inline u32 get_ccount(void)
{
	return e32_host_ccount();
}
#endif

#endif /* __E32_HOST_H__ */
