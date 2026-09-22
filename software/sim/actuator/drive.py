"""Endpoint-fitted current-position servo with explicit dissipative power flow.

The electrical port is quasi-static: internal current-loop dynamics are an
identified-later first-order approximation, not a winding inductance claim.
Only energized operation at the constructor voltage is represented. Torque-off,
brownout and disconnected-bus commutation require a different electrical model.
"""
from pathlib import Path
import json
import sys
import numpy as np

SIM=Path(__file__).resolve().parents[1]/'mujoco'
sys.path.insert(0,str(SIM))
from stackchan_rl.actuation import PostSlewLowPassBank

CATALOG=json.loads((Path(__file__).with_name('catalog.json')).read_text())


class CurrentPositionBank:
    def __init__(self, names, motor, dt=.001, slew=6., lowpass=.04, voltage=5.,
                 delay_s=.010, current_tau=.002, backlash=.004363323129985824,
                 thermal_capacity=15., thermal_resistance=15., ambient=25.):
        numeric=[dt,slew,voltage,current_tau,thermal_capacity,thermal_resistance,ambient,delay_s,lowpass,backlash]
        if not np.isfinite(numeric).all() or min(dt,slew,current_tau,thermal_capacity,thermal_resistance)<=0 or min(delay_s,lowpass,backlash)<0:
            raise ValueError('invalid actuator model parameters')
        self.names=list(names);self.dt=dt;self._voltage=voltage
        self.current_alpha=-np.expm1(-dt/current_tau);self.backlash=backlash
        self.C=thermal_capacity;self.Rth=thermal_resistance;self.ambient=ambient
        specs=[CATALOG['models'][name] for name in names]
        if any(not s['voltage_V'][0]<=voltage<=s['voltage_V'][-1] for s in specs):
            raise ValueError('voltage outside datasheet range')
        def interp(field):return np.array([np.interp(voltage,s['voltage_V'],s[field]) for s in specs])
        self.stall=interp('stall_torque_Nm');self.stall_current=interp('stall_current_A')
        self.omega=interp('no_load_speed_rpm')*np.pi/30
        self.resistance=voltage/self.stall_current
        self.K=voltage/self.omega
        self.eta=self.stall/(self.K*self.stall_current)
        if not np.all((self.eta>0)&(self.eta<=1)):raise ValueError('nonphysical endpoint fit')
        self.idle=np.array([s['standby_current_A'] for s in specs])
        self.ilimit=np.array([s['analysis_current_limit_A'] for s in specs])
        self.cap=np.minimum(np.array([s['analysis_torque_limit_Nm'] for s in specs]),motor['cap'])
        params={k:np.asarray(v).copy() for k,v in motor.items()}
        params['delay_s']=np.full(len(names),delay_s)
        self.kp=params['kp'];self.kd=params['kd']
        self.filter=PostSlewLowPassBank(params,dt,slew,lowpass)
        self.reset(np.zeros(len(names)))

    @property
    def voltage(self):
        """Fixed operating point used to fit resistance, back EMF and limits."""
        return self._voltage

    @property
    def filtered(self):return self.filter.filtered

    def reset(self,target,strength=1.):
        self.filter.reset(target,strength)
        self.current=np.zeros(len(self.names));self.temperature=np.full(len(self.names),float(self.ambient))
        self.telemetry={}

    def step(self,q,qd,target,*,power_state="energized"):
        if power_state != "energized":
            raise NotImplementedError("Only energized fixed-voltage operation is modeled; "
                                      "torque-off, brownout and bus disconnection need commutation/energy models")
        q=np.asarray(q);qd=np.asarray(qd);target=np.asarray(target)
        if q.shape!=(len(self.names),) or qd.shape!=q.shape or target.shape!=q.shape or not np.isfinite([q,qd,target]).all():
            raise ValueError('finite joint arrays required')
        self.filter.step(q,qd,target)
        resolution=2*np.pi/CATALOG['mode']['position_counts_per_revolution']
        reference=np.round(self.filter.delayed/resolution)*resolution
        measured=np.round(q/resolution)*resolution
        speed_quantum=CATALOG['mode']['velocity_quantum_rpm']*np.pi/30
        measured_speed=np.round(qd/speed_quantum)*speed_quantum
        error=reference-measured
        error=np.sign(error)*np.maximum(abs(error)-self.backlash/2,0)
        request=self.kp*error-self.kd*measured_speed
        # Motoring: output power eta*air-gap power. Regeneration: air-gap
        # power eta*negative output power. Both directions dissipate heat.
        kt=np.where(request*qd>=0,self.eta*self.K,self.K/self.eta)
        goal=request/kt
        quantum=CATALOG['mode']['current_quantum_A']
        goal=np.round(goal/quantum)*quantum
        limit=np.minimum(self.ilimit,self.cap*self.filter.strength/kt)
        goal=np.clip(goal,-limit,limit)
        self.current+=self.current_alpha*(goal-self.current)
        # Respect available bridge voltage as speed changes.
        lower=(-self.voltage-self.K*qd)/self.resistance
        upper=( self.voltage-self.K*qd)/self.resistance
        low=np.maximum(-limit,lower);high=np.minimum(limit,upper)
        if np.any(low>high):raise ValueError('back EMF exceeds current-limited bridge feasibility')
        self.current=np.clip(self.current,low,high)
        kt_actual=np.where(self.current*qd>=0,self.eta*self.K,self.K/self.eta)
        # Current lag can cross the motoring boundary; enforce the torque cap
        # with the actual sign, not just the requested sign.
        actual_limit=np.minimum(self.ilimit,self.cap*self.filter.strength/kt_actual)
        low=np.maximum(-actual_limit,lower);high=np.minimum(actual_limit,upper)
        if np.any(low>high):raise ValueError('regeneration exceeds bridge feasibility')
        self.current=np.clip(self.current,low,high)
        torque=kt_actual*self.current
        terminal=self.resistance*self.current+self.K*qd
        copper=self.resistance*self.current**2
        airgap=self.K*qd*self.current
        mechanical=torque*qd
        gear_loss=airgap-mechanical
        idle=self.voltage*self.idle
        loss=copper+gear_loss+idle
        supply_power=terminal*self.current+idle
        self.temperature+=self.dt*(loss-(self.temperature-self.ambient)/self.Rth)/self.C
        bound=np.minimum(self.cap*self.filter.strength,kt_actual*np.minimum(self.ilimit,
                     np.where(request*qd>=0,np.maximum(0,(self.voltage-abs(self.K*qd))/self.resistance),self.ilimit)))
        self.telemetry={'joint_position_rad':q.copy(),'angular_velocity_rad_s':qd.copy(),
                        'requested_torque_Nm':request.copy(),'reference_rad':reference,
                        'motor_current_A':self.current.copy(),'motor_terminal_V':terminal,
                        'torque_Nm':torque,'mechanical_power_W':mechanical,
                        'copper_loss_W':copper,'gear_loss_W':gear_loss,'idle_loss_W':idle,
                        'supply_power_W':supply_power,'supply_current_A':supply_power/self.voltage,
                        'case_temperature_C':self.temperature.copy(),
                        'tracking_error_rad':reference-q}
        return torque,abs(request)>bound+1e-10,bound
