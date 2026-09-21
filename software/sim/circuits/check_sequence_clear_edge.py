"""Bound a released GPIO pullup edge; capacitance is a design budget, not measured."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
a = p.parse_args()
a.out.mkdir(parents=True, exist_ok=False)
source = Path('validation/sequence_clear_driver_v1/plan.json')
plan = {
    'scope': 'Valid common 3.207..3.393 V rail; GPIO releases from <=0.4 V to high impedance.',
    'manufacturer_limits': {'input_rate_ns_per_V': 200, 'VIH_V': 2.0, 'VIL_V': 0.9, 'GPIO_sink_A': 0.006},
    'engineering_assumptions': {
        'capacitance_budget_F': 50e-12, 'resistor_total_tolerance': 0.01,
        'leakage_sink_A': 13.58e-6, 'initial_voltage_V': 0.4,
        'board_leakage': 'Excluded; must be budgeted before integration',
        'edge_interval': 'Check local slope throughout logic window and additionally 10..90% of final excursion. The latter is an engineering diagnostic, not a claimed manufacturer definition.'},
    'sources': {'receiver': 'https://assets.nexperia.com/documents/data-sheet/74AUP1G06.pdf Table 6,7 Rev12',
                'driver': 'https://www.st.com/resource/en/datasheet/stm32g030f6.pdf Table50 DS12991 Rev6'},
    'stop': 'Compare previous 10k proposal with one 1k candidate. No capacitance sweep; actual capacitance qualification remains open.'}
(a.out / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
rows = []
for r in (10000, 1000):
    rmax = r * 1.01
    final = 3.207 - 13.58e-6 * rmax
    tau = rmax * 50e-12
    # dt/dV = RC/(Vfinal-V); maximum on any interval occurs at its upper end.
    logic_rate = tau / (final - 2.0)
    diagnostic_rate = tau / (0.1 * (final - 0.4))
    sink = 3.393 / (r * .99) + .5e-6
    rows.append({'R_ohm': r, 'final_lower_V': final,
                 'logic_window_max_ns_per_V': logic_rate * 1e9,
                 'excursion_10_90_max_ns_per_V': diagnostic_rate * 1e9,
                 'diagnostic_capacitance_limit_pF': 200e-9 * .1 * (final - .4) / rmax * 1e12,
                 'sink_A_upper': sink, 'resistor_power_W_upper': 3.393**2 / (r * .99),
                 'conditional_budget_pass': final >= 2 and logic_rate <= 200e-9 and diagnostic_rate <= 200e-9 and sink <= .006})
assert not rows[0]['conditional_budget_pass'] and rows[1]['conditional_budget_pass']
report = {'rows': rows, 'baseline_plan_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'status': '1k conditional candidate, not integrated or manufacturer edge qualification',
          'remaining': ['Actual total pin plus trace capacitance maximum', 'Board leakage and rail current budget',
                        'Manufacturer transition interval interpretation', 'Driven GPIO edges, reset, brownout and power sequencing'],
          'manufacturing_release': False}
(a.out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(rows, indent=2))
