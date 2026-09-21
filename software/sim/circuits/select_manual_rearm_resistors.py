"""Attach manufacturer-coded resistor candidates to revH without changing connectivity."""
import argparse,csv,hashlib,json,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--current',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
root=Path(__file__).resolve().parents[3];spec_path=root/'schematics/power/manual_rearm_resistors.json';assembly_path=root/'schematics/power/manual_rearm_revH/assembly.json'
if a.current:
 current=json.loads((root/'schematics/power/manual_rearm_current.json').read_text());spec_path=root/current['resistor_selection'];assembly_path=root/current['assembly']
d=json.loads(spec_path.read_text());assembly=json.loads(assembly_path.read_text());refs={x['reference']:x for x in assembly['parts']};rows=[]
temp=max(abs(t-d['reference_temperature_C']) for t in d['comparison_temperature_C'])
for r in d['resistors']:
    assert r['reference'] in refs
    value_match=re.match(r'(\d+(?:\.\d+)?)([kM]?)',refs[r['reference']]['part'])
    assert value_match
    original_value=float(value_match[1])*{'':1,'k':1000,'M':1000000}[value_match[2]]
    assert original_value==r['value_ohm'], 'Value changed: '+r['reference']
    assert 47<=r['value_ohm']<=(332000 if r['size_imperial']=='0603' else 1000000)
    factor_hi=(1+r['initial_tolerance'])*(1+r['TCR_ppm_K']*1e-6*temp)*(1+d['load_life_comparison']['maximum_fractional_change'])
    factor_lo=(1-r['initial_tolerance'])*(1-r['TCR_ppm_K']*1e-6*temp)*(1-d['load_life_comparison']['maximum_fractional_change'])
    assert max(factor_hi-1,1-factor_lo)<d['existing_total_tolerance_budget']
    # 5.25 V across every resistor is a conservative rail voltage comparison,
    # not a complete fault-voltage or temperature calculation.
    rows.append(dict(r,net1=refs[r['reference']]['pins']['1'],net2=refs[r['reference']]['pins']['2'],factor_lower=factor_lo,factor_upper=factor_hi,power_upper_at_5_25V_W=5.25**2/(r['value_ohm']*factor_lo)))
assert {r['reference'] for r in rows}=={r for r in refs if r.startswith('R')}
with (a.out/'resistor_bom.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
report={'resistors':len(rows),'resistance_values_unchanged':True,'size_exception':'R11=1 Mohm requires 0805; TNPW0603 maximum332 kohm','maximum_compared_fractional_drift':max(r['factor_upper']-1 for r in rows),'maximum_resistor_power_comparison_W':max(r['power_upper_at_5_25V_W'] for r in rows),'existing_total_tolerance_budget':d['existing_total_tolerance_budget'],'source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [spec_path,assembly_path]},'limits':['load-life comparison is not a combined environmental guarantee','film temperature board leakage soldering and required lifetime unresolved','ordering-code compatibility checked; purchasing availability not checked'],'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
