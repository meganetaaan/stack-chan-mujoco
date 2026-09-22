"""Check real C integration with register callbacks and delayed observations."""
import argparse,ctypes,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
base=Path('software/firmware/power_sequence');sources=[base/x for x in ('power_runtime.c','power_sequence.c','g030_gpio_outputs.c')]
lib=a.out/'runtime.so';subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC',*map(str,sources),'-o',str(lib)],check=True)
class Ctx(ctypes.Structure):_fields_=[('state',ctypes.c_uint8),('io_fault',ctypes.c_uint8)]
R=ctypes.CFUNCTYPE(ctypes.c_uint32,ctypes.c_uint,ctypes.c_uint);W=ctypes.CFUNCTYPE(None,ctypes.c_uint,ctypes.c_uint,ctypes.c_uint32)
dll=ctypes.CDLL(str(lib.resolve()));dll.power_runtime_boot.argtypes=[ctypes.POINTER(Ctx),ctypes.c_int]
f=dll.power_runtime_step;f.argtypes=[ctypes.POINTER(Ctx),ctypes.c_uint16,R,W];f.restype=ctypes.c_uint8
ctx=Ctx();dll.power_runtime_boot(ctypes.byref(ctx),1);latch=[0];fail=[False];trace=[]
def write(p,r,v):
 if fail[0]:fail[0]=False;latch[0]=0;return
 latch[0]=(latch[0]|(v&65535))&~(v>>16)
def step(label,mask):
 request=f(ctypes.byref(ctx),mask,R(lambda p,r:latch[0]),W(write))
 trace.append(dict(event=label,inputs=mask,request=request,state=ctx.state,io_fault=ctx.io_fault,latch=latch[0]));return request
H=7;CLR=128;DONE=256;PERM=64;ARMED=32;PG=24
step('hold_low',H|CLR);step('hold_done',H|CLR|DONE)
assert ctx.state==2
step('clear_still_low',H|CLR)
assert ctx.state==2  # Must not qualify permission Low while physical reset is asserted.
step('released_and_permission_low',H);assert ctx.state==3
step('new_permission',H|PERM|ARMED);assert ctx.state==4
step('both_pg',H|PERM|ARMED|PG);assert ctx.state==5
fail[0]=True
step('write_failure',H|PERM|ARMED|PG)
assert ctx.io_fault and ctx.state==0
for n in range(5):
 assert step('healthy_after_failure',H|PERM|ARMED|PG)==2
 assert ctx.io_fault and not latch[0]&(1<<8)
bad=Ctx();dll.power_runtime_boot(ctypes.byref(bad),0)
assert f(ctypes.byref(bad),H|PERM|ARMED|PG,R(lambda p,r:latch[0]),W(write))==2 and bad.io_fault
for source in sources:
 subprocess.run(['clang','--target=arm-none-eabi','-mcpu=cortex-m0plus','-mthumb','-ffreestanding','-std=c11','-Wall','-Wextra','-Werror','-Oz','-c',str(source),'-o',str(a.out/(source.stem+'.o'))],check=True)
(a.out/'report.json').write_text(json.dumps({'trace':trace,'sticky_failure_verified_in_callback_model':True,'failed_initialization_inhibits':True,'delayed_reset_release_waits':True,'host_and_arm_compile':True,'hardware_verified':False},indent=2)+'\n');print('Runtime integration scenarios passed')
