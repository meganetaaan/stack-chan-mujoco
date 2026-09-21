/* GPIO callback semantics only: no claim about real voltage or timing. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "g030_power_runtime.h"
#include "g030_gpio_mmio.h"
static uint32_t regs[3][10];
static unsigned reads,writes;
static int access_fault,fail_next_read,fail_next_write,drop_next_write;
uint32_t power_g030_mmio_read(unsigned port,unsigned reg) {
    assert(port<3 && reg<=36 && !(reg%4));reads++;
    if(fail_next_read) { access_fault=1;fail_next_read=0; }
    return regs[port][reg/4];
}
void power_g030_mmio_write(unsigned port,unsigned reg,uint32_t value) {
    assert(port<3 && reg<=36 && !(reg%4));writes++;
    if(fail_next_write) { access_fault=1;fail_next_write=0; }
    if(drop_next_write) { drop_next_write=0;return; }
    if(reg==P_BSRR) regs[port][P_ODR/4]=(regs[port][P_ODR/4]|(value&65535u))&~(value>>16);
    else regs[port][reg/4]=value;
}
int power_g030_mmio_ok(void) { return !access_fault; }
static void reset_hardware_model(void) {
    memset(regs,0,sizeof(regs));access_fault=0;
    fail_next_read=fail_next_write=drop_next_write=0;
}
static void assert_inhibited(struct power_runtime *c,uint8_t request) {
    assert(c->io_fault && c->state==POWER_CLEAR_RESET);
    assert(request==P_OUT_CLEAR);
    assert(!(regs[0][P_ODR/4]&(1u<<8)));
    assert(regs[0][P_ODR/4]&(1u<<11));
}
static void reach_run(struct power_runtime *c,struct power_deadline *t) {
    assert(power_g030_runtime_boot(c,t,10));
    assert(c->state==POWER_CLEAR_RESET);
    const uint16_t masks[]={7|128,7|128|256,7,7|32|64,7|32|64|24};
    for(unsigned i=0;i<5;i++) (void)power_g030_runtime_step(c,t,i,masks[i]);
    assert(c->state==POWER_RUN);
    assert(regs[0][P_ODR/4]&(1u<<8));
}
int main(void) {
    struct power_runtime c;struct power_deadline t;
    unsigned scenarios=0;
    for(unsigned mode=0;mode<3;mode++) {
        reset_hardware_model();reach_run(&c,&t);
        if(mode==0) access_fault=1;
        if(mode==1) fail_next_read=1;
        if(mode==2) fail_next_write=1;
        uint8_t q=power_g030_runtime_step(&c,&t,6,7|32|64|24);
        assert_inhibited(&c,q);
        /* Even a later apparently healthy adapter cannot clear runtime memory. */
        access_fault=0;
        for(unsigned k=0;k<5;k++) assert_inhibited(&c,power_g030_runtime_step(&c,&t,7+k,127));
        scenarios++;
    }
    reset_hardware_model();access_fault=1;
    unsigned old_writes=writes;
    assert(!power_g030_runtime_boot(&c,&t,10) && c.io_fault);
    assert(writes==old_writes);scenarios++;
    reset_hardware_model();fail_next_write=1;
    assert(!power_g030_runtime_boot(&c,&t,10) && c.io_fault);scenarios++;
    reset_hardware_model();drop_next_write=1;
    assert(!power_g030_runtime_boot(&c,&t,10) && c.io_fault);scenarios++;
    const uint32_t invalid_limits[]={0,UINT32_C(0x80000000),UINT32_MAX};
    for(unsigned i=0;i<3;i++) {
        reset_hardware_model();old_writes=writes;
        assert(!power_g030_runtime_boot(&c,&t,invalid_limits[i]) && c.io_fault);
        assert(writes==old_writes);scenarios++;
    }
    reset_hardware_model();assert(!power_g030_runtime_boot(&c,0,10) && c.io_fault);
    assert(!power_g030_runtime_boot(0,&t,10));scenarios++;
    reset_hardware_model();reach_run(&c,&t);
    assert_inhibited(&c,power_g030_runtime_step(&c,0,6,127));scenarios++;
    printf("{\"fault_scenarios\":%u,\"model_reads\":%u,\"model_writes\":%u}\n",scenarios,reads,writes);
    return 0;
}
