"""Check ideal cell-to-channel wiring and mask; not a protection simulation."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
d = json.loads((ROOT / 'schematics/power/bq76942_candidate.json').read_text())
m = d['cell_input_map']
# Distinct cell voltages expose swaps; these are diagnostic values, not a battery model.
cell_voltages = [3.2, 3.7, 4.1]
taps = [0.0]
for voltage in cell_voltages:
    taps.append(taps[-1] + voltage)
nodes = {int(p['signal'][2:]): taps[p['physical_stack_tap']] for p in m['pins']}
channels = {i: round(nodes[i]-nodes[i-1], 9) for i in range(1, 11)}
mask = int(m['vcell_mode']['value_hex'], 16)
active = [i for i in range(1, 11) if mask & (1 << (i-1))]
assert active == [1, 2, 10]
assert [channels[i] for i in active] == cell_voltages
assert all(channels[i] == 0 for i in range(3, 10))
assert mask == sum(1 << (i-1) for i in active)
# Demonstrate why a naive three-lowest-channels setting is wrong.
wrong_mask_channels = [i for i in range(1, 11) if 0x0007 & (1 << (i-1))]
report = {'scope': 'ideal connectivity and mask only; no RC, timing, IC behavior or physical validation',
          'result': 'consistent', 'diagnostic_cell_voltages_V': cell_voltages,
          'IC_channel_voltages_V': channels, 'active_channels': active,
          'vcell_mode': hex(mask), 'wrong_0x0007_channels': wrong_mask_channels,
          'wrong_0x0007_misses_physical_cell': 3,
          'wrong_0x0007_monitors_shorted_channel': 3,
          'manufacturing_release': False}
out = ROOT / 'validation/bq76942_3s_mapping_v1/report.json'
out.write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
