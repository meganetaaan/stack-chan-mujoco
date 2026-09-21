"""Resistor-limited brake load line; not a MOSFET qualification model."""
import hashlib
import json
from pathlib import Path

p = Path('validation/brake_mosfet_selection_v1')
plan = json.loads((p / 'plan.json').read_text())
inputs = plan['inputs']
source = Path(inputs['resistor_envelope_source'])
r = json.loads(source.read_text())['Rmin_ohm']
v = inputs['bus_limit_V']
ron = inputs['rds_comparison_ohm']
i = v / (r + ron)
result = {
    'candidate': inputs['candidate'],
    'Rmin_ohm': r,
    'full_on_comparison_current_A': i,
    'full_on_comparison_mosfet_loss_W': i*i*ron,
    'partial_conduction_max_loss_W': v*v/(4*r),
    'partial_conduction_max_loss_Vds_V': v/2,
    'partial_conduction_max_loss_Id_A': v/(2*r),
    'formula': 'Pmos=Vds*(Vbus-Vds)/R; maximum at Vds=Vbus/2',
    'assumptions': ['Bus stays at or below 6 V', 'Series resistor remains intact',
                    'No inductive transient; shunt and wiring resistance omitted',
                    '48 milliohm is a comparison at a stated datasheet condition'],
    'qualification': False,
    'next_gate': 'Actual gate drive and power-loss path; timed load line versus SOA and thermal boundary',
    'source_sha256': {str(f): hashlib.sha256(f.read_bytes()).hexdigest()
                      for f in (source, p/'plan.json')},
}
(p/'report.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
