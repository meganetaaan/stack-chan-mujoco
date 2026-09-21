"""Compare existing/new feed at predeclared static sensitivity conditions."""
import argparse,hashlib,itertools,json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
paths=['schematics/power/stop_feed_candidate.json','validation/aux_start_isolator_v1/report.json']
c,b=[json.loads((root/x).read_text()) for x in paths];load=b['updated_STOP_DC_comparison_A']
# At 4.8V input TPS709's load-regulation test has the required 1.5V headroom.
# This is a screening reference, not a minimum-input specification.
vref=4.8;rbleed=99000;rows=[]
for label,R in [('old1kohm',1000),('parallel1_5kohm',750),('one_open',1500)]:
 for vb,vd,ig in itertools.product([9.,12.6],[1.,1.25],[0.,350e-6]):
  r=R*1.01
  vin=(vb-vd-r*(load+ig))/(1+r/rbleed)
  rows.append(dict(network=label,pack_V=vb,diode_drop_sensitivity_V=vd,ground_current_sensitivity_A=ig,
   LDO_input_V=vin,margin_to4_8V_reference_V=vin-vref,
   available_output_load_at_reference_A=(vb-vd-vref)/r-vref/rbleed-ig))
rmin=c['resistance_each_ohm']*(1-c['total_resistance_variation_allocation'])
p_each=12.6**2/rmin
report={'source_sha256':{x:hashlib.sha256((root/x).read_bytes()).hexdigest() for x in paths},
 'assumptions':{'load_A':load,'load_qualified':False,'pack_endpoints_V':[9.,12.6],
 'diode_drop_sensitivity_V':[1.,1.25],'diode_basis':'BAS116 max at10mA/150mA,25C pulsed; not whole temperature guarantee atactual current',
 'ground_current_sensitivity_A':[0.,350e-6],'ground_current_basis':'TPS709350uA is typical at150mA, not maximum atactual load;0 is optimistic comparison',
 'LDO_input_screen_reference_V':vref,'reference_basis':'3.3V+1.5V load regulation characterization condition; not dropout threshold',
 'additional_capacitor_charge_and_leakage_included':False},
 'rows':rows,'downstream_short_at12_6V_zero_diode':{'each_resistor_W':p_each,'total_W':2*p_each,'general_P70_W_each':.27,'board_thermal_qualified':False},
 'one_open_normal_operation_qualified':False,'one_short_current_limit_present':False,
 'decision':'Prefer parallel1.5kohm feed for headroom and shared loss; cold/ramp/load/thermal/fault qualification still incomplete',
 'manufacturing_release':False}
a.out.mkdir(parents=True,exist_ok=True);(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'rows':len(rows),'each_short_W':p_each,'manufacturing_release':False}))
