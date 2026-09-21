#include "g030_gpio_outputs.h"
#define EN_PIN (1u<<8)
#define CLEAR_PIN (1u<<11)
#define QUAL_PIN (1u<<12)
#define CONTROL_PINS (EN_PIN|CLEAR_PIN|QUAL_PIN)
static void apply(p_gpio_write write,uint32_t high) {
    write(0,P_BSRR,high|((CONTROL_PINS&~high)<<16));
}
int power_g030_apply_outputs(uint8_t request,p_gpio_read read,p_gpio_write write) {
    uint32_t high=0;
    int valid=(request&~15u)==0 &&
        !((request&P_OUT_ENABLE)&&(request&P_OUT_CLEAR)) &&
        (!(request&P_OUT_RESET_LOW_VALID)||(request&P_OUT_CLEAR));
    if(!read||!write) return 0;
    if(!valid) request=P_OUT_CLEAR;
    if(request&P_OUT_ENABLE) high|=EN_PIN;
    if(request&P_OUT_CLEAR) high|=CLEAR_PIN;
    if(request&P_OUT_RESET_LOW_VALID) high|=QUAL_PIN;
    apply(write,high);
    if((read(0,P_ODR)&CONTROL_PINS)!=high) {
        apply(write,CLEAR_PIN); /* Best effort only; independent cutoff is required. */
        return 0;
    }
    return valid;
}
