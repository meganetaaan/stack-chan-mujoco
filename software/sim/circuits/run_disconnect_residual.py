"""Characterize stored output energy after ideal battery disconnection, with optional prescribed regeneration."""
import argparse, hashlib, json, re, subprocess
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[3]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', type=Path, required=True)
p.add_argument('--bleed-ohms', type=float, default=0., help='Resistance of each of two permanent bleed branches; zero disables them')
p.add_argument('--open-bleeds', type=int, choices=[0,1,2], default=0)
p.add_argument('--regen-start-s',type=float,default=.1)
p.add_argument('--regen-a', type=float, default=0., help='Injected return current for 20 ms from regen-start-s, 1 us edges')
p.add_argument('--cout-uf', type=float, default=800.)
a = p.parse_args()
assert np.isfinite(a.bleed_ohms) and a.bleed_ohms >= 0
assert np.isfinite(a.regen_start_s) and .08 <= a.regen_start_s < .979999
assert np.isfinite(a.regen_a) and a.regen_a >= 0
assert np.isfinite(a.cout_uf) and a.cout_uf > 0
a.out.mkdir(parents=True, exist_ok=False)
base = ROOT/'validation/coupled_power_ldo_development_v1/coupled_power_startup_continuous_v2/coupled.cir'
plan = {'scope': __doc__, 'source_sha256': hashlib.sha256(base.read_bytes()).hexdigest(),
        'bleed_each_ohm': a.bleed_ohms, 'open_bleeds': a.open_bleeds, 'Cout_uF': a.cout_uf,
        'regeneration_A': a.regen_a, 'regeneration_window_s': [a.regen_start_s,a.regen_start_s+.02],
        'battery_V': 7.4, 'disconnect_s': .08, 'stop_s': 1., 'motor_current_A': 0.,
        'measurements_s': [.079, .081, .1, .2, 1.],
        'criteria': {'finite_measurements': True, 'simulation_reaches_s': 1.},
        'limitations': ['Characterization only; no discharge time or safe-voltage acceptance established',
                       'Ideal disconnect switch is a test fixture, not a selected protection component',
                       'Only Cout energy is reported, not total system or mechanical energy',
                       'Existing behavioral LDO, converter and brake assumptions retained',
                       'Prescribed current injection is not a coupled shutdown motor model; no external backfeed, component tolerances or thermal qualification']}
(a.out/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
net = base.read_text().split('.control')[0]
net, n = re.subn(r'^Vbattery.*$', 'Vbattery battery 0 PWL(0 0 .0002 7.4)', net, flags=re.M)
assert n == 1
net, n = re.subn(r'^Rb battery vin .1$', '''Vdisconnect disconnect 0 PWL(0 1 .08 1 .080001 0)
Sdisconnect battery switched disconnect 0 DISCONNECT
.model DISCONNECT SW(RON=1u ROFF=1e12 VT=.5 VH=0)
Rb switched vin .1''', net, flags=re.M)
assert n == 1
net, n = re.subn(r'Vwave wave 0 PWL\(.*?^\+ \)', 'Vwave wave 0 0', net, flags=re.M|re.S)
assert n == 1
if a.regen_a:
    net = net.replace('Vwave wave 0 0', f'Vwave wave 0 PWL(0 0 {a.regen_start_s:.12g} 0 {a.regen_start_s+1e-6:.12g} {-a.regen_a:.12g} {a.regen_start_s+.02:.12g} {-a.regen_a:.12g} {a.regen_start_s+.020001:.12g} 0 1 0)')
assert re.search(r'^Cout rail 0 800u$', net, re.M)
net = net.replace('Cout rail 0 800u', f'Cout rail 0 {a.cout_uf:.12g}u')
if a.bleed_ohms:
    for branch in range(2-a.open_bleeds):
        net += f'Rbleed{branch} rail 0 {a.bleed_ohms:.12g}\n'
vectors = 'v(vin) v(rail) v(bus) v(aux) v(en) i(Lout) i(Vbattery) v(drain0) v(drain1) v(gate0) v(gate1)'
measures = [('bus_after_disconnect_max', 'meas tran bus_after_disconnect_max MAX v(bus) FROM=.08 TO=1')]
for index, t in enumerate(plan['measurements_s']):
    for field, expr in [('bus','v(bus)'), ('rail','v(rail)'), ('en','v(en)'), ('aux','v(aux)')]:
        measures.append((f'{field}_{index}', f'meas tran {field}_{index} FIND {expr} AT={t}'))
net += f'.save {vectors}\n.control\nset wr_singlescale\nset wr_vecnames\ntran 100u 1 0 1u uic\n'
for branch in range(2):
    match=re.search(r'^Rbrake'+str(branch)+r' bus drain'+str(branch)+r' ([0-9.eE+-]+)$',net,re.M)
    assert match
    resistance=float(match.group(1))
    net += f'let brake_current{branch} = (v(bus)-v(drain{branch}))/{resistance:.12g}\n'
    net += f'let brake_power{branch} = brake_current{branch}*brake_current{branch}*{resistance:.12g}\n'
    net += f'let mos_power{branch} = v(drain{branch})*brake_current{branch}\n'
    for part in ['brake','mos']:
        for metric,operation in [('energy_J','INTEG'),('peak_W','MAX')]:
            key=f'{part}{branch}_{metric}'
            measures.append((key,f'meas tran {key} {operation} {part}_power{branch} FROM=.08 TO=1'))
net += '\n'.join(line for _, line in measures)
net += f'\nlinearize {vectors}\nwrdata display_trace.dat {vectors}\nquit\n.endc\n.end\n'
(a.out/'disconnect.cir').write_text(net)
with (a.out/'ngspice.log').open('w') as log:
    r = subprocess.run([str(ROOT/'.tools/root/usr/bin/ngspice'), '-b', 'disconnect.cir'], cwd=a.out.resolve(), stdout=log, stderr=subprocess.STDOUT)
(a.out/'run.json').write_text(json.dumps({'returncode':r.returncode})+'\n')
r.check_returncode()
log = (a.out/'ngspice.log').read_text()
values = {}
for key, _ in measures:
    found = re.search(r'^'+key+r'\s*=\s*([-+0-9.eE]+)', log, re.M|re.I)
    assert found, key
    values[key] = float(found.group(1))
assert all(np.isfinite(v) for v in values.values())
data = np.loadtxt(a.out/'display_trace.dat', skiprows=1)
assert np.isfinite(data).all() and abs(data[-1,0]-1.) < 1e-6
samples = [{'time_s':t, **{f'{k}_V':values[f'{k}_{i}'] for k in ['bus','rail','aux','en']},
            'Cout_energy_J': .5*a.cout_uf*1e-6*values[f'rail_{i}']**2} for i,t in enumerate(plan['measurements_s'])]
report = {'samples':samples, 'numerical_checks_passed':True, 'post_disconnect_absorber_measurements':{k:v for k,v in values.items() if k.startswith(('brake','mos'))}, 'bus_after_disconnect_max_V':values['bus_after_disconnect_max'], 'protection_design_verified':False}
(a.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps(report, indent=2))
