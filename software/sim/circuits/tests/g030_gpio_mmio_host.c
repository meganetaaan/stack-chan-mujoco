/* Linux host address-translation test, NOT a GPIO peripheral emulator. */
#define _GNU_SOURCE
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#include "g030_gpio_mmio.h"
#ifndef MAP_FIXED_NOREPLACE
#error Test requires MAP_FIXED_NOREPLACE; never overwrite a host mapping.
#endif
int main(void) {
    const uintptr_t base=UINT32_C(0x50000000);
    const size_t size=4096;
    void *mem=mmap((void *)base,size,PROT_READ|PROT_WRITE,
                  MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0);
    if(mem==MAP_FAILED || mem!=(void *)base) {
        if(mem!=MAP_FAILED) (void)munmap(mem,size);
        perror("GPIO test mapping unavailable"); return 77;
    }
    unsigned reads=0,writes=0,invalid=0;
    const unsigned readable[]={0,4,8,12,16,20,32,36};
    const unsigned writable[]={0,4,8,12,24,32,36};
    assert(power_g030_mmio_ok());
    for(unsigned port=0;port<3;port++) {
        for(unsigned i=0;i<sizeof(readable)/sizeof(readable[0]);i++) {
            unsigned reg=readable[i];
            uint32_t *slot=(uint32_t *)(base+port*0x400+reg);
            *slot=0xa55a0000u+port*256+reg;
            assert(power_g030_mmio_read(port,reg)==*slot); reads++;
        }
        for(unsigned i=0;i<sizeof(writable)/sizeof(writable[0]);i++) {
            unsigned reg=writable[i];
            uint32_t before[1024];memcpy(before,mem,size);
            uint32_t value=0x5aa50000u+port*256+reg;
            power_g030_mmio_write(port,reg,value);
            before[(port*0x400+reg)/4]=value;
            assert(memcmp(before,mem,size)==0); writes++;
        }
    }
    assert(power_g030_mmio_ok());
    /* Reserved, unaligned, write-only/read-only, and invalid-port requests. */
    for(unsigned port=0;port<5;port++) for(unsigned reg=0;reg<64;reg++) {
        int r=0,w=0;
        if(port<3) {
            for(unsigned i=0;i<8;i++) if(reg==readable[i]) r=1;
            for(unsigned i=0;i<7;i++) if(reg==writable[i]) w=1;
        }
        if(!r) { assert(power_g030_mmio_read(port,reg)==0); invalid++; }
        if(!w) {
            uint32_t before[1024];memcpy(before,mem,size);
            power_g030_mmio_write(port,reg,UINT32_MAX);
            assert(memcmp(before,mem,size)==0); invalid++;
        }
    }
    assert(!power_g030_mmio_ok());
    power_g030_mmio_write(0,P_BSRR,1u<<11); /* Best-effort clearing remains possible. */
    assert(!power_g030_mmio_ok());
    assert(*(uint32_t *)(base+24)==(1u<<11));
    assert(munmap(mem,size)==0);
    printf("{\"read_mappings\":%u,\"write_mappings\":%u,\"invalid_access_checks\":%u}\n",reads,writes,invalid);
    return 0;
}
