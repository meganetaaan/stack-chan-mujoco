#ifndef STACKCHAN_G030_POWER_RUNTIME_H
#define STACKCHAN_G030_POWER_RUNTIME_H
#include "power_deadline.h"
/* Boot-only bridge to the STM32G030 MMIO callbacks. Requires qualified GPIO
 * clocks/ownership and external inhibition as documented by g030_gpio_init.h.
 * Does not release external inhibition. No default startup deadline is supplied.
 * A failure must not be retried as an automatic restart. */
int power_g030_runtime_boot(struct power_runtime *ctx,
                           struct power_deadline *timer,uint32_t limit_ticks);
/* Observations and time must already be qualified; this does not read raw IDR.
 * Remembers MMIO access faults before/after a step and attempts CLEAR in the
 * same call on a newly reported fault. Independent hardware cutoff is required. */
uint8_t power_g030_runtime_step(struct power_runtime *ctx,
    struct power_deadline *timer,uint32_t now,uint16_t observations);
#endif
