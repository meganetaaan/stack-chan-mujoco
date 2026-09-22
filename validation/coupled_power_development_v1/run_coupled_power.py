"""Couple auxiliary sequencing with averaged converter, recorded load and dual brake."""
import argparse,hashlib,json,re,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
p.add_argument('--case',choices=['startup','short_dip','long_dip','slow_ramp'],default='startup')
p.add_argument('--primary-open-regen',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
aux=ROOT/f'validation/aux_sequence_development_v1/aux_sequence_reset_{a.case}_v2/sequence.cir'
kind='primary_open' if a.primary_open_regen else 'normal'
power=ROOT/f'validation/startup_hold_corner_development_v1/startup_hold_late_{kind}_v2/startup_hold.cir'
plan={'scope':__doc__,'case':a.case,'primary_open_regen':a.primary_open_regen,
 'source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [aux,power]},
 'changes':['Auxiliary supply, EN pullup and battery monitor moved to vin after modeled battery resistance',
 'EN gates converter directly; RC 1 ms reference rise replaces time-driven 5 ms reference ramp',
 'Gate-hold TPS3700 monitors powered by AUX3V3; readiness restarts after AUX3V3 falls below 1.8 V',
 'Positive recorded current load rolls off only below 0.5 V to avoid negative bus voltage; regen current remains injected',
 'Controller 3 W model rolls to a resistive load below 0.5 V; not a Tab5 brownout model'],
 'criteria':{'normal_bus_min_V':4.75,'normal_bus_max_V':5.25,'regen_bus_max_V':5.8,'gate_off_max_V':.4,'startup_complete_by_s':.03,'recovery_by_s':.13},
 'limitations':['All inherited behavioral-model limitations apply; not vendor-macromodel validation',
 'Only first 150 ms of recorded load or synthetic regeneration waveform is run',
 'Output may drop during an input outage; this test checks controlled restart, not uninterrupted walking',
 'No real motor brownout/reinitialization, battery protection, fuse, thermal or full energy accounting',
 'Shared AUX3V3 introduces common supply failure, not covered by branch-open test',
 'Converter enable thresholds and soft start remain approximations']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
aux_lines=aux.read_text().split('.control')[0].splitlines()[1:]
battery=aux_lines.pop(0);assert battery.startswith('Vbattery')
aux_block='\n'.join(re.sub(r'\bbattery\b','vin',line) for line in aux_lines)
net=power.read_text();net=re.sub(r'^Vbattery.*$',battery,net,flags=re.M)
net=re.sub(r'^Vref.*$', 'Bcommand command 0 V=(V(en)>1) ? 5.15 : 0\nRsoft command reference 1000\nCsoft reference 0 1u',net,flags=re.M)
net=re.sub(r'^Bconverter.*$', 'Bconverter drive 0 V=(V(en)>1) ? max(0,min(V(reference),V(vin)-.6)) : 0',net,flags=re.M)
net=net.replace('Bload bus 0 I=V(wave)','Bload bus 0 I=(V(wave)>0) ? V(wave)*min(max(V(bus)/.5,0),1) : V(wave)')
net=net.replace('Bcontroller vin 0 I=3/max(V(vin),.5)','Bcontroller vin 0 I=3*max(V(vin),0)/(max(V(vin),.5)^2)')
for i in range(2):
 net=net.replace(f'Iuvq{i} vin 0 13u',f'Buvq{i} aux 0 I=13u*min(max(V(aux)/1.8,0),1)')
 net=net.replace(f'Cuvdec{i} vin 0 100n',f'Cuvdec{i} aux 0 100n')
 net=net.replace(f'Bquiescent{i} bus 0 I=.0008',f'Bquiescent{i} bus 0 I=.0008*min(max(V(bus)/.5,0),1)')
 net=net.replace('(time < 0.00045)', '(V(uvready) < .64)')
ready='''Vuvunit uvunit 0 1
Ruvready uvunit uvready 100k
Cuvready uvready 0 4.4052675n
Buvreset uvreset 0 V=1.8-V(aux)
Suvreset uvready 0 uvreset 0 UVREADY
.model UVREADY SW(RON=10 ROFF=1e12 VT=0 VH=.005)
'''
net=net.replace('.control',aux_block+'\n'+ready+'.control')
net=net.replace('i(Vuvcurrent1)','i(Vuvcurrent1) v(aux) v(en) v(timer) v(uvready)')
(a.out/'coupled.cir').write_text(net)
with (a.out/'ngspice.log').open('w') as log:
 r=subprocess.run([str(ROOT/'.tools/root/usr/bin/ngspice'),'-b','coupled.cir'],cwd=a.out.resolve(),stdout=log,stderr=subprocess.STDOUT,text=True)
(a.out/'run.json').write_text(json.dumps({'returncode':r.returncode},indent=2)+'\n')
r.check_returncode()
x=np.loadtxt(a.out/'trace.dat',skiprows=1);assert np.isfinite(x).all()
t=x[:,0];bus=x[:,7];gate=x[:,[11,15]];auxv=x[:,21];en=x[:,22]
normal=((t>=.05)&(t<.075))|(t>=.13)
if a.case in ['startup','slow_ramp']:normal=t>=.05
startup=t<.03;restart=(t>=.08)&(t<.13)
ceiling=5.8 if a.primary_open_regen else 5.25
checks={'normal_windows':bool(bus[normal].min()>=4.75 and bus[normal].max()<=ceiling),
 'startup_gate':bool(gate[startup].max()<=.4),'startup_complete':bool(bus[(t>=.03)&(t<.04)].min()>=4.75)}
if a.case in ['short_dip','long_dip']:
 checks['restart_gate']=bool(gate[restart].max()<=.4)
report={'case':a.case,'primary_open_regen':a.primary_open_regen,'checks':checks,'passed_screen':all(checks.values()),
 'normal_window_bus_min_V':float(bus[normal].min()),'normal_window_bus_max_V':float(bus[normal].max()),
 'startup_gate_max_V':float(gate[startup].max()),'restart_gate_max_V':float(gate[restart].max()),
 'outage_bus_min_V':float(bus[restart].min()),'aux_min_V_after_50ms':float(auxv[t>=.05].min()),
 'overall_bus_max_V':float(bus.max()),'overall_bus_min_V':float(bus.min()),
 'power_design_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
