"""Evaluate the complete recorded twelve-axis load with internal-step voltage measurements."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
p.add_argument('--side',choices=['left','right'],default='left');p.add_argument('--battery-v',type=float,default=7.4)
a=p.parse_args();assert np.isfinite(a.battery_v) and 6<=a.battery_v<=8.4;a.out.mkdir(parents=True,exist_ok=False)
source=ROOT/f'validation/prototype_epic4_v1/load_export_{a.side}_v1/loads.npz'
base=ROOT/'validation/coupled_power_ldo_development_v1/coupled_power_startup_continuous_v2/coupled.cir'
with np.load(source) as load: t=load['time_s'];current=load['net_A']
assert len(t)==len(current) and len(t)>1 and np.all(np.diff(t)>0) and np.isfinite(current).all()
stop=float(t[-1]+.06)
plan={'scope':__doc__,'side':a.side,'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [source,base]},
 'load_samples':len(t),'load_time_s':[float(t[0]),float(t[-1])],'load_start_s':.05,'stop_s':stop,'battery_V':a.battery_v,
 'solver_max_step_s':1e-6,'display_interval_s':1e-4,'measurement_method':'ngspice meas on original internal-step vectors before linearize',
 'criteria':{'operating_bus_min_V':4.75,'operating_bus_max_V':5.25,'startup_gate_max_V':.4},
 'limitations':['All continuous-LDO coupled model assumptions retained','Prescribed current does not respond to motor voltage except rolloff below 0.5 V',
 'No new mechanical mass or load regeneration incorporated','No component/thermal/protection qualification','Uniform display trace is not used to certify extrema','Battery energy is measured but complete energy balance not checked']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
net=base.read_text().split('.control')[0]
net=re.sub(r'^Vbattery.*$',f'Vbattery battery 0 PWL(0 0 .0002 {a.battery_v})',net,flags=re.M)
points=[(0.,0.),(.05,0.)]+[(float(x+.05),float(y)) for x,y in zip(t,current)]
wave='Vwave wave 0 PWL(\n'+'\n'.join('+ %.12g %.12g'%point for point in points)+'\n+ )'
net,n=re.subn(r'Vwave wave 0 PWL\(.*?^\+ \)',wave,net,flags=re.M|re.S);assert n==1
vectors='v(bus) v(gate0) v(gate1) v(aux) v(en) v(wave) v(battery) i(Vbattery)'
net+=f'''.save {vectors}
.control
set wr_singlescale
set wr_vecnames
tran 100u {stop:.12g} 0 1u uic
meas tran operating_min MIN v(bus) FROM=.05 TO={stop:.12g}
meas tran operating_max MAX v(bus) FROM=.05 TO={stop:.12g}
meas tran gate0_start_max MAX v(gate0) FROM=0 TO=.03
meas tran gate1_start_max MAX v(gate1) FROM=0 TO=.03
meas tran load_max MAX v(wave) FROM=.05 TO={stop:.12g}
let battery_power = -v(battery)*i(Vbattery)
meas tran battery_energy INTEG battery_power FROM=0 TO={stop:.12g}
linearize {vectors}
wrdata display_trace.dat {vectors}
quit
.endc
.end
'''
(a.out/'full_trace.cir').write_text(net)
with (a.out/'ngspice.log').open('w') as log:
 r=subprocess.run([str(ROOT/'.tools/root/usr/bin/ngspice'),'-b','full_trace.cir'],cwd=a.out.resolve(),stdout=log,stderr=subprocess.STDOUT)
(a.out/'run.json').write_text(json.dumps({'returncode':r.returncode},indent=2)+'\n');r.check_returncode()
log=(a.out/'ngspice.log').read_text();measures={}
for key in ['operating_min','operating_max','gate0_start_max','gate1_start_max','load_max','battery_energy']:
 found=re.search(r'^'+key+r'\s*=\s*([-+0-9.eE]+)',log,re.M);assert found,(key,'measurement missing')
 measures[key]=float(found.group(1));assert np.isfinite(measures[key])
checks={'operating_voltage':4.75<=measures['operating_min']<=measures['operating_max']<=5.25,
 'startup_gate':max(measures['gate0_start_max'],measures['gate1_start_max'])<=.4,
 'complete_load_peak':abs(measures['load_max']-float(current.max()))<1e-6}
display=np.loadtxt(a.out/'display_trace.dat',skiprows=1);assert np.isfinite(display).all()
assert abs(display[-1,0]-stop)<1.1e-4
report={'measurements':measures,'checks':checks,'passed_screen':all(checks.values()),'display_samples':len(display),'full_power_design_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
