"""Compare compiled portable C with the sampled reference; no GPIO timing claim."""
import argparse,ctypes,hashlib,json,subprocess
from pathlib import Path
from power_sequence_model import Inputs,State,outputs,advance
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
source=Path('software/firmware/power_sequence/power_sequence.c')
lib=a.out/'power_sequence.so'
subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-pedantic','-O2','-fPIC','-shared',str(source),'-o',str(lib)],check=True)
dll=ctypes.CDLL(str(lib.resolve()))
for f in (dll.power_sequence_outputs,dll.power_sequence_next):f.argtypes=[ctypes.c_uint8,ctypes.c_uint16];f.restype=ctypes.c_uint8
states=[State(),State('CLEAR','QUALIFY'),State('WAIT_NEW_PRESS'),State('WAIT_NEW_PRESS',permission_low_seen=True),State('START'),State('RUN')]
count=0
for idx,s in enumerate(states):
 for mask in range(1024):
  i=Inputs(*(bool(mask&(1<<bit)) for bit in range(10)))
  o=outputs(s,i);expected=sum(int(getattr(o,key))<<bit for bit,key in enumerate(['enable_request','clear_request','reset_low_valid','startup_timer_run']))
  assert dll.power_sequence_outputs(idx,mask)==expected,(idx,mask,'output')
  assert dll.power_sequence_next(idx,mask)==states.index(advance(s,i)),(idx,mask,'next')
  count+=1
invalid=0
for s in range(6,256):
 for mask in (0,1023):
  assert dll.power_sequence_outputs(s,mask)==2 and dll.power_sequence_next(s,mask)==0
  invalid+=1
for s in range(6):
 for bit in range(10,16):
  assert dll.power_sequence_outputs(s,1<<bit)==2 and dll.power_sequence_next(s,1<<bit)==0
  invalid+=1
arm=a.out/'power_sequence_arm.o'
subprocess.run(['clang','--target=arm-none-eabi','-mcpu=cortex-m0plus','-mthumb','-ffreestanding','-std=c11','-Wall','-Wextra','-Werror','-Oz','-c',str(source),'-o',str(arm)],check=True)
report={'model_comparisons':count,'invalid_encoding_checks':invalid,'host_compile_pass':True,'cortex_m0plus_compile_pass':True,
 'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (source,source.with_suffix('.h'))},
 'compiler_versions':{tool:subprocess.check_output([tool,'--version'],text=True).splitlines()[0] for tool in ('cc','clang')},
 'hardware_verified':False,'remaining':['Startup/linker and board initialization','Qualified GPIO observations','Real clock/timer and watchdog','Asynchronous fault capture','Output ordering and reset recovery','Integrated electrical verification']}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
