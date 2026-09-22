"""Select input capacitor comparison from explicit supplier ratings, not measured behavior."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
source=ROOT/'validation/precision_module_comparison_v1/report.json'
spec=json.loads(source.read_text())['new_module_candidate']
assert spec['input_cap_min_ripple_A']==.7
part={'part':'EEUFR1C471','manufacturer':'Panasonic','quantity_per_module':1,'module_quantity':2,'nominal_F':470e-6,'initial_tolerance_fraction':.2,'rated_voltage_V':16,'rated_ripple_A_at100kHz':.95,'impedance_max_ohm_at100kHz':.056,'ESR_min_ohm':None,'body_diameter_mm':8,'body_length_mm':11.5,'lead_pitch_mm':3.5,'leakage_max_A':75.2e-6,'source':'https://industrial.panasonic.com/ww/products/pt/aluminum-cap-lead/models/EEUFR1C471'}
checks={'initial_C_min_F':part['nominal_F']*.8,'initial_C_max_F':part['nominal_F']*1.2,'required_input_C_F':220e-6,'ripple_rating_margin_A_at_table_frequency':.95-.7,'DC_voltage_headroom_at_pack_full_V':16-12.6,'DC_voltage_headroom_at_module_operating_limit_V':16-14}
assert checks['initial_C_min_F']>=checks['required_input_C_F'] and checks['ripple_rating_margin_A_at_table_frequency']>0
r={'source_sha256':{str(source.relative_to(ROOT)):hashlib.sha256(source.read_bytes()).hexdigest()},'part_candidate':part,'checks':checks,
 'revision_correction':'PTH table footnote500mArms is not sufficient requirement for5V: application p13 specifies700mArms forVO>=3V; use stricter applicable condition',
 'decision':'Select for input-side detailed design; not installed in current assembly or procurement released',
 'output_bank_rule':{'minimum_C_at5V_F':330e-6,'minimum_bank_ESR_without_TurboTrans_ohm':.007,'applies_to':'entire output capacitor bank, including connected downstream capacitors; not only selected local capacitor','isolated_cap_ESR_max_is_not_min':True,'bank_minimum_verified':False},
 'limits':['470uF +/-20% covers initial tolerance only; temperature,aging and source impedance need review','950mArms is100kHz rating; actual ripple spectrum/frequency coefficient and hot-enclosure life are not qualified','Impedance maximum is not a guaranteed minimum ESR and cannot prove output-bank7mohm requirement','16V capacitor rating does not protect module from excursions above14V','Optional high-frequency ceramic, pin routing, mounting height and inrush energy remain','Capacitor model not executed; no full supply stability claim'],
 'sources':[{'url':'https://www.ti.com/lit/gpn/pth08t240w','revision':'J June2009','sections':['p5 footnotes5/6','p13 input capacitor','p14 non-TurboTrans output bank']}, {'url':part['source'],'section':'Specifications'}],
 'next_design_decision':'Before local output capacitor selection, bound whole output bank with connected servos or compare PTH08T241W ceramic-optimized variant; do not infer lower ESR bound from upper ESR catalog rating.',
 'manufacturing_release':False}
out=ROOT/'schematics/power/pth_input_cap_candidate_v1'
(out/'selection.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(checks))
