"""Counter and runtime integration checks; tick values are not selected real deadlines."""
import argparse,ctypes,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
base=Path('software/firmware/power_sequence');sources=[base/x for x in ('power_deadline.c','power_runtime.c','power_sequence.c','g030_gpio_outputs.c')]
lib=a.out/'deadline.so';subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC',*map(str,sources),'-o',str(lib)],check=True)
class Timer(ctypes.Structure):_fields_=[('limit',ctypes.c_uint32),('start',ctypes.c_uint32),('last',ctypes.c_uint32),('active',ctypes.c_uint8),('expired',ctypes.c_uint8)]
class Ctx(ctypes.Structure):_fields_=[('state',ctypes.c_uint8),('fault',ctypes.c_uint8)]
d=ctypes.CDLL(str(lib.resolve()));init=d.power_deadline_init;init.argtypes=[ctypes.POINTER(Timer),ctypes.c_uint32]
u=d.power_deadline_update;u.argtypes=[ctypes.POINTER(Timer),ctypes.c_int,ctypes.c_uint32];u.restype=ctypes.c_int
for limit in (0,0x80000000,0xffffffff):
 t=Timer();init(ctypes.byref(t),limit)
 assert u(ctypes.byref(t),0,1)==u(ctypes.byref(t),1,2)==1
for origin in (0,100,0xfffffff9):
 t=Timer();init(ctypes.byref(t),10)
 assert [u(ctypes.byref(t),1,(origin+n)&0xffffffff) for n in (0,9,10,11)]==[0,0,1,1]
 assert u(ctypes.byref(t),1,origin)==1
 assert u(ctypes.byref(t),0,origin)==0 and u(ctypes.byref(t),1,origin)==0
# A backward tick before timeout also expires.
t=Timer();init(ctypes.byref(t),100)
assert [u(ctypes.byref(t),1,n) for n in (10,20,19)]==[0,0,1]
R=ctypes.CFUNCTYPE(ctypes.c_uint32,ctypes.c_uint,ctypes.c_uint);W=ctypes.CFUNCTYPE(None,ctypes.c_uint,ctypes.c_uint,ctypes.c_uint32)
f=d.power_runtime_timed_step;f.argtypes=[ctypes.POINTER(Ctx),ctypes.POINTER(Timer),ctypes.c_uint32,ctypes.c_uint16,R,W];f.restype=ctypes.c_uint8
ctx=Ctx(4,0);t=Timer();init(ctypes.byref(t),10);latch=[0]
def write(p,r,v):latch[0]=(latch[0]|(v&65535))&~(v>>16)
trace=[]
for now,pg in ((100,0),(109,0),(110,24)):
 out=f(ctypes.byref(ctx),ctypes.byref(t),now,7|32|64|pg,R(lambda p,r:latch[0]),W(write))
 trace.append(dict(tick=now,output=out,state=ctx.state))
assert trace[0]['output']&1 and trace[1]['output']&1
assert not trace[2]['output']&1 and ctx.state==0  # Timeout wins simultaneous PG.
# Invalid timer configuration must inhibit every phase and remain latched even
# if the caller repairs the timer object without a new boot.
invalid_cases=[]
for phase in range(6):
 for limit in (None,0,0x80000000,0xffffffff):
  ctx=Ctx(phase,0);t=Timer();init(ctypes.byref(t),limit or 0)
  ptr=None if limit is None else ctypes.byref(t)
  out=f(ctypes.byref(ctx),ptr,200,127,R(lambda p,r:latch[0]),W(write))
  assert out==2 and ctx.state==0 and ctx.fault==1, (phase,limit,out,ctx.state,ctx.fault)
  init(ctypes.byref(t),10)
  out=f(ctypes.byref(ctx),ctypes.byref(t),201,127,R(lambda p,r:latch[0]),W(write))
  assert out==2 and ctx.fault==1
  invalid_cases.append(dict(phase=phase,limit=limit,clear_and_sticky=True))
subprocess.run(['clang','--target=arm-none-eabi','-mcpu=cortex-m0plus','-mthumb','-ffreestanding','-std=c11','-Wall','-Wextra','-Werror','-Oz','-c',str(sources[0]),'-o',str(a.out/'deadline_arm.o')],check=True)
(a.out/'report.json').write_text(json.dumps({'invalid_timer_runtime_cases':invalid_cases,'invalid_limits_rejected':True,'wraparound_and_backward_tick_checked':True,'expiry_sticky_until_run_reset':True,'timeout_wins_pg_trace':trace,'host_arm_compile_pass':True,'real_limit_selected':False,'hardware_timebase_verified':False,'limits':['Less than 2^31 ticks between updates','Clock stall not detectable from this clock alone','Real clock frequency/tolerance and safe startup deadline unselected']},indent=2)+'\n');print('Deadline and runtime checks passed')
