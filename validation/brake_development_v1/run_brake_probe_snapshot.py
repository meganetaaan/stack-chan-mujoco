"""Test a hysteretic dissipative brake added to the archived supply probes.

LM393B/TL431B-style behavior is approximated, with explicit offset, component
corners and response lag. The MOSFET is a switch model, not a vendor macro-model.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--case',choices=['normal','regeneration','brake_open'],default='regeneration')
    p.add_argument('--corner',choices=['nominal','late','early'],default='nominal')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    regen=a.case!='normal'
    source=ROOT/'validation/supply_development_v1'/('supply_regeneration_v2' if regen else 'supply_probe_v2')/'probe.cir'
    c={'reference_V':2.495,'rtop_ohm':11800.,'rbottom_ohm':10000.,'rfeedback_ohm':1e6,
       'rbrake_ohm':4.7,'rmos_ohm':.05,'gate_capacity_F':1.5e-9,'response_tau_s':5e-6,
       'offset_V':0.,'bus_capacity_F':.001,'regulator_V':5.}
    if a.corner=='late':
        c.update(reference_V=2.495*1.005,rtop_ohm=11800*1.01,rbottom_ohm=10000*.99,
                 rfeedback_ohm=1e6*.99,rbrake_ohm=4.7*1.05,rmos_ohm=.1,
                 gate_capacity_F=2e-9,response_tau_s=20e-6,offset_V=.004,bus_capacity_F=.0008,regulator_V=5.15)
    elif a.corner=='early':
        c.update(reference_V=2.495*.995,rtop_ohm=11800*.99,rbottom_ohm=10000*1.01,
                 rfeedback_ohm=1e6*1.01,rbrake_ohm=4.7*.95,offset_V=-.004,regulator_V=5.15)
    gates={'operating_min_V':4.75,'operating_max_V':5.8 if regen else 5.25,
           'energy_relative_error_max':.01,'brake_resistor_energy_max_J':.15,
           'brake_resistor_peak_power_max_W':10.,'normal_brake_energy_max_J':.001}
    plan={'scope':__doc__,'case':a.case,'corner':a.corner,'parameters':c,'criteria':gates,
          'source_path':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
          'sources':{'comparator':'https://www.ti.com/lit/ds/symlink/lm393.pdf',
                     'reference':'https://www.ti.com/lit/ds/symlink/tl431.pdf'},
          'limitations':['gate RC and comparator lag are engineering scenarios, not guaranteed delays',
                         'MOSFET and resistor part selection/thermal mounting still pending',
                         '5.8 V fault ceiling leaves 0.2 V below the 6 V actuator operating maximum',
                         'normal supply gate remains 4.75-5.25 V',
                         '1 A regeneration injection is a fault source, not a coupled motor prediction',
                         'brake_open is expected to fail; independent overvoltage cutoff is still required']}
    (a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    text=source.read_text()
    assert text.count('Cout rail 0 1000u')==1
    text=text.replace('Cout rail 0 1000u',f'Cout rail 0 {c["bus_capacity_F"]}')
    text=text.replace('Vref reference 0 PWL(0 0 .005 5)',f'Vref reference 0 PWL(0 0 .005 {c["regulator_V"]})')
    brake=f'''* Comparator and dissipative brake candidate
Rtop bus sense {c['rtop_ohm']}
Rbottom sense 0 {c['rbottom_ohm']}
Rfeedback gate sense {c['rfeedback_ohm']}
Rpull bus gate 2200
Cgate gate 0 {c['gate_capacity_F']}
Rbias bus refbrake 2200
Bref refbrake 0 V=min({c['reference_V']},max(V(bus)-1,0))
Berror cmp 0 V=V(refbrake)-V(sense)+{c['offset_V']}
Rlag cmp cmpfilter 10000
Clag cmpfilter 0 {c['response_tau_s']/10000}
Ssink gate 0 cmpfilter 0 SCOMP
.model SCOMP SW(RON=50 ROFF=1e9 VT=0 VH=.001)
Rbrake bus drain {c['rbrake_ohm']}
Sbrake drain 0 gate 0 SMOS
.model SMOS SW(RON={c['rmos_ohm']} ROFF=1e9 VT={100 if a.case=='brake_open' else 2.5} VH=.05)
Bquiescent bus 0 I=.0008
'''
    text=text.replace('.control',brake+'.control')
    if regen:text=text.replace('tran 100u 0.15 0 100u uic','tran 1u 0.15 0 1u uic')
    text=text.replace('i(Lout) v(wave)','i(Lout) v(wave) v(gate) v(drain) v(sense) v(refbrake)')
    (a.out/'brake.cir').write_text(text)
    run=subprocess.run([str(ROOT/'.tools/root/usr/bin/ngspice'),'-b','brake.cir'],cwd=a.out.resolve(),text=True,capture_output=True)
    (a.out/'ngspice.log').write_text(run.stdout+run.stderr);run.check_returncode()
    data=np.loadtxt(a.out/'trace.dat',skiprows=1)
    assert np.isfinite(data).all()
    time=data[:,0];vb,vi,vd,vr,vl,rail,bus,ib,il,load,gate,drain,sense,ref=data[:,1:].T
    brake_i=(bus-drain)/c['rbrake_ohm']
    control_i=(bus-sense)/c['rtop_ohm']+(bus-gate)/2200+(bus-ref)/2200+.0008
    integrate=lambda x:float(np.trapezoid(x,time))
    energy_in=integrate(-vb*ib)
    energy_load=integrate(bus*load)
    energy_brake=integrate(bus*brake_i)
    resistor_power=brake_i**2*c['rbrake_ohm']
    energy_control=integrate(bus*control_i)
    losses=integrate((vb-vi)**2/.1+il**2*.03+(rail-bus)**2/.02+(vd-vr)*il+
                     np.maximum(vd*il,0)*(1/.85-1))
    stored=lambda k:.5*c['bus_capacity_F']*rail[k]**2+.5*1e-6*il[k]**2+.5*100e-6*vi[k]**2
    residual=energy_in-energy_load-energy_brake-energy_control-losses-3*(time[-1]-time[0])-(stored(-1)-stored(0))
    active=time>=.05
    checks={'voltage':bool(bus[active].min()>=gates['operating_min_V'] and bus[active].max()<=gates['operating_max_V']),
            'energy_accounting':bool(abs(residual)/max(abs(energy_in),1e-9)<gates['energy_relative_error_max']),
            'resistor_energy':integrate(resistor_power)<=gates['brake_resistor_energy_max_J'],
            'resistor_peak_power':bool(resistor_power.max()<=gates['brake_resistor_peak_power_max_W'])}
    if not regen:checks['no_normal_braking']=energy_brake<=gates['normal_brake_energy_max_J']
    report={'scope':__doc__,'case':a.case,'corner':a.corner,'gates':checks,'passed_screen':all(checks.values()),
            'minimum_operating_bus_V':float(bus[active].min()),'maximum_operating_bus_V':float(bus[active].max()),
            'brake_energy_J':energy_brake,'resistor_energy_J':integrate(resistor_power),
            'resistor_peak_power_W':float(resistor_power.max()),'mosfet_peak_power_W':float((drain*brake_i).max()),
            'control_input_energy_J':energy_control,'energy_residual_J':residual,
            'energy_relative_error':abs(residual)/abs(energy_in),'protection_design_verified':False}
    np.savez_compressed(a.out/'trace.npz',time_s=time,bus_V=bus,gate_V=gate,brake_current_A=brake_i,
                        resistor_power_W=resistor_power,mosfet_power_W=drain*brake_i)
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
