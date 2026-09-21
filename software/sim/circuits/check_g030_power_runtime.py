"""Fault injection through the C MMIO/runtime bridge using GPIO callback semantics."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
base=Path('software/firmware/power_sequence')
names=['g030_power_runtime','g030_gpio_init','g030_gpio_outputs','power_runtime','power_deadline','power_sequence']
sources=[base/(x+'.c') for x in names]
test=Path('software/sim/circuits/tests/g030_power_runtime_host.c');exe=a.out/'runtime_host'
flags=['-std=c11','-Wall','-Wextra','-Werror','-pedantic','-O2']
subprocess.run(['cc',*flags,'-I',str(base),*map(str,sources),str(test),'-o',str(exe)],check=True)
counts=json.loads(subprocess.check_output([str(exe.resolve())],text=True))
for source in sources+[base/'g030_gpio_mmio.c']:
 subprocess.run(['clang','--target=arm-none-eabi','-mcpu=cortex-m0plus','-mthumb','-ffreestanding',*flags,'-c',str(source),'-o',str(a.out/(source.stem+'.o'))],check=True)
files=sources+[base/(x+'.h') for x in names]+[base/'g030_gpio_mmio.c',base/'g030_gpio_mmio.h',test,Path(__file__).resolve().relative_to(Path.cwd())]
r={**counts,'arm_object_build_pass':True,'same_call_clear_on_reported_access_fault':True,'fault_memory_survives_healthy_observations':True,'hardware_verified':False,'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},'limits':['Fault injection uses replacement callbacks; not a peripheral/bus electrical failure model.','A fault detected after an enable write can leave a transient enable pulse; independent hardware cutoff remains necessary.','No boot clock/RTC/remap setup, qualified input acquisition, actual timebase or watchdog.','No final linking, flashed image or real pin/timing verification.']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k!='source_sha256'},indent=2))
