#include "g030_power_runtime.h"
#include "g030_gpio_mmio.h"
int power_g030_runtime_boot(struct power_runtime *ctx,
                           struct power_deadline *timer,uint32_t limit_ticks) {
    /* Start inhibited even if a pointer/configuration is invalid. */
    power_runtime_boot(ctx,0);
    power_deadline_init(timer,limit_ticks);
    if(!ctx || !timer || !limit_ticks || limit_ticks>=UINT32_C(0x80000000))
        return 0;
    int ready=power_g030_mmio_ok() &&
        power_g030_gpio_init(power_g030_mmio_read,power_g030_mmio_write) &&
        power_g030_mmio_ok();
    power_runtime_boot(ctx,ready);
    return ready;
}
uint8_t power_g030_runtime_step(struct power_runtime *ctx,
    struct power_deadline *timer,uint32_t now,uint16_t observations) {
    if(ctx && !power_g030_mmio_ok()) ctx->io_fault=1;
    uint8_t request=power_runtime_timed_step(ctx,timer,now,observations,
                                           power_g030_mmio_read,power_g030_mmio_write);
    if(!power_g030_mmio_ok()) {
        if(ctx) ctx->io_fault=1;
        /* A valid ODR read can coexist with an adapter access fault. Do not
         * wait for the next scheduler invocation to request inhibition. */
        request=power_runtime_step(ctx,0,power_g030_mmio_read,power_g030_mmio_write);
    }
    return request;
}
