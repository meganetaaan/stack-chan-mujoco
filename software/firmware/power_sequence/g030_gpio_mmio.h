#ifndef STACKCHAN_G030_GPIO_MMIO_H
#define STACKCHAN_G030_GPIO_MMIO_H
#include "g030_gpio_init.h"
/* STM32G030 only. The caller must meet g030_gpio_init.h's boot prerequisites.
 * No clock/reset/RTC setup is performed here. No concurrent writers allowed.
 * Invalid access latches a software fault until MCU reset. Check mmio_ok before
 * and after each sequence step and latch failure into power_runtime.io_fault.
 * Valid accesses remain possible after a fault for best-effort output disable.
 * A successful access/readback is NOT proof of the physical pin level. */
uint32_t power_g030_mmio_read(unsigned port, unsigned reg);
void power_g030_mmio_write(unsigned port, unsigned reg, uint32_t value);
int power_g030_mmio_ok(void);
#endif
