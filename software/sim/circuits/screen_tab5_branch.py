"""Static divider screen; not a transient model or 3S qualification."""
import hashlib
import itertools
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
p = ROOT / 'schematics/power/tab5_input_branch_candidate.json'
raw = p.read_bytes()
d = json.loads(raw)
parts = {x['reference']: x for x in d['parts']}
results = {}
for name, prefix, limits in [('UV_rise', 'UV', [1.175, 1.225]),
                              ('UV_fall', 'UV', [1.08, 1.125]),
                              ('OV_rise', 'OV', [1.17, 1.225]),
                              ('OV_fall', 'OV', [1.085, 1.125])]:
    top = parts['TAB5__R_'+prefix+'_TOP']['value_ohm']
    bottom = parts['TAB5__R_'+prefix+'_BOTTOM']['value_ohm']
    values = [v*(1+top*ta/(bottom*ba)) + leak*top*ta
              for v, ta, ba, leak in itertools.product(limits, [.99,1.01], [.99,1.01], [-100e-9,100e-9])]
    results[name] = {'minimum_V':min(values), 'maximum_V':max(values), 'corners':len(values)}
report = {'source_sha256':hashlib.sha256(raw).hexdigest(),
          'formula':'Vin relative to RTN = Vthreshold*(1+Rtop/Rbottom)+Ileak*Rtop',
          'assumptions':['resistor total allocation +/-1%; process/aging not qualified',
                         'datasheet section7.5 limits screened; heading uses Vin24V',
                         'RTN-to-PACK_RETURN offset omitted, not a guarantee at 3S'],
          'divider_screen':results,
          'static_headroom_before_wiring_and_switch_V':results['UV_fall']['minimum_V']-6,
          'scope':'Only static divider selection; no load/inrush/thermal/response-delay/restart proof',
          'branch_operational':False,'manufacturing_release':False}
out=ROOT/'validation/tab5_branch_v1';out.mkdir(exist_ok=True)
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
