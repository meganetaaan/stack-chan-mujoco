#include "power_runtime.h"
void power_runtime_boot(struct power_runtime *ctx,int gpio_ready) {
    if(!ctx) return;
    ctx->state=POWER_CLEAR_RESET;
    ctx->io_fault=(uint8_t)!gpio_ready;
}
uint8_t power_runtime_step(struct power_runtime *ctx,uint16_t in,
                          p_gpio_read read,p_gpio_write write) {
    uint8_t request;
    if(!ctx) {
        (void)power_g030_apply_outputs(P_OUT_CLEAR,read,write);
        return P_OUT_CLEAR;
    }
    if(ctx->state>POWER_RUN || (in&~1023u)) ctx->io_fault=1;
    request=ctx->io_fault ? P_OUT_CLEAR : power_sequence_outputs(ctx->state,in);
    if(!power_g030_apply_outputs(request,read,write)) ctx->io_fault=1;
    if(ctx->io_fault) {
        ctx->state=POWER_CLEAR_RESET;
        return P_OUT_CLEAR;
    }
    ctx->state=power_sequence_next(ctx->state,in);
    return request;
}
