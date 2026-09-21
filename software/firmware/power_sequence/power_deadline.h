#ifndef STACKCHAN_POWER_DEADLINE_H
#define STACKCHAN_POWER_DEADLINE_H
#include "power_runtime.h"
struct power_deadline {
    uint32_t limit_ticks, start_tick, last_tick;
    uint8_t active, expired;
};
/* No default limit. 0 and >=2^31 are invalid. Units come from a qualified
 * hardware timebase. Call at intervals <2^31 ticks; stalled clocks require
 * independent supervision. Initialization is for boot/configuration only. */
void power_deadline_init(struct power_deadline *timer,uint32_t limit_ticks);
int power_deadline_update(struct power_deadline *timer,int run,uint32_t now);
/* Missing/invalid timer latches a runtime fault in every phase. */
uint8_t power_runtime_timed_step(struct power_runtime *ctx,struct power_deadline *timer,
    uint32_t now,uint16_t observations,p_gpio_read read,p_gpio_write write);
#endif
