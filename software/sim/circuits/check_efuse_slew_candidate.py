"""Conditional slew envelope; never convert typical delay into a deadline guarantee."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'question':'Does a real 6.8nF candidate permit a useful inrush comparison without inventing total startup time?', 'stop':'One algebraic corner comparison; no load transient sweep', 'acceptance':'Keep startup deadline unassigned unless delay, full capacitance, startup load and fault energy bounds are available', 'assumptions':['3.207..3.393V logic supply is irrelevant to this bus ramp calculation','5.25V upper bus comparison','960uF is historical simulation capacitance, NOT twelve-servo upper limit','Only initial capacitor +/-5% tolerance is applied','Use I/C approximation with datasheet charging current bounds; not a complete switching guarantee']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
cmin,cmax=6800*.95,6800*1.05
srmin,srmax=2e3/cmax,6.33e3/cmin
r={'candidate_base_part':'GRM1885C1H682JA01','initial_capacitance_pF':[cmin,cmax], 'conditional_slew_V_per_ms':[srmin,srmax], 'conditional_0_to_5p25V_ramp_ms':[5.25/srmax,5.25/srmin], 'conditional_capacitive_current_A_at_960uF':[960*srmin/1000,960*srmax/1000], 'capacitive_charge_energy_J_at_960uF_5p25V':.5*960e-6*5.25**2,'startup_deadline_ms':None,'physical_qualification':False, 'missing':['Effective dVdt capacitance including temperature and operating bias','Device delay and PG delay worst-case bounds','Actual total bus capacitance','Actual startup load and upstream current limit','Thermal/energy allowable during ramp and failed startup']}
(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
