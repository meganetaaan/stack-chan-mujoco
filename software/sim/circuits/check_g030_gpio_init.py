"""Exercise C register sequencing with an emulated GPIO bank, not real hardware."""
import argparse,ctypes,json,random,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
src='software/firmware/power_sequence/g030_gpio_init.c';lib=a.out/'gpio.so'
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-pedantic','-shared','-fPIC',src,'-o',str(lib)],check=True)
rtype=ctypes.CFUNCTYPE(ctypes.c_uint32,ctypes.c_uint,ctypes.c_uint)
wtype=ctypes.CFUNCTYPE(None,ctypes.c_uint,ctypes.c_uint,ctypes.c_uint32)
f=ctypes.CDLL(str(lib.resolve())).power_g030_gpio_init;f.argtypes=[rtype,wtype];f.restype=ctypes.c_int
contract=json.loads(Path('validation/g030_bonded_pins_v1/report.json').read_text())['gpio_mode_contract']
rng=random.Random(0);traces=[]
for case in range(101):
 regs={(port,reg):rng.getrandbits(32) for port in range(3) for reg in (0,4,8,12,20,24,32,36)}
 before=dict(regs);trace=[]
 blocked=case==100
 def read(port,reg):return regs[port,reg]
 def write(port,reg,value):
  trace.append([port,reg,value])
  if blocked and port==1 and reg==0:return
  regs[port,reg]=value
  if reg==24:regs[port,20]=(regs[port,20]|(value&65535))&~(value>>16)
 rc=f(rtype(read),wtype(write))
 if blocked:
  assert rc==0 and len(trace)==3  # No output activation after alias disable fails.
  continue
 assert rc==1
 for name,mode in contract.items():
  port=ord(name[1])-ord('A');bit=int(name[2:]);mask=3<<(2*bit)
  if mode=='debug':
   assert (regs[port,0]&mask)==(before[port,0]&mask)
   assert (regs[port,12]&mask)==(before[port,12]&mask)
  else:
   assert (regs[port,0]>>(2*bit))&3=={'input':0,'output':1,'analog':3}[mode]
   assert regs[port,12]&mask==0
 # First three writes release all drivers; safe latch data is fourth.
 assert [(x[0],x[1]) for x in trace[:4]]==[(0,0),(1,0),(2,0),(0,24)]
 assert trace[3][2]==(1<<11)|((1<<8|1<<12)<<16)
 if case==0:traces=trace
subprocess.run(['clang','--target=arm-none-eabi','-mcpu=cortex-m0plus','-mthumb','-ffreestanding','-std=c11','-Wall','-Wextra','-Werror','-Oz','-c',src,'-o',str(a.out/'gpio_arm.o')],check=True)
r={'initial_register_patterns':100,'blocked_alias_disable_rejected':True,'host_and_arm_compile':True,'first_trace':traces,
 'scope':'Register callback model only; GPIO clocks, locking, power, backup domain and MMIO adapter not verified','hardware_verified':False}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print('100 patterns and blocked-write case passed')
