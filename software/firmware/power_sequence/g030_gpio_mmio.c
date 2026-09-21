#include "g030_gpio_mmio.h"
/* ST CMSIS stm32g030xx.h: IOPORT_BASE + A/B/C offsets 0/0x400/0x800.
 * Register-map evidence is recorded in validation/g030_gpio_mmio_v1. */
#define GPIO_BASE UINT32_C(0x50000000)
#define GPIO_STRIDE UINT32_C(0x400)
static int access_fault;
static volatile uint32_t *address(unsigned port, unsigned reg, int writing) {
    int allowed=0;
    if(port<3) {
        switch(reg) {
        case P_MODER: case P_OTYPER: case P_OSPEEDR: case P_PUPDR:
        case P_AFRL: case P_AFRH:
            allowed=1; break;
        case P_IDR: case P_ODR:
            allowed=!writing; break;
        case P_BSRR:
            allowed=writing; break;
        default: break;
        }
    }
    if(!allowed) { access_fault=1; return 0; }
    return (volatile uint32_t *)(uintptr_t)(GPIO_BASE+GPIO_STRIDE*port+reg);
}
uint32_t power_g030_mmio_read(unsigned port, unsigned reg) {
    volatile uint32_t *p=address(port,reg,0);
    return p ? *p : 0;
}
void power_g030_mmio_write(unsigned port, unsigned reg, uint32_t value) {
    volatile uint32_t *p=address(port,reg,1);
    if(p) *p=value;
}
int power_g030_mmio_ok(void) { return !access_fault; }
