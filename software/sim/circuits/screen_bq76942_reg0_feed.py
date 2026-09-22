"""DC voltage/loss trade-off only; does not model BREG loop or startup."""
import csv
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'validation/bq76942_reg0_feed_v1'
OUT.mkdir(exist_ok=True)
# Keep origin and scope explicit: these are comparison points, not load guarantees.
assumptions = {
    'pack_V': [9.0, 9.9438, 12.6],
    'pack_origin': '3x manufacturer general 3V floor; 3x existing static CUV minimum; 3x4.2V full charge. Dynamic cell floor not qualified.',
    'collector_current_A': [0.010, 0.020, 0.045],
    'current_origin': 'comparison points, not measured control load or REG1 output current; BREG base and IC current use a separate feed',
    'diode_drop_V': [0.45, 1.0],
    'diode_scope': 'BAT46W 25C limits at 10mA and 250mA respectively; cross-product is sensitivity analysis, not guaranteed bounds at other currents/temperatures',
    'regin_upper_V': 5.8,
    'regin_scope': 'TI 7.11 conditional upper regulation voltage, requires BAT>8V and suitable transistor',
    'VCE_reserve_V': 1.0,
    'VCE_origin': 'engineering screening allowance; not a guaranteed FCX495 dropout specification',
    'resistor_tolerance_fraction': 0.001,
    'resistor_temperature_drift_included': False,
}
rows=[]
for r in [100.0, 47.0, 22.1]:
    rmax=r*(1+assumptions['resistor_tolerance_fraction'])
    for vp in assumptions['pack_V']:
        for i in assumptions['collector_current_A']:
            for vd in assumptions['diode_drop_V']:
                vc=vp-vd-i*rmax
                available=vc-assumptions['regin_upper_V']
                rows.append(dict(R_ohm=r,pack_V=vp,collector_A=i,diode_V=vd,
                    collector_V=vc,available_VCE_V=available,
                    screen_margin_V=available-assumptions['VCE_reserve_V'],
                    resistor_W=i*i*rmax,
                    conditional_transistor_W=i*max(0,available)))
with (OUT/'comparison.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
fault=[]
for r in [100.0,47.0,22.1]:
    rmin=r*(1-assumptions['resistor_tolerance_fraction'])
    fault.append({'R_ohm':r,'collector_short_zero_diode_drop_A':12.6/rmin,
                  'resistor_short_W':12.6**2/rmin})
report={'scope':'DC candidate comparison, not circuit qualification', 'assumptions':assumptions,
        'cases':len(rows),'short_comparison':fault,
        'selection':'22.1 ohm as next feed candidate; separate branch fault protection required',
        'unknowns':['actual local controller and interface load','cold diode drop','BREG headroom and base current','transistor gain and SOA over temperature','capacitor effective values and loop stability','branch short protection and PCB thermal path'],
        'manufacturing_release':False}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
for row in rows:
    if row['pack_V']==9 and row['collector_A']==0.020 and row['diode_V']==1:
        print(row)
print('short comparison:',fault)
