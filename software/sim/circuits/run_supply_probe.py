"""Run an averaged, energy-accounted supply probe with the recorded 12-axis load.

Development model: effective output impedance and response are assumptions,
not a vendor macromodel. No battery/protection design is certified here.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[3]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=ROOT/'validation/prototype_epic4_v1/load_export_left_v1/loads.npz')
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--regeneration-test',action='store_true')
    a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    with np.load(a.source) as source:
        t=source['time_s'];current=source['net_A']
    plan={'scope':__doc__,'source_sha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),
          'source_path':str(a.source.relative_to(ROOT)),
          'parameters':{'battery_open_circuit_V':7.4,'battery_resistance_ohm':.1,
                        'nominal_output_V':5.,'efficiency_assumed':.85,
                        'effective_output_inductance_H':1e-6,'effective_output_resistance_ohm':.03,
                        'output_capacitance_F':.001,'harness_resistance_ohm':.02,
                        'startup_ramp_s':.005,'load_start_s':.05},
          'regeneration_test':a.regeneration_test,
          'predefined_screen':{'operating_bus_min_V':4.75,'operating_bus_max_V':5.25,
                               'energy_relative_error_max':.01},
          'limitations':['unselected battery; resistance is a scenario','no current limit or protection yet',
                         'assumed effective output dynamics, not switching ripple',
                         'prescribed current load; motor current/torque not re-simulated at varying voltage',
                         'generic controller load 3 W; Tab5 dynamic load still to be bounded']}
    (a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    points=[(0.,0.),(.05,0.)]+[(float(x+.05),float(y)) for x,y in zip(t,current)]
    if a.regeneration_test:
        # Deliberate fault injection: load removal followed by 1 A regeneration.
        points=[(0,0),(.05,0),(.051,.3),(.099,.3),(.1,-1),(.12,-1),(.121,0),(.15,0)]
    stop=.15 if a.regeneration_test else float(t[-1]+.06)
    lines=['Recorded-load averaged supply probe',
           'Vbattery battery 0 7.4','Rb battery vin .1','Cin vin 0 100u',
           'Vref reference 0 PWL(0 0 .005 5)',
           'Bconverter drive 0 V=max(0,min(V(reference),V(vin)-.6))',
           'Drect drive rect DAVG','.model DAVG D(IS=1e-12 N=.01 RS=.001)',
           'Lout rect internal 1u','Rout internal rail .03','Cout rail 0 1000u',
           'Rwire rail bus .02',
           'Vwave wave 0 PWL(']
    lines.extend('+ %.9g %.9g'%point for point in points);lines.append('+ )')
    lines+=['Bload bus 0 I=V(wave)',
            'Binput vin 0 I=max(V(drive)*I(Lout),0)/(.85*max(V(vin),.5))',
            'Bcontroller vin 0 I=3/max(V(vin),.5)',
            '.control','set wr_singlescale','set wr_vecnames',
            f'tran 100u {stop:.9g} 0 100u uic',
            'wrdata trace.dat v(battery) v(vin) v(drive) v(rect) v(internal) v(rail) v(bus) i(Vbattery) i(Lout) v(wave)',
            'quit','.endc','.end']
    netlist=a.out/'probe.cir';netlist.write_text('\n'.join(lines)+'\n')
    command=[str(ROOT/'.tools/root/usr/bin/ngspice'),'-b',netlist.name]
    run=subprocess.run(command,cwd=a.out.resolve(),text=True,capture_output=True)
    (a.out/'ngspice.log').write_text(run.stdout+run.stderr);run.check_returncode()
    raw=np.loadtxt(a.out/'trace.dat',skiprows=1)
    time=raw[:,0];vb,vi,vd,vr,vl,rail,bus,ib,il,load=raw[:,1:].T
    assert np.isfinite(raw).all()
    input_energy=np.trapezoid(-vb*ib,time)
    output_energy=np.trapezoid(bus*load,time)
    battery_loss=np.trapezoid((vb-vi)**2/.1,time)
    output_loss=np.trapezoid(il**2*.03+load**2*.02+(vd-vr)*il,time)
    converter_loss=np.trapezoid(np.maximum(vd*il,0)*(1/.85-1),time)
    controller_energy=3*(time[-1]-time[0])
    stored=lambda k:.5*.001*rail[k]**2+.5*1e-6*il[k]**2+.5*100e-6*vi[k]**2
    residual=input_energy-output_energy-battery_loss-output_loss-converter_loss-controller_energy-(stored(-1)-stored(0))
    active=time>=.05
    gates={'operating_voltage':bool(bus[active].min()>=4.75 and bus[active].max()<=5.25),
           'energy_accounting':bool(abs(residual)/max(abs(input_energy),1e-9)<.01)}
    report={'scope':__doc__,'gates':gates,'passed_screen':all(gates.values()),
            'minimum_operating_bus_V':float(bus[active].min()),'maximum_operating_bus_V':float(bus[active].max()),
            'source_energy_J':float(input_energy),'load_energy_J':float(output_energy),
            'energy_residual_J':float(residual),'energy_relative_error':float(abs(residual)/abs(input_energy)),
            'power_architecture_verified':False}
    np.savez_compressed(a.out/'trace.npz',time_s=time,battery_V=vb,input_V=vi,rail_V=rail,bus_V=bus,
                        battery_current_A=-ib,converter_current_A=il,load_current_A=load)
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
