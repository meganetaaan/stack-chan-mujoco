#ifndef STACKCHAN_G030_GPIO_OUTPUTS_H
#define STACKCHAN_G030_GPIO_OUTPUTS_H
#include "g030_gpio_init.h"
#include "power_sequence.h"
/* Requires successful initialization and exclusive GPIO ownership.
 * Returns 0 on invalid request or latch mismatch; caller must retain fault.
 * Timer-run is not a GPIO and must be consumed separately by timer logic. */
int power_g030_apply_outputs(uint8_t request,p_gpio_read read,p_gpio_write write);
#endif
