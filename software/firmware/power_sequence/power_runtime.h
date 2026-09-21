#ifndef STACKCHAN_POWER_RUNTIME_H
#define STACKCHAN_POWER_RUNTIME_H
#include "g030_gpio_outputs.h"
struct power_runtime { uint8_t state; uint8_t io_fault; };
/* Boot only, after GPIO initialization result is known. Do not use as a
 * runtime fault-clear API. GPIO reset may not replace a new physical press. */
void power_runtime_boot(struct power_runtime *ctx,int gpio_ready);
/* Returns requested outputs (including internal timer-run), not pin levels.
 * io_fault is sticky until a new boot; independent hardware cutoff required. */
uint8_t power_runtime_step(struct power_runtime *ctx,uint16_t observations,
                          p_gpio_read read,p_gpio_write write);
#endif
