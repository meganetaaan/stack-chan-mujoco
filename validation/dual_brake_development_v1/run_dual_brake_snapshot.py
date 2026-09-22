"""Independent reference/comparator/resistor branches; development fault study only."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[3]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--fault', choices=['none', 'primary_open', 'secondary_open', 'both_open'], default='none')
    parser.add_argument('--normal-load', action='store_true')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    source = ROOT / 'validation/supply_development_v1' / ('supply_probe_v2' if args.normal_load else 'supply_regeneration_v2') / 'probe.cir'
    # Both branches use the late-switching development corner. The second
    # branch has its own reference, comparator, MOSFET, resistor and gate clamp.
    common = dict(reference_V=2.495*1.005, rbottom_ohm=9900., rfeedback_ohm=990000.,
                  rbrake_ohm=4.7*1.05, rmos_ohm=.1, offset_V=.004,
                  lag_s=20e-6, gate_capacity_F=2e-9, zener_knee_V=7.7625,
                  zener_slope_ohm=80., zener_capacity_F=200e-12)
    branches = [dict(common, rtop_ohm=11800*1.01), dict(common, rtop_ohm=12100*1.01)]
    opened = [args.fault in ('primary_open', 'both_open'), args.fault in ('secondary_open', 'both_open')]
    criteria = dict(bus_min_V=4.75, bus_max_V=5.25 if args.normal_load else 5.8,
                    gate_abs_max_V=10., resistor_peak_W=10., resistor_energy_J=.15,
                    zener_peak_W=.1, pullup_peak_W=.25, energy_relative_error=.01,
                    normal_brake_energy_J=.001)
    plan = dict(scope=__doc__, fault=args.fault, normal_load=args.normal_load,
                branches=branches, branch_open=opened, criteria=criteria,
                source=str(source.relative_to(ROOT)), source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                limitations=['Development corners, not all component/temperature bounds',
                             'Open fault disables only one dissipative switch; no common-cause coverage',
                             'Reference, comparator, gate and zener are behavioral approximations',
                             'No short/stuck-on detection, fuse, battery undervoltage or upstream shutdown yet',
                             'Injected regeneration is not a coupled motor model',
                             'No thermal mounting or physical independence verification'])
    (args.out/'plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    netlist = source.read_text().replace('Cout rail 0 1000u', 'Cout rail 0 800u').replace('Vref reference 0 PWL(0 0 .005 5)', 'Vref reference 0 PWL(0 0 .005 5.15)')
    lines = []
    outputs = []
    for i, c in enumerate(branches):
        suffix = str(i)
        sense, gate, ref, cmp, filt, drain = [n+suffix for n in ('sense','gate','refbrake','cmp','filt','drain')]
        lines.extend([
            f'Rtop{i} bus {sense} {c["rtop_ohm"]}',
            f'Rbottom{i} {sense} 0 {c["rbottom_ohm"]}',
            f'Rfeedback{i} {gate} {sense} {c["rfeedback_ohm"]}',
            f'Rpull{i} bus {gate} 2200',
            f'Cgate{i} {gate} 0 {c["gate_capacity_F"]+c["zener_capacity_F"]}',
            f'Rbias{i} bus {ref} 2200',
            f'Bref{i} {ref} 0 V=min({c["reference_V"]},max(V(bus)-1,0))',
            f'Berror{i} {cmp} 0 V=V({ref})-V({sense})+{c["offset_V"]}',
            f'Rlag{i} {cmp} {filt} 10000',
            f'Clag{i} {filt} 0 {c["lag_s"]/10000}',
            f'Ssink{i} {gate} 0 {filt} 0 SCOMP{i}',
            f'.model SCOMP{i} SW(RON=50 ROFF=1e9 VT=0 VH=.001)',
            f'Rbrake{i} bus {drain} {c["rbrake_ohm"]}',
            f'Sbrake{i} {drain} 0 {gate} 0 SMOS{i}',
            f'.model SMOS{i} SW(RON={c["rmos_ohm"]} ROFF=1e9 VT={100 if opened[i] else 2.5} VH=.05)',
            f'Bzener{i} {gate} 0 I=max(0,(V({gate})-{c["zener_knee_V"]})/{c["zener_slope_ohm"]})',
            f'Bquiescent{i} bus 0 I=.0008'])
        outputs.extend(f'v({n})' for n in (gate,drain,sense,ref))
    netlist = netlist.replace('.control', '\n'.join(lines)+'\n.control')
    netlist = netlist.replace('i(Lout) v(wave)', 'i(Lout) v(wave) '+' '.join(outputs))
    if not args.normal_load:
        netlist = netlist.replace('tran 100u 0.15 0 100u uic', 'tran 1u 0.15 0 1u uic')
    (args.out/'dual_brake.cir').write_text(netlist)
    run = subprocess.run([str(ROOT/'.tools/root/usr/bin/ngspice'), '-b', 'dual_brake.cir'], cwd=args.out.resolve(), text=True, capture_output=True)
    (args.out/'ngspice.log').write_text(run.stdout+run.stderr)
    run.check_returncode()
    data = np.loadtxt(args.out/'trace.dat', skiprows=1)
    assert np.isfinite(data).all()
    t = data[:,0]
    vb, vi, vd, vr, vl, rail, bus, ib, il, load = data[:,1:11].T
    integrate = lambda x: float(np.trapezoid(x,t))
    details = []
    brake_total = np.zeros_like(t)
    control_total = np.zeros_like(t)
    waveforms = dict(time_s=t, bus_V=bus)
    for i, c in enumerate(branches):
        gate, drain, sense, ref = data[:,11+4*i:15+4*i].T
        current = (bus-drain)/c['rbrake_ohm']
        resistor_power = current**2*c['rbrake_ohm']
        zener_i = np.maximum(0,(gate-c['zener_knee_V'])/c['zener_slope_ohm'])
        brake_total += bus*current
        control_total += bus*((bus-sense)/c['rtop_ohm']+(bus-gate)/2200+(bus-ref)/2200+.0008)
        details.append(dict(open=opened[i], gate_max_V=float(np.abs(gate).max()),
                            resistor_peak_W=float(resistor_power.max()), resistor_energy_J=integrate(resistor_power),
                            zener_peak_W=float((gate*zener_i).max()), pullup_peak_W=float(((bus-gate)**2/2200).max()),
                            mosfet_peak_W=float((drain*current).max())))
        waveforms.update({f'gate{i}_V':gate, f'brake{i}_A':current, f'resistor{i}_W':resistor_power})
    energy_in = integrate(-vb*ib)
    losses = integrate((vb-vi)**2/.1+il**2*.03+(rail-bus)**2/.02+(vd-vr)*il+np.maximum(vd*il,0)*(1/.85-1))
    stored = lambda k:.5*.0008*rail[k]**2+.5*1e-6*il[k]**2+.5*100e-6*vi[k]**2
    residual = energy_in-integrate(bus*load)-integrate(brake_total)-integrate(control_total)-losses-3*(t[-1]-t[0])-(stored(-1)-stored(0))
    active = t >= .05
    checks = dict(voltage=bool(bus[active].min()>=criteria['bus_min_V'] and bus[active].max()<=criteria['bus_max_V']),
                  energy_accounting=bool(abs(residual)/abs(energy_in)<criteria['energy_relative_error']))
    for i, d in enumerate(details):
        for metric in ('resistor_peak_W','resistor_energy_J','zener_peak_W','pullup_peak_W'):
            checks[f'branch{i}_{metric}'] = d[metric]<=criteria[metric]
        checks[f'branch{i}_gate'] = d['gate_max_V']<=criteria['gate_abs_max_V']
    if args.normal_load:
        checks['no_normal_braking'] = integrate(brake_total)<=criteria['normal_brake_energy_J']
    report = dict(fault=args.fault, normal_load=args.normal_load, checks=checks, passed_screen=all(checks.values()),
                  bus_min_V=float(bus[active].min()), bus_max_V=float(bus[active].max()), branches=details,
                  energy_relative_error=abs(residual)/abs(energy_in), protection_design_verified=False)
    np.savez_compressed(args.out/'trace.npz', **waveforms)
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
