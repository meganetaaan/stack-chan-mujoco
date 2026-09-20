"""TPS3700-inspired startup hold on dual brake; bounded behavioral development model."""
import argparse,hashlib,json,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
p.add_argument('--case',choices=['normal','no_fault','primary_open','secondary_open','both_open'],default='normal')
p.add_argument('--ready-delay-us',type=float,default=450)
p.add_argument('--converter-delay-ms',type=float,default=0.)
p.add_argument('--uv-corner',choices=['nominal','early','late','max_hysteresis'],default='nominal')
a=p.parse_args()
assert np.isfinite(a.ready_delay_us) and a.ready_delay_us>=0
assert np.isfinite(a.converter_delay_ms) and a.converter_delay_ms>=0
a.out.mkdir(parents=True,exist_ok=False)
# Correlated rising/falling pairs stay within individual threshold and hysteresis bounds.
corners={'nominal':(95300.,10000.,.4,.0055,0.),
         'early':(95300*.99,10000*1.01,.396,.009,-25e-9),
         'late':(95300*1.01,10000*.99,.404,.004,25e-9),
         'max_hysteresis':(95300*1.01,10000*.99,.404,.012,25e-9)}
rt,rb,threshold,hys,bias=corners[a.uv_corner]
rising_bus=threshold*(1+rt/rb)+bias*rt
falling_bus=(threshold-hys)*(1+rt/rb)+bias*rt
source=ROOT/f'validation/dual_brake_development_v1/dual_{a.case}_v2/dual_brake.cir'
plan={'scope':__doc__,'case':a.case,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'supervisor':'TPS3700, one independently powered monitor per branch','source':'https://www.ti.com/lit/ds/symlink/tps3700.pdf',
 'ready_delay_us':a.ready_delay_us,'converter_delay_ms':a.converter_delay_ms,'divider_ohm':[rt,rb], 'threshold_V':threshold,'hysteresis_V':hys,
 'uv_corner':a.uv_corner,'input_bias_A':bias,'bus_release_V':rising_bus,'bus_reassert_V':falling_bus,
 'sink_equivalent_ohm':.25/.003,'supervisor_supply':'vin (battery-side input)','supply_quiescent_A':13e-6,
 'criteria':{'startup_gate_max_V':.4,'startup_window_s':.05,'active_bus_min_V':4.75,'active_bus_max_V':5.25 if a.case=='normal' else 5.8,'sink_current_max_A':.003},
 'limitations':['Selected threshold/divider/input-bias corners only; not all system corners','Gate sink resistance approximates a single VOL bound, not a transistor macro-model',
 'Supervisor held high impedance before fixed ready time; battery is pre-applied, no slow brownout or hot-plug model',
 'Comparator propagation delay not modeled','Underlying brake MOSFET remains ideal 2.5 V switch','Not a complete protection or thermal qualification']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
net=source.read_text(); extra=[]
if a.converter_delay_ms:
 delay=a.converter_delay_ms/1000
 assert 'PWL(0 0 .005 5.15)' in net
 net=net.replace('PWL(0 0 .005 5.15)',f'PWL(0 0 {delay} 0 {delay+.005} 5.15)')
for i in range(2):
 extra += [f'Ruvtop{i} bus uvsense{i} {rt}',f'Ruvbottom{i} uvsense{i} 0 {rb}',f'Iuvbias{i} uvsense{i} 0 {bias}',
 f'Buvlogic{i} uvlogic{i} 0 V=(time < {a.ready_delay_us*1e-6}) ? -1 : ({threshold}-V(uvsense{i}))',
 f'Vuvcurrent{i} gate{i} uvout{i} 0',f'Suvsink{i} uvout{i} 0 uvlogic{i} 0 UVHOLD',f'Iuvq{i} vin 0 13u',f'Cuvdec{i} vin 0 100n']
extra += [f'.model UVHOLD SW(RON=83.3333333333 ROFF=1e9 VT={hys/2} VH={hys/2})']
net=net.replace('.control','\n'.join(extra)+'\n.control')
net=net.replace('v(refbrake1)', 'v(refbrake1) i(Vuvcurrent0) i(Vuvcurrent1)')
import re
net=re.sub(r'tran [^\n]+','tran 1u 0.15 0 1u uic',net)
(a.out/'startup_hold.cir').write_text(net)
r=subprocess.run([str(ROOT/'.tools/root/usr/bin/ngspice'),'-b','startup_hold.cir'],cwd=a.out.resolve(),text=True,capture_output=True)
(a.out/'ngspice.log').write_text(r.stdout+r.stderr);r.check_returncode()
x=np.loadtxt(a.out/'trace.dat',skiprows=1);assert np.isfinite(x).all()
t=x[:,0];bus=x[:,7];assert 'v(bus)' in (a.out/'trace.dat').read_text().splitlines()[0]
# Baseline saved order: time, battery, vin, drive, rect, internal, rail, bus, ib, il, wave, then four values/branch.
active=t>=.05; startup=t<.05;rows=[]
for i in range(2):
 gate=x[:,11+4*i];rows.append({'branch':i,'startup_gate_max_V':float(gate[startup].max()),'gate_max_V':float(gate.max()),'sink_peak_A':float(np.abs(x[:,19+i]).max())})
checks={'sink_current':all(r['sink_peak_A']<=.003 for r in rows),'startup_gate':all(r['startup_gate_max_V']<=.4 for r in rows),
 'active_bus':bool(bus[active].min()>=4.75 and bus[active].max()<=plan['criteria']['active_bus_max_V'])}
report={'branches':rows,'bus_min_V':float(bus[active].min()),'bus_max_V':float(bus[active].max()),'checks':checks,'passed_screen':all(checks.values()),'protection_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
