"""Conditional component-interface and minimum-delay budget for converter enable."""
import argparse,json,math
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'regulator':'Pololu D42V55F5','delay_supervisor_candidate':'TPS3840DL30',
 'sources':['https://www.pololu.com/product/5571','https://www.ti.com/lit/ds/symlink/tps3840.pdf'],
 'supervisor_supply_assumed_V':[3.234,3.366],'supply_status':'3.3 V +/-2 percent always-on supply requirement; LDO not yet selected',
 'VIT_minus_nominal_V':3.,'threshold_error_fraction':.015,'hysteresis_max_V':.125,
 'CT_nominal_F':4.7e-9,'CT_effective_tolerance_fraction':.05,'RCT_min_ohm':350000,
 'minimum_delay_log_argument':.36,'output_low_max_V':.2,'output_low_test_current_A':.002,
 'EN_disable_below_V':.5,'EN_enable_above_V':1.,'EN_pullup_nominal_ohm':1e6,
 'battery_assumed_max_V':8.4,'criteria':{'delay_min_s':.001,'monitor_ready_s':.000450},
 'limitations':['CT effective tolerance must include temperature and bias; part not yet selected',
 'Internal EN pull-up tolerance and EN input leakage not published on product page',
 'Open-drain release pull-up voltage calculation omits unspecified EN input current',
 'Always-on regulator, sequencing wiring, hot plug, brownout and residual charge not simulated',
 'EN is pulled to battery before the 3.3 V supervisor is powered; a default-off circuit is still required to prevent early enable',
 'No claim that this 3 V supervisor protects a 2S battery against overdischarge']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
ctmin=plan['CT_nominal_F']*(1-plan['CT_effective_tolerance_fraction'])
delay=-math.log(.36)*plan['RCT_min_ohm']*ctmin
release=3*1.015+.125
report={'CT_min_F':ctmin,'capacitor_delay_lower_bound_s':delay,
 'ready_margin_s':delay-.000450,'supervisor_max_release_threshold_V':release,
 'supply_min_release_margin_V':3.234-release,'disable_voltage_margin_V':.5-.2,
 'nominal_EN_pullup_current_at_8p4V_A':8.4/1e6,
 'checks':{'minimum_delay':delay>=.001,'ready_margin':delay>.000450,'supervisor_release':3.234>release,'EN_low_level':.2<.5},
 'interpretation':'Conditional interface budget only. Nonnegative startup and uncapped delay terms omitted for a conservative minimum; no upper delay bound asserted.',
 'hardware_sequence_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
