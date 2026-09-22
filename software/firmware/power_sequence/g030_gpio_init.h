#ifndef STACKCHAN_G030_GPIO_INIT_H
#define STACKCHAN_G030_GPIO_INIT_H
#include <stdint.h>
enum p_gpio_reg { P_MODER=0x00, P_OTYPER=0x04, P_OSPEEDR=0x08,
    P_PUPDR=0x0c, P_IDR=0x10, P_ODR=0x14, P_BSRR=0x18, P_AFRL=0x20, P_AFRH=0x24 };
typedef uint32_t (*p_gpio_read)(unsigned port, unsigned reg);
typedef void (*p_gpio_write)(unsigned port, unsigned reg, uint32_t value);
/* Ports A/B/C = 0/1/2. Caller must hold external power inhibition, enable
 * GPIO clocks, disable RTC/external clock ownership and PA9/10 remapping,
 * and exclude concurrent register writers. This is not complete boot code. */
int power_g030_gpio_init(p_gpio_read read, p_gpio_write write);
#endif
