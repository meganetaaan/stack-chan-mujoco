"""R6 residual RL with a kinematic prior; only torque drives the floating base.

Separate interface from R5 policies. The prior is joint targets, never simulator
state. Every physics step checks contact, joint limits and sustained saturation.
Sensor ranges and protective thresholds are assumptions, not hardware ratings.
"""
from __future__ import annotations
from collections import deque
import gzip
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import gymnasium as gym
import mujoco
import numpy as np
from .actuation import PostSlewLowPassBank
from .spec import JOINT_NAMES
from .walk_events import WalkEventTracker
from .config import DEFAULT

ROOT = Path(__file__).resolve().parents[1]
STATE_SPEC = mujoco.mjtState.mjSTATE_INTEGRATION
OBS_FIELDS = [('reference_q',10),('q_minus_reference',10),('joint_velocity_div10',10),
              ('noisy_projected_gravity',3),('noisy_gyro_div10',3),('body_velocity',3),
              ('previous_action',10),('filtered_minus_reference',10),('command',1),
              ('phase_sin_cos',2),('planned_support',2),('height_error',1)]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def runtime_xml(xml_path, visuals=False):
    root = ET.parse(xml_path).getroot()
    compiler = root.find('compiler')
    compiler.set('meshdir',str((xml_path.parent/compiler.get('meshdir','.')).resolve()))
    if not visuals:
        for body in root.findall('.//body'):
            for g in list(body.findall('geom')):
                if g.get('name','').startswith('vis_'):
                    if any(g.get(k) != '0' for k in ('contype','conaffinity','mass')):
                        raise ValueError('visual geom contributes to physics')
                    body.remove(g)
        used = {g.get('mesh') for g in root.findall('.//geom') if g.get('mesh')}
        asset = root.find('asset')
        for mesh in list(asset.findall('mesh')):
            if mesh.get('name') not in used:
                asset.remove(mesh)
    return ET.tostring(root,encoding='unicode')


class SaturationProtection:
    def __init__(self,dt,cfg):
        self.dt=dt
        self.continuous_limit=cfg['continuous_saturation_s']
        self.window_ticks=round(cfg['saturation_window_s']/dt)
        self.duty_limit=cfg['saturation_duty_limit']
        if self.continuous_limit<=0 or self.window_ticks<1 or not 0<self.duty_limit<=1:
            raise ValueError('invalid saturation protection')
        self.streak=np.zeros(10,dtype=int)
        self.peak_streak=np.zeros(10,dtype=int)
        self.window=deque()
        self.sum=np.zeros(10,dtype=int)
        self.peak_duty=np.zeros(10)

    def update(self,saturated):
        a=np.asarray(saturated,dtype=bool)
        self.streak=np.where(a,self.streak+1,0)
        self.peak_streak=np.maximum(self.peak_streak,self.streak)
        if len(self.window)==self.window_ticks:
            self.sum-=self.window.popleft()
        self.window.append(a.copy());self.sum+=a
        if np.any(self.streak*self.dt>=self.continuous_limit-1e-12):
            return 'continuous_saturation'
        if len(self.window)==self.window_ticks:
            duty=self.sum/self.window_ticks
            self.peak_duty=np.maximum(self.peak_duty,duty)
            if np.any(duty>self.duty_limit):
                return 'saturation_duty'
        return None


class ResidualEnv(gym.Env):
    metadata={'render_modes':[]}
    def __init__(self,config,*,visuals=False,record=False):
        super().__init__()
        self.cfg=json.loads(json.dumps(config))
        if config['schema']!='r6-residual-v1' or config['command_m_s']!=0.1:
            raise ValueError('this reference interface is defined only for 0.10 m/s')
        self.design=ROOT/config['design'];self.xml_path=self.design/'models/scene.xml'
        self.robot=json.loads((self.design/'robot.json').read_text())
        if not self.robot['revision'].startswith('r6-experimental-hip-22mm-'):
            raise ValueError('requires explicitly reviewed R6 design')
        ref_path=ROOT/config['reference']
        with gzip.open(ref_path,'rt') as f:self.reference=json.load(f)
        self.ref_q=np.asarray([x['q'] for x in self.reference])
        self.ref_tau=np.asarray([x['quasistatic_torque_Nm'] for x in self.reference])
        self.ref_support=np.asarray([x['support'] for x in self.reference])
        self.ref_base=np.asarray([x['base'] for x in self.reference])
        self.ref_times=np.asarray([x['time_s'] for x in self.reference])
        self.dt=float(config['policy_dt_s'])
        if not np.allclose(np.diff(self.ref_times),self.dt,rtol=0,atol=1e-10):
            raise ValueError('reference and control period differ')
        if not 0 < config['episode_s'] <= self.ref_times[-1]:
            raise ValueError('episode must fit reference')
        self.model=mujoco.MjModel.from_xml_string(runtime_xml(self.xml_path,visuals))
        self.data=mujoco.MjData(self.model)
        m=self.model
        if (m.nq,m.nv,m.nu)!=(17,16,10) or m.neq or np.any(m.body_gravcomp):
            raise ValueError('expected unassisted ten-joint floating robot')
        if not np.allclose(m.opt.gravity,[0,0,-9.81]):raise ValueError('gravity must remain enabled')
        self.substeps=round(self.dt/m.opt.timestep)
        if not np.isclose(self.substeps*m.opt.timestep,self.dt):raise ValueError('nonintegral control period')
        self.qadr=np.array([m.joint(n).qposadr[0] for n in JOINT_NAMES])
        self.vadr=np.array([m.joint(n).dofadr[0] for n in JOINT_NAMES])
        self.aids=np.array([m.actuator(n+'_motor').id for n in JOINT_NAMES])
        self.limits=np.array([m.joint(n).range for n in JOINT_NAMES])
        self.base=m.body('base').id;self.floor=m.geom('floor').id
        self.soles=np.array([m.geom('col_'+s+'_sole_TPU_0').id for s in ('left','right')])
        specs=[]
        for n in JOINT_NAMES:
            spec=dict(self.robot['motor']);over=self.robot['motor_overrides']
            if n.split('_',1)[1] in over['joint_types']:spec.update(over)
            specs.append(spec)
        fields={'cap':'simulation_torque_cap_Nm','stall':'stall_torque_Nm','kp':'kp_Nm_rad',
                'kd':'kd_Nm_s_rad','delay_s':'command_delay_s'}
        self.nominal_motor={k:np.array([s[f] for s in specs]) for k,f in fields.items()}
        self.nominal_motor['omega']=np.array([s['no_load_speed_rpm']*np.pi/30 for s in specs])
        self.nominal={name:getattr(m,name).copy() for name in ('body_mass','body_inertia','body_ipos',
                    'geom_friction','actuator_ctrlrange','actuator_forcerange')}
        for name in ('ctrlrange','forcerange'):
            if not np.allclose(getattr(m,'actuator_'+name)[self.aids],
                               np.stack([-self.nominal_motor['cap'],self.nominal_motor['cap']],axis=1)):
                raise ValueError('XML motor cap mismatch')
        self.action_space=gym.spaces.Box(-1.,1.,(10,),np.float32)
        self.observation_space=gym.spaces.Box(-np.inf,np.inf,(sum(n for _,n in OBS_FIELDS),),np.float32)
        self.record=record
        self.fingerprint={'schema':config['schema'],'model_sha256':sha(self.xml_path),
            'robot_sha256':sha(self.design/'robot.json'),'reference_sha256':sha(ref_path),
            'source_sha256':{p:sha(ROOT/p) for p in ('stackchan_rl/residual.py','stackchan_rl/actuation.py',
                            'stackchan_rl/walk_events.py','stackchan_rl/ordered_steps.py','stackchan_rl/config.py')},
            'observation_fields':OBS_FIELDS,'joint_order':list(JOINT_NAMES)}

    def reset(self,*,seed=None,options=None):
        super().reset(seed=seed)
        self.seed_used=seed;self.options=options or {}
        rng=self.np_random;c=self.cfg;m=self.model;d=self.data
        for name,value in self.nominal.items():getattr(m,name)[:]=value
        randomized=self.options.get('randomize',c['randomize'])
        ranges=c['ranges']
        def draw(k):return float(rng.uniform(*ranges[k]))
        p={'mass_scale':1.,'base_com_shift_m':[0.,0.,0.],'friction':float(self.nominal['geom_friction'][self.floor,0]),
           'torque_scale':1.,'speed_scale':1.,'extra_delay_s':0.,**c['fixed_noise']}
        if randomized:
            for key in p:
                p[key]=rng.uniform(*ranges[key],size=3).tolist() if key=='base_com_shift_m' else draw(key)
            m.body_mass[:]*=p['mass_scale'];m.body_inertia[:]*=p['mass_scale']
            m.body_ipos[self.base]+=p['base_com_shift_m']
            m.geom_friction[:,0]=p['friction']
        motor={k:v.copy() for k,v in self.nominal_motor.items()}
        motor['cap']*=p['torque_scale'];motor['stall']*=p['torque_scale']
        motor['omega']*=p['speed_scale'];motor['delay_s']+=p['extra_delay_s']
        m.actuator_ctrlrange[self.aids]*=p['torque_scale'];m.actuator_forcerange[self.aids]*=p['torque_scale']
        mujoco.mj_setConst(m,d);mujoco.mj_resetDataKeyframe(m,d,m.key('home').id)
        d.qpos[:3]=self.ref_base[0,:3,3];d.qpos[2]+=.0005
        offsets=rng.uniform(-c['initial_joint_offset_rad'],c['initial_joint_offset_rad'],10) if randomized else np.zeros(10)
        d.qpos[self.qadr]=self.ref_q[0]+offsets
        mujoco.mj_forward(m,d)
        self.bank=PostSlewLowPassBank(motor,m.opt.timestep,c['slew_rad_s'],c['lowpass_s'])
        self.bank.reset(d.qpos[self.qadr])
        self.protection=SaturationProtection(m.opt.timestep,c['protection'])
        self.tracker=WalkEventTracker(float(m.opt.timestep),DEFAULT['env'])
        self.start=d.xpos[self.base].copy();self.previous_action=np.zeros(10)
        self.gyro_bias=rng.normal(0,p['gyro_bias_std_rad_s'],3)
        self.parameters={**p,'initial_joint_offsets_rad':offsets.tolist(),'gyro_bias_rad_s':self.gyro_bias.tolist(),
            'battery_included_total_mass_kg':float(m.body_mass.sum()),'initial_com_world_m':d.subtree_com[self.base].tolist(),
            'motor_caps_Nm':motor['cap'].tolist(),'motor_speeds_rad_s':motor['omega'].tolist(),
            'effective_delay_s':self.bank.delay_ticks*m.opt.timestep,'randomized':randomized}
        self.loads=np.zeros(2);self.force=np.zeros(6);self.failure=None;self.crossing_time=None
        self.i=0;self.sat_count=np.zeros(10,dtype=int);self.physics_steps=0
        self.states=[];self.actions=[];self.observations=[];self.torques=[]
        self.warnings=np.array([w.number for w in d.warning])
        self.vel_window=deque(maxlen=10)
        self.failure=self._check_physics()
        if self.record:self.states.append(self.get_state())
        obs=self._observation()
        if self.record:self.observations.append(obs.copy())
        return obs,self._info()

    def get_state(self):
        state=np.empty(mujoco.mj_stateSize(self.model,STATE_SPEC))
        mujoco.mj_getState(self.model,self.data,state,STATE_SPEC)
        return state

    def _observation(self):
        d=self.data;m=self.model;rng=self.np_random
        j=min(self.i,len(self.reference)-1);qref=self.ref_q[j]
        rot=d.xmat[self.base].reshape(3,3)
        vel=np.zeros(6);mujoco.mj_objectVelocity(m,d,mujoco.mjtObj.mjOBJ_BODY,self.base,vel,1)
        gravity=-rot[2].copy()+rng.normal(0,self.parameters['gravity_noise_std'],3)
        gravity/=np.linalg.norm(gravity)
        gyro=vel[:3]+self.gyro_bias+rng.normal(0,self.parameters['gyro_noise_std_rad_s'],3)
        phase=2*np.pi*max(0,d.time-1.)/.54
        obs=np.concatenate((qref,d.qpos[self.qadr]-qref,d.qvel[self.vadr]/10,gravity,gyro/10,
            vel[3:],self.previous_action,self.bank.filtered-qref,[self.cfg['command_m_s']],
            [np.sin(phase),np.cos(phase)],self.ref_support[j],[d.xpos[self.base,2]-self.start[2]]))
        return obs.astype(np.float32)

    def _check_physics(self):
        m=self.model;d=self.data
        if not np.isfinite(d.qpos).all() or not np.isfinite(d.qvel).all() or np.any(np.array([w.number for w in d.warning])>self.warnings):
            return 'invalid_physics'
        if np.any(d.qpos[self.qadr]<self.limits[:,0]-1e-5) or np.any(d.qpos[self.qadr]>self.limits[:,1]+1e-5):
            return 'joint_limit'
        if d.xmat[self.base].reshape(3,3)[2,2]<np.cos(np.deg2rad(35)):
            return 'fall'
        self.loads[:]=0
        for k in range(d.ncon):
            contact=d.contact[k];pair=(contact.geom1,contact.geom2)
            mujoco.mj_contactForce(m,d,k,self.force)
            force=float(np.linalg.norm(self.force[:3]))
            if self.floor in pair:
                other=pair[1] if pair[0]==self.floor else pair[0]
                ids=np.flatnonzero(self.soles==other)
                if len(ids):self.loads[ids[0]]+=abs((contact.frame.reshape(3,3).T@self.force[:3])[2])
                elif contact.dist < -1e-8 or force>1e-6:return 'nonsole_floor_contact'
            elif contact.dist < -1e-8 or force>1e-6:return 'self_collision'
        return None

    def step(self,action):
        action=np.asarray(action,dtype=float)
        if action.shape!=(10,) or not np.isfinite(action).all():raise ValueError('ten finite residual actions required')
        action=np.clip(action,-1,1)
        if self.i>=len(self.reference)-1:raise RuntimeError('reset required at end of reference')
        target=self.ref_q[self.i]+self.ref_tau[self.i]/self.nominal_motor['kp']+self.cfg['residual_scale_rad']*action
        target=np.clip(target,self.limits[:,0]+.015,self.limits[:,1]-.015)
        d=self.data;m=self.model;start_x=float(d.xpos[self.base,0]);tau=np.zeros(10)
        for _ in range(self.substeps):
            if self.failure:break
            tau,sat,bound=self.bank.step(d.qpos[self.qadr],d.qvel[self.vadr],target)
            d.ctrl[self.aids]=tau
            previous_time=d.time
            mujoco.mj_step(m,d);mujoco.mj_forward(m,d)
            self.physics_steps+=1;self.sat_count+=sat
            self.failure=self._check_physics()
            if d.time<=previous_time:self.failure=self.failure or 'invalid_physics_time'
            protection=self.protection.update(sat)
            self.failure=self.failure or protection
            heights=np.array([d.geom_xpos[gid,2]-np.abs(d.geom_xmat[gid].reshape(3,3)[2])@m.geom_size[gid] for gid in self.soles])
            events=self.tracker.update(self.loads>.35,heights,d.geom_xpos[self.soles,:2],
                                      float(d.xpos[self.base,0]-self.start[0]),d.time>=1.)
            if d.time>2. and events['no_step_elapsed_s']>1.:self.failure=self.failure or 'walking_interrupted'
            if self.crossing_time is None and d.xpos[self.base,0]-self.start[0]>=10.:
                self.crossing_time=float(d.time)
        vx=(d.xpos[self.base,0]-start_x)/self.dt
        self.vel_window.append(vx);vmean=float(np.mean(self.vel_window))
        desired=0. if d.time<1. else self.cfg['command_m_s']
        tracking=float(np.exp(-((vmean-desired)/.04)**2))
        reward=tracking-.05*float(np.mean(action**2))-.02*float(np.mean((action-self.previous_action)**2))
        reward-=2.*float(d.xpos[self.base,1]-self.start[1])**2
        if self.failure:reward-=10.
        self.i+=1;self.previous_action=action.copy()
        obs=self._observation()
        if self.record:
            self.states.append(self.get_state());self.actions.append(action.copy())
            self.observations.append(obs.copy());self.torques.append(tau.copy())
        terminated=self.failure is not None
        truncated=d.time>=self.cfg['episode_s']-1e-9 or self.i>=len(self.reference)-1
        return obs,reward,terminated,truncated,self._info()

    def _info(self):
        return {'failure':self.failure,'time_s':float(self.data.time),
            'forward_m':float(self.data.xpos[self.base,0]-self.start[0]),'crossing_time_s':self.crossing_time,
            'valid_landings':self.tracker.counts.tolist(),'parameters':self.parameters,
            'saturation_fraction':(self.sat_count/max(1,self.physics_steps)).tolist(),
            'peak_continuous_saturation_s':(self.protection.peak_streak*self.model.opt.timestep).tolist(),
            'peak_one_second_saturation_duty':self.protection.peak_duty.tolist()}

    def save_trajectory(self,path):
        if not self.record:raise ValueError('record=True required')
        np.savez_compressed(path,state=np.asarray(self.states),action=np.asarray(self.actions),
            observation=np.asarray(self.observations),last_substep_torque=np.asarray(self.torques),
            state_spec=int(STATE_SPEC),physics_dt=float(self.model.opt.timestep),
            parameters_json=json.dumps(self.parameters),fingerprint_json=json.dumps(self.fingerprint))
