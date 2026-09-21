"""Enumerate single ideal capacitor faults in a 3P-2S input filter."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
out=ROOT/'validation/bq76942_series_filter_v1';out.mkdir(exist_ok=True)
c=100e-9
rows=[]
for fault in ['none']+['open','short']:
    targets=[None] if fault=='none' else range(6)
    for target in targets:
        banks=[3,3]
        short_bank=None
        if fault=='open':banks[target//3]-=1
        if fault=='short':short_bank=target//3
        effective=(banks[1-short_bank]*c if short_bank is not None else c*banks[0]*banks[1]/sum(banks))
        rows.append({'fault':fault,'component':target,'capacitance_min_F':effective*.95,'capacitance_max_F':effective*1.05,'ideal_DC_short_between_terminals':False,'initial_tolerance_range_within_0p1_to_1uF':effective*.95>=1e-7 and effective*1.05<=1e-6})
assert len(rows)==13 and all(r['initial_tolerance_range_within_0p1_to_1uF'] for r in rows)
report={'scope':'one filter, ideal single component open/short and initial capacitance tolerance only','cases':rows,'parts_per_filter':6,'filters':4,'total_capacitors':24,'typical_capacitor_mass_g':24*.036,'body_area_upper_sum_mm2':24*3.4*1.8,'layout_area_including_pads_and_spacing_mm2':None,'manufacturing_release':False}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('13 ideal fault cases: capacity range check passed; not full protection qualification.')
p=ROOT/'schematics/power/bq76942_series_filter_candidate.json'
d={'status':'preferred_filter_topology_candidate_not_released','base':'bq76942_candidate.json','capacitor_part':'C1206C104J3GACAUTO','quantity':24,'topology':'two series banks, each three parallel 100nF capacitors','filters':[],'source':'https://search.kemet.com/component-documentation/download/specsheet/C1206C104J3GACAUTO','manufacturing_release':False}
base=json.loads((ROOT/'schematics/power/bq76942_candidate.json').read_text())
for i,b in enumerate(base['cell_input_filter_candidate']['branches']):
    a,z=b['capacitor_pair'];mid=f'FILTER_{i}_MID'
    d['filters'].append({'terminals':[a,z],'midpoint':mid,'midpoint_external_connection':False,'capacitors':[{'reference':f'C_F{i}_{j}','nets':[a,mid] if j<3 else [mid,z]} for j in range(6)]})
p.write_text(json.dumps(d,indent=2)+'\n')
