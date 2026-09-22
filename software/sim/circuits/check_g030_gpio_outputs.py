"""Check output mapping, preservation and invalid requests in a register model."""
import argparse,ctypes,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
src='software/firmware/power_sequence/g030_gpio_outputs.c';lib=a.out/'outputs.so'
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC',src,'-o',str(lib)],check=True)
R=ctypes.CFUNCTYPE(ctypes.c_uint32,ctypes.c_uint,ctypes.c_uint);W=ctypes.CFUNCTYPE(None,ctypes.c_uint,ctypes.c_uint,ctypes.c_uint32)
f=ctypes.CDLL(str(lib.resolve())).power_g030_apply_outputs;f.argtypes=[ctypes.c_uint8,R,W];f.restype=ctypes.c_int
bits=(8,11,12);control=sum(1<<b for b in bits);count=0
for request in range(256):
 for initial in range(8):
  latch=[0xa55a&~control|sum(((initial>>n)&1)<<b for n,b in enumerate(bits))];old=latch[0];trace=[]
  def write(port,reg,value):
   assert port==0 and reg==24
   trace.append(value);latch[0]=(latch[0]|(value&65535))&~(value>>16)
  rc=f(request,R(lambda p,r:latch[0]),W(write))
  valid=request<16 and not(request&1 and request&2) and not(request&4 and not request&2)
  expected=sum(((request>>n)&1)<<b for n,b in enumerate(bits)) if valid else 1<<11
  assert bool(rc)==valid and latch[0]&control==expected
  assert latch[0]&~control==old&~control
  assert len(trace)==1 and (trace[0]&65535)&(trace[0]>>16)==0
  count+=1
# Simulate a first write not taking effect; fallback must request clear.
latch=[1<<8];trace=[]
def fail_first(p,r,v):
 trace.append(v)
 if len(trace)>1:latch[0]=(latch[0]|(v&65535))&~(v>>16)
assert f(2,R(lambda p,r:latch[0]),W(fail_first))==0
assert len(trace)==2 and latch[0]&control==1<<11
subprocess.run(['clang','--target=arm-none-eabi','-mcpu=cortex-m0plus','-mthumb','-ffreestanding','-std=c11','-Wall','-Wextra','-Werror','-Oz','-c',src,'-o',str(a.out/'outputs_arm.o')],check=True)
r={'request_initial_latch_combinations':count,'invalid_requests_force_clear':True,'other_pins_preserved':True,'single_BSRR_update':True,
 'failed_write_returns_failure_and_attempts_clear':True,'host_arm_compile_pass':True,
 'hardware_verified':False,'limits':['ODR is an output latch, not a physical pin observation','One BSRR write does not guarantee zero pin skew','Repeated write failure requires independent hardware cutoff','Caller must remember failures; no automatic retry to enable','Complete MCU boot, timing and electrical integration remain unverified']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(count)
