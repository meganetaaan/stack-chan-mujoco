"""Coupled auxiliary-rail, reset-timer and default-off EN behavioral development model."""
import argparse,json,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
p.add_argument('--case',choices=['startup','short_dip','long_dip','slow_ramp'],default='startup')
p.add_argument('--battery-reset',action='store_true')
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
wave={'startup':'0 0 .0002 8.4 .15 8.4','slow_ramp':'0 0 .01 8.4 .15 8.4',
 'short_dip':'0 0 .0002 8.4 .08 8.4 .0801 0 .0802 0 .0803 8.4 .15 8.4',
 'long_dip':'0 0 .0002 8.4 .08 8.4 .0801 0 .10 0 .1002 8.4 .15 8.4'}[a.case]
plan={'scope':__doc__,'case':a.case,'battery_reset':a.battery_reset,'battery_reset_threshold_nominal_V':6.,'battery_monitor_RC_lag_s':50e-6,'battery_PWL':wave,'ldo_candidate':'TPS70933DBVR, EN floating (do not tie to 8.4 V)',
 'supervisor_candidate':'TPS3840PL30','diode_candidate':'BAS116','aux_target_V':3.234,'aux_C_F':4.7e-6,'aux_load_ohm':10000,
 'ldo_output_resistance_ohm':10,'ldo_current_limit_A':.15,'ldo_dropout_assumed_V':.5,
 'reset_rising_V':3.17,'reset_falling_V':3.045,'timer_R_ohm':350000,'timer_C_F':4.465e-9,'timer_release_normalized':.64,
 'EN_pulldown_ohm':22220,'EN_pullup_assumed_ohm':800000,'EN_capacitance_F':1e-9,'drive_series_ohm':1000,
 'criteria':{'initial_EN_stays_off_until_s':.001,'off_EN_max_V':.5,'on_EN_min_V':1.,'recovery_by_s':.13,'restart_hold_s':.00045},
 'sources':['https://www.ti.com/lit/ds/symlink/tps709.pdf','https://www.ti.com/lit/ds/symlink/tps3840.pdf','https://www.pololu.com/product/5571'],
 'limitations':['LDO behavioral current source is not a vendor macro-model; startup, dropout and output resistance are assumptions',
 'Timer is normalized RC with fast ideal reset; real reset-discharge and propagation delays not modeled',
 'Optional battery reset uses nominal TPS3700 thresholds and assumed 50 us RC lag, not a guaranteed propagation limit; manual-reset release logic simplified',
 'Supervisor drive uses 80 percent rail and ideal output impedance; below-POR behavior conservatively follows rail',
 'No DC/DC power stage, motor load or regenerative energy in this EN interface test',
 'Input leakage, diode parameters and EN pull-up remain assumptions from prior interface study']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
net=f'''Auxiliary supply and reset sequence development
Vbattery battery 0 PWL({wave})
Bldo battery aux I=(V(battery)>2.7) ? min(.15,max(0,(min(3.234,V(battery)-.5)-V(aux))/10)) : 0
Caux aux 0 4.7u
Rauxload aux 0 10k
Buv uv 0 V=3.1075-V(aux)
Sreset timer 0 uv 0 RESET
.model RESET SW(RON=10 ROFF=1e12 VT=0 VH=.0625)
Vnormalized normalized 0 1
Rtimer normalized timer 350k
Ctimer timer 0 4.465n
Bdriver driver 0 V=(V(timer)>.64) ? .8*V(aux) : min(.2,V(aux))
Bdriverload aux 0 I=max(0,-I(Bdriver)*V(driver))/max(V(aux),.1)
Rdrive driver diode_anode 1000
Bdiode diode_anode en I=max((V(diode_anode)-V(en)-.9)/10,0)-80n*max(0,min((V(en)-V(diode_anode))*100,1))
Cdiode diode_anode en 2p
Rinternal battery en 800k
Roff en 0 22220
Cen en 0 1n
Iinput 0 en 1u
.control
set wr_singlescale
set wr_vecnames
tran 1u .15 0 1u uic
wrdata trace.dat v(battery) v(aux) v(timer) v(driver) v(en) i(Bdriver)
quit
.endc
.end
'''
if a.battery_reset:
 extra='''Rbatmon_top battery batmon 140k
Rbatmon_bottom batmon 0 10k
Bbaterror baterror 0 V=.4-V(batmon)
Rbatlag baterror batfilter 10k
Cbatlag batfilter 0 5n
Rmr aux mr 100k
Smrsink mr 0 batfilter 0 BATMON
.model BATMON SW(RON=83.333333 ROFF=1e9 VT=.00275 VH=.00275)
Bmrerror mrerror 0 V=.6-V(mr)
Sctmanual timer 0 mrerror 0 MANUAL
.model MANUAL SW(RON=10 ROFF=1e12 VT=0 VH=.001)
Bbatq aux 0 I=13u*min(max(V(aux)/1.8,0),1)
'''
 net=net.replace('.control',extra+'.control')
(a.out/'sequence.cir').write_text(net)
r=subprocess.run([str(ROOT/'.tools/root/usr/bin/ngspice'),'-b','sequence.cir'],cwd=a.out.resolve(),text=True,capture_output=True)
(a.out/'ngspice.log').write_text(r.stdout+r.stderr);r.check_returncode()
x=np.loadtxt(a.out/'trace.dat',skiprows=1);assert np.isfinite(x).all();t,battery,aux,timer,driver,en,current=x.T
on=t[en>1]; release=float(on[0]) if len(on) else None
checks={'no_early_enable':bool(en[t<.001].max()<.5),'initial_enable':bool(release is not None and release<.03),'recovered_enable':bool(en[t>=.13].min()>1)}
if a.case in ['short_dip','long_dip']:
 restart=.0803 if a.case=='short_dip' else .1002
 checks['restart_hold']=bool(en[(t>=restart)&(t<restart+.00045)].max()<.5)
report={'case':a.case,'checks':checks,'passed_screen':all(checks.values()),'first_enable_s':release,
 'initial_EN_peak_before_1ms_V':float(en[t<.001].max()),'aux_min_during_80_to_100ms_V':float(aux[(t>=.08)&(t<=.10)].min()),
 'EN_min_during_80_to_100ms_V':float(en[(t>=.08)&(t<=.10)].min()),'driver_current_peak_A':float(np.abs(current).max()),
 'full_power_sequence_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
