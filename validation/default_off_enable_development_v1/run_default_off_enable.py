"""Default-off EN pull-down and diode-isolated push-pull control development screen."""
import argparse,json,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--cap-pf',type=float,default=1000)
p.add_argument('--pulldown-kohm',type=float,default=33.)
p.add_argument('--series-ohm',type=float,default=0.)
a=p.parse_args();assert np.isfinite(a.cap_pf) and a.cap_pf>0;assert np.isfinite(a.pulldown_kohm) and a.pulldown_kohm>0
assert np.isfinite(a.series_ohm) and a.series_ohm>=0
a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'candidate_supervisor':'TPS3840PL30 (push-pull, changes earlier DL candidate)',
 'candidate_diode':'BAS116, anode at supervisor output, cathode at EN',
 'battery_max_V':8.4,'EN_internal_pullup_ohm':800000,'internal_pullup_status':'20 percent below nominal 1 Mohm is a sensitivity assumption, not manufacturer tolerance',
 'external_pulldown_ohm':a.pulldown_kohm*1000*1.01,'drive_series_ohm':a.series_ohm,'EN_source_leakage_A':1e-6,'EN_leakage_status':'assumed injection bound; regulator specification pending',
 'control_high_V':.8*3.234,'control_low_V':.2,'diode_forward_drop_V':.9,'diode_series_ohm':10,
 'diode_reverse_leakage_A':80e-9,'EN_capacitance_F':a.cap_pf*1e-12,'diode_capacitance_F':2e-12,
 'events_s':{'release':.003,'supply_loss':.008,'control_falls':.008030,'restart_release':.012},
 'criteria':{'off_max_V':.5,'on_min_V':1.,'disable_deadline_s':100e-6,'control_current_max_A':.002},
 'sources':['https://www.pololu.com/product/5571','https://www.ti.com/lit/ds/symlink/tps3840.pdf','https://assets.nexperia.com/documents/data-sheet/BAS116.pdf'],
 'limitations':['Behavioral sources replace actual supervisor and LDO startup/reset state machine','Diode is a bounded-drop/leakage approximation, not a vendor macro-model',
 '0.9 V diode drop derives from 25 C pulsed 1 mA spec; not a full-temperature guarantee',
 '30 us control-fall delay assumes specified supervisor overdrive; slow brownouts unverified','No converter switching or load/energy model in this EN-only test','Capacitance and EN leakage require part/board constraints']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
net=f'''Default-off converter enable interface
Vbattery battery 0 8.4
Rinternal battery en 800k
Roff en 0 {plan['external_pulldown_ohm']}
Iinput 0 en 1u
Cen en 0 {plan['EN_capacitance_F']}
Vcontrol control 0 PWL(0 .2 .003 .2 .003001 {plan['control_high_V']} .008030 {plan['control_high_V']} .008031 0 .012 0 .012001 {plan['control_high_V']})
Bdiode control en I=max((V(control)-V(en)-.9)/10,0)-80n*max(0,min((V(en)-V(control))*100,1))
Cdiode control en 2p
.control
set wr_singlescale
set wr_vecnames
tran 100n 15m 0 100n
wrdata trace.dat v(en) v(control) i(Vcontrol)
quit
.endc
.end
'''
if a.series_ohm:
 net=net.replace('Vcontrol control 0 PWL','Vcontrol driver 0 PWL').replace('Bdiode control en',f'Rdrive driver control {a.series_ohm}\nBdiode control en')
(a.out/'enable.cir').write_text(net)
r=subprocess.run([str(ROOT/'.tools/root/usr/bin/ngspice'),'-b','enable.cir'],cwd=a.out.resolve(),capture_output=True,text=True)
(a.out/'ngspice.log').write_text(r.stdout+r.stderr);r.check_returncode()
x=np.loadtxt(a.out/'trace.dat',skiprows=1);assert np.isfinite(x).all();t,en,control,current=x.T
pre=t<.003;off=(t>=.0081)&(t<.012);on=((t>.0031)&(t<.008))|(t>.0121)
first_off=t[(t>.00803)&(t<.012)&(en<.5)]
metrics={'startup_EN_max_V':float(en[pre].max()),'loss_EN_after_deadline_max_V':float(en[off].max()),
 'enabled_EN_min_V':float(en[on].min()),'control_current_peak_A':float(np.abs(current).max()),
 'loss_to_disable_s':float(first_off[0]-.008) if len(first_off) else None}
checks={'startup_off':metrics['startup_EN_max_V']<.5,'loss_off':metrics['loss_EN_after_deadline_max_V']<.5,
 'enabled':metrics['enabled_EN_min_V']>1,'control_current':metrics['control_current_peak_A']<.002}
report={'metrics':metrics,'checks':checks,'passed_screen':all(checks.values()),'hardware_sequence_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
