#include "g030_gpio_init.h"
static uint32_t fields(uint32_t pins) {
    uint32_t mask=0;
    for(unsigned bit=0;bit<16;bit++) if(pins&(1u<<bit)) mask|=3u<<(2*bit);
    return mask;
}
static void update(p_gpio_read r,p_gpio_write w,unsigned p,unsigned reg,uint32_t mask,uint32_t value) {
    w(p,reg,(r(p,reg)&~mask)|(value&mask));
}
int power_g030_gpio_init(p_gpio_read r,p_gpio_write w) {
    const uint32_t pins[3]={0x99ffu,0x03ffu,0xc000u}; /* Preserve PA13/14 SWD. */
    const uint32_t inputs[3]={0x00ffu,0x0080u,0xc000u};
    const uint32_t outputs= (1u<<8)|(1u<<11)|(1u<<12);
    if(!r||!w) return 0;
    /* First release all selected and bonded-alias drivers. */
    for(unsigned p=0;p<3;p++) update(r,w,p,P_MODER,fields(pins[p]),fields(pins[p]));
    for(unsigned p=0;p<3;p++)
        if((r(p,P_MODER)&fields(pins[p]))!=fields(pins[p])) return 0;
    /* Safe data before any output mode: EN=0, CLEAR=1, qualifier=0. */
    w(0,P_BSRR,(1u<<11)|((1u<<8|1u<<12)<<16));
    if((r(0,P_ODR)&outputs)!=(1u<<11)) return 0;
    for(unsigned p=0;p<3;p++) {
        update(r,w,p,P_PUPDR,fields(pins[p]),0);
        update(r,w,p,P_OSPEEDR,fields(pins[p]),0);
        update(r,w,p,P_OTYPER,pins[p],0);
        for(unsigned half=0;half<2;half++) {
            uint32_t mask=0;
            for(unsigned bit=0;bit<8;bit++) if(pins[p]&(1u<<(half*8+bit))) mask|=15u<<(bit*4);
            update(r,w,p,half?P_AFRH:P_AFRL,mask,0);
        }
        update(r,w,p,P_MODER,fields(inputs[p]),0);
    }
    /* Aliases are analog before PA8 drives the shared physical terminal. */
    uint32_t modes=(1u<<(2*8))|(1u<<(2*11))|(1u<<(2*12));
    update(r,w,0,P_MODER,fields(outputs),modes);
    for(unsigned p=0;p<3;p++) {
        uint32_t expected=fields(pins[p])&~fields(inputs[p]);
        if(p==0) expected=(expected&~fields(outputs))|modes;
        if((r(p,P_MODER)&fields(pins[p]))!=expected || (r(p,P_PUPDR)&fields(pins[p]))) return 0;
    }
    return (r(0,P_ODR)&outputs)==(1u<<11);
}
