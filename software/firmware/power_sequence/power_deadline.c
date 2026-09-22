#include "power_deadline.h"
void power_deadline_init(struct power_deadline *t,uint32_t limit) {
    if(!t) return;
    t->limit_ticks=limit;t->start_tick=0;t->last_tick=0;t->active=0;t->expired=0;
}
int power_deadline_update(struct power_deadline *t,int run,uint32_t now) {
    if(!t || !t->limit_ticks || t->limit_ticks>=UINT32_C(0x80000000)) return 1;
    if(!run) {
        t->active=0;t->expired=0;t->last_tick=now;
        return 0;
    }
    if(!t->active) {
        t->start_tick=now;t->last_tick=now;t->active=1;t->expired=0;
        return 0;
    }
    if((uint32_t)(now-t->last_tick)>=UINT32_C(0x80000000) ||
       (uint32_t)(now-t->start_tick)>=t->limit_ticks) t->expired=1;
    t->last_tick=now;
    return t->expired!=0;
}
uint8_t power_runtime_timed_step(struct power_runtime *ctx,struct power_deadline *timer,
    uint32_t now,uint16_t in,p_gpio_read read,p_gpio_write write) {
    /* Configuration failure is independent of the startup phase. */
    if(ctx && (!timer || !timer->limit_ticks ||
               timer->limit_ticks>=UINT32_C(0x80000000))) ctx->io_fault=1;
    int run=ctx && ctx->state==POWER_START && !ctx->io_fault;
    int expired=power_deadline_update(timer,run,now);
    in=(uint16_t)(in&~P_IN_STARTUP_EXPIRED);
    if(expired) in|=P_IN_STARTUP_EXPIRED;
    return power_runtime_step(ctx,in,read,write);
}
