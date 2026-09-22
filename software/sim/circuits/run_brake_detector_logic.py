"""Check a behavioral current detector's persistence and sticky fault output in ngspice."""
import json,re,subprocess
from pathlib import Path
p=Path('validation/brake_detector_logic_v1');plan=json.loads((p/'plan.json').read_text());s=plan['sensor']
net=f'''Behavioral brake detector timing contract
Vs aux 0 {s['supply_V']}
Vcurrent current 0 PWL(0 0 .02 0 .020001 1.1 .04 1.1 .040001 0 .05 0 .050001 1.1 .0505 1.1 .050501 0 .07 0 .070001 1.1 .09 1.1 .090001 0 .1 0)
Vgate gate 0 PWL(0 0 .019 0 .019001 3 .041 3 .041001 0 .1 0)
Bsensor sensor 0 V=min(max({s['gain']}*(V(current)*{s['shunt_ohm']}+({s['input_offset_V']})),.005),V(aux)-.03)
Rfilter sensor filtered 1000
Cfilter filtered 0 {s['filter_tau_s']/1000}
Bcondition condition 0 V=(V(filtered)>{plan['threshold_V']} && V(gate)<{plan['gate_off_max_V']}) ? 1 : 0
Btimer 0 timer I=(V(condition)>.5 && V(timer)<1.1) ? .001 : 0
Ctimer timer 0 1u IC=0
Breset reset 0 V=1-V(condition)
Sreset timer 0 reset 0 RESET
.model RESET SW(RON=1 ROFF=1e12 VT=.5 VH=.01)
Blatch 0 latch I=(V(timer)>1) ? max(1-V(latch),0)/1000 : 0
Clatch latch 0 1n IC=0
Rhold latch 0 1e12
.control
set wr_singlescale
set wr_vecnames
tran 1u .1 0 1u uic
meas tran pre_fault_latch MAX v(latch) FROM=0 TO=.0699
meas tran latch_peak MAX v(latch) FROM=0 TO=.1
meas tran detected FIND v(latch) AT=.072
meas tran retained MIN v(latch) FROM=.092 TO=.1
wrdata trace.dat v(current) v(gate) v(filtered) v(timer) v(latch)
quit
.endc
.end
'''
(p/'detector.cir').write_text(net)
with (p/'ngspice.log').open('w') as log:r=subprocess.run([str(Path('.tools/root/usr/bin/ngspice').resolve()),'-b','detector.cir'],cwd=p,stdout=log,stderr=subprocess.STDOUT)
(p/'run.json').write_text(json.dumps({'returncode':r.returncode})+'\n');r.check_returncode();log=(p/'ngspice.log').read_text();m={}
for key in ['pre_fault_latch','detected','retained','latch_peak']:
 match=re.search(r'^'+key+r'\s*=\s*([-+0-9.eE]+)',log,re.M);assert match,key;m[key]=float(match.group(1))
c=plan['criteria'];checks={'latch_amplitude':m['latch_peak']<=c['latch_max_V'],'no_premature_latch':m['pre_fault_latch']<=c['pre_fault_latch_max_V'],'persistent_fault_detected':m['detected']>=c['latch_at_72ms_min_V'],'latch_retained':m['retained']>=c['latch_after_fault_clears_min_V']}
result={'measurements':m,'checks':checks,'hardware_protection_verified':False};(p/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
