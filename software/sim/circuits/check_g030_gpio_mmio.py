"""Compile actual STM32G030 adapter and test its literal addresses on a Linux host."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
root=Path('software/firmware/power_sequence')
src=root/'g030_gpio_mmio.c';test=Path('software/sim/circuits/tests/g030_gpio_mmio_host.c')
flags=['-std=c11','-Wall','-Wextra','-Werror','-pedantic','-O2']
exe=a.out/'host_mmio'
subprocess.run(['cc',*flags,'-I',str(root),str(src),str(test),'-o',str(exe)],check=True)
run=subprocess.run([str(exe.resolve())],text=True,capture_output=True)
if run.returncode: raise RuntimeError(f'Host mapping test did not pass: {run.returncode}: {run.stderr}')
counts=json.loads(run.stdout)
subprocess.run(['clang','--target=arm-none-eabi','-mcpu=cortex-m0plus','-mthumb','-ffreestanding',*flags,'-c',str(src),'-o',str(a.out/'mmio_arm.o')],check=True)
files=[src,root/'g030_gpio_mmio.h',root/'g030_gpio_init.h',test,Path(__file__).resolve().relative_to(Path.cwd())]
r={**counts,'cortex_m0plus_compile_pass':True,'invalid_access_fault_is_sticky':True,
   'source_sha256':{str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in files},
   'hardware_verified':False,'limits':['Host anonymous RAM tests address selection and write isolation, not GPIO side effects or timing.','Clock, reset, RTC/remap ownership, startup/linking and watchdog not implemented by this adapter.','Caller must check sticky access fault and keep independent hardware inhibition.','Inputs still require qualified receiver circuits; IDR is raw.']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
