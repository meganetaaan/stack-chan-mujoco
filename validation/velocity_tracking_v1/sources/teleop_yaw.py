#!/usr/bin/env python3
"""WASD control of the r9 floating-base robot (optional legacy r8 profile)."""
import argparse
import importlib.util
import importlib
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import mujoco
from yaw_maneuver_reference import YawCommandReference
from live_fast_turn_reference import LiveFastTurnReference
from velocity_control import VelocityControl, keyboard_velocity
from generate_yaw_zero_reference import configure_candidate_mass
from stackchan_rl.yaw_kinematics import YawLegKinematics
from stackchan_rl.residual import runtime_xml, ResidualEnv
from stackchan_rl.actuation import PostSlewLowPassBank
from probe_yaw_dynamics_candidate import JointProtection

ROOT=Path(__file__).resolve().parent
COMMANDS={'stop':(0.,0.),'forward':(.10,0.),'backward':(-.05,0.),
          'left':(0.,np.pi/20),'right':(0.,-np.pi/20)}


class LiveReference(YawCommandReference):
    def set_command(self, name, t):
        vx,wz=COMMANDS[name]
        self.protocol['segments'][0].update(vx_m_s=vx,yaw_rate_rad_s=wz)
        # Wake a settled stand; an airborne foot completes its current step.
        if self.mode=='stand' and (vx or wz):self.end=t


def requested_command(pressed):
    if 'SPACE' in pressed:return 'stop'
    if 'W' in pressed and 'S' not in pressed:return 'forward'
    if 'S' in pressed and 'W' not in pressed:return 'backward'
    if 'A' in pressed and 'D' not in pressed:return 'left'
    if 'D' in pressed and 'A' not in pressed:return 'right'
    return 'stop'


def advance_reusing_forward(model, data):
    # Every previous tick ends with mj_forward; ctrl is the only changed input.
    # Reuse its position/velocity stages, retaining MuJoCo's state checks.
    mujoco.mj_checkPos(model,data)
    mujoco.mj_checkVel(model,data)
    mujoco.mj_step2(model,data)


class Simulation:
    def __init__(self, cad_design, design, *, fast_turn=False):
        src=cad_design/'src'
        if not (src/'tab5_biped/planner.py').exists():
            raise FileNotFoundError(f'{src}/tab5_biped/planner.py missing; see docs/REPRODUCE_MOUNTED_ja.md or --cad-design')
        # Keep model-specific geometry and mutable feedforward inertials isolated.
        package=f'_teleop_reference_{id(self)}'
        spec=importlib.util.spec_from_file_location(package,src/'tab5_biped/__init__.py',
                                                   submodule_search_locations=[str(src/'tab5_biped')])
        module=importlib.util.module_from_spec(spec)
        sys.modules[package]=module
        try:
            spec.loader.exec_module(module)
            core=importlib.import_module(package+'.core')
            legacy=importlib.import_module(package+'.planner')
        finally:
            for name in list(sys.modules):
                if name==package or name.startswith(package+'.'):del sys.modules[name]
        self.legacy=legacy
        robot=json.loads((design/'robot.json').read_text())
        configure_candidate_mass(legacy,json.loads((design/'models/inertials.json').read_text()),robot)
        initial=legacy.Planner(steps=1)
        initial.q0,initial.b0,_=legacy.pose(initial.initial_feet,initial.initial_feet.mean(axis=0)[:2],(initial.q0,initial.b0),initial.b0[2,3]+.002)
        protocol=json.loads((ROOT/'configs/maneuver/acceptance_v1.json').read_text())
        for segment in protocol['segments']:segment.update(vx_m_s=0.,yaw_rate_rad_s=0.)
        kin=YawLegKinematics(core,robot['hip_yaw_candidate']['axis_base_m'],(-.245,.245) if fast_turn else (-.075,.075))
        if fast_turn:
            self.reference=LiveFastTurnReference(initial,legacy.pose,core.smooth,protocol,kin)
        else:
            self.reference=LiveReference(initial,legacy.pose,core.smooth,protocol,kin,.25,25.9,.32,.30,'quartic',62.,.1,.22)
        self.reference.boundaries=np.array([0.,np.inf])
        self.reference.end=np.inf
        self.m=mujoco.MjModel.from_xml_string(runtime_xml(design/'models/scene.xml',visuals=True))
        self.m.opt.timestep=.001
        self.d=mujoco.MjData(self.m)
        names=[x['name'] for x in json.loads((design/'models/joint_map.json').read_text())]
        self.qadr=np.array([self.m.joint(n).qposadr[0] for n in names])
        self.vadr=np.array([self.m.joint(n).dofadr[0] for n in names])
        self.aids=np.array([self.m.actuator(n+'_motor').id for n in names])
        self.limits=np.array([self.m.joint(n).range for n in names])
        self.old=np.array([i for i,n in enumerate(names) if not n.endswith('hip_yaw')])
        specs=[]
        for n in names:
            s=dict(robot['motor'])
            if n.split('_',1)[1] in robot['motor_overrides']['joint_types']:s.update(robot['motor_overrides'])
            specs.append(s)
        fields={'cap':'simulation_torque_cap_Nm','stall':'stall_torque_Nm','kp':'kp_Nm_rad','kd':'kd_Nm_s_rad','delay_s':'command_delay_s'}
        motor={k:np.array([s[v] for s in specs]) for k,v in fields.items()}
        motor['omega']=np.array([s['no_load_speed_rpm']*np.pi/30 for s in specs])
        yaw=[i for i,n in enumerate(names) if n.endswith('hip_yaw')]
        motor['kp'][yaw]=6.;motor['kd'][yaw]=.13
        self.motor=motor
        cfg=json.loads((ROOT/'policies/r6_mounted_seed20260924/config.json').read_text())
        self.bank=PostSlewLowPassBank(motor,.001,cfg['slew_rad_s'],cfg['lowpass_s'])
        self.protection=JointProtection(.001,cfg['protection'],12)
        sample=self.reference.sample(0.)
        mujoco.mj_resetDataKeyframe(self.m,self.d,0)
        self.d.qpos[:3]=sample.base[:3,3];self.d.qpos[2]+=.0005
        self.d.qpos[self.qadr]=sample.q12
        mujoco.mj_forward(self.m,self.d);self.bank.reset(sample.q12)
        self.plant=SimpleNamespace(model=self.m,data=self.d,qadr=self.qadr,limits=self.limits,base=self.m.body('base').id,
            floor=self.m.geom('floor').id,soles=np.array([self.m.geom('col_'+s+'_sole_TPU_0').id for s in ['left','right']]),
            warnings=np.array([w.number for w in self.d.warning]),loads=np.zeros(2),force=np.zeros(6))
        if self.m.opt.integrator!=mujoco.mjtIntegrator.mjINT_IMPLICITFAST:
            raise ValueError('interactive fast path requires the implicitfast integrator')
        self.advance=advance_reusing_forward
        self.failure=None;self.command='stop';self.tick=0
        self.physics_observer=None
        self.velocity=VelocityControl() if fast_turn else None
        self.velocity_buffer=np.zeros(6)

    def step(self, command):
        if self.failure:return
        t=self.tick*.02
        self.command=command if t>=2. else 'stop'
        try:
            if self.velocity is not None and not isinstance(command,str):
                R=self.d.xmat[self.plant.base].reshape(3,3)
                tilt=np.rad2deg(np.arccos(np.clip(R[2,2],-1,1)))
                self.velocity.observe_support(tilt,self.plant.loads)
                drive=self.velocity.update(command,ready=t>=2.)
                self.reference.set_command(drive,t)
                self.command='velocity'
            else:
                self.reference.set_command(self.command,t)
            sample=self.reference.sample(t)
            tau,_=self.legacy.static_torques(sample.q,sample.base,sample.support)
            target=sample.q12.copy();target[self.old]+=tau/self.motor['kp'][self.old]
            target=np.clip(target,self.limits[:,0]+.015,self.limits[:,1]-.015)
            for _ in range(20):
                torque,sat,_=self.bank.step(self.d.qpos[self.qadr],self.d.qvel[self.vadr],target)
                self.d.ctrl[self.aids]=torque
                self.advance(self.m,self.d);mujoco.mj_forward(self.m,self.d)
                self.failure=ResidualEnv._check_physics(self.plant) or self.protection.update(sat)
                if self.physics_observer is not None:self.physics_observer(self)
                if self.failure:break
            if self.velocity is not None:
                mujoco.mj_objectVelocity(self.m,self.d,mujoco.mjtObj.mjOBJ_BODY,self.plant.base,self.velocity_buffer,0)
                R=self.d.xmat[self.plant.base].reshape(3,3)
                yaw=np.arctan2(R[1,0],R[0,0]);c,s=np.cos(yaw),np.sin(yaw)
                vx,vy=self.velocity_buffer[3:5]
                self.velocity.observe([c*vx+s*vy,-s*vx+c*vy,self.velocity_buffer[2]])
            self.tick+=1
        except ValueError as exc:self.failure='planning: '+str(exc)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',choices=['r9','r8'],default='r9',help='r9 fast turn (default), or legacy r8')
    p.add_argument('--cad-design',type=Path,help='numeric reference source (normally selected with model)')
    p.add_argument('--design',type=Path,help='model directory (normally selected with profile)')
    p.add_argument('--headless',action='store_true',help='run a 24 s command-switch smoke test without a window')
    p.add_argument('--fps',type=float,default=30.,help='maximum drawing rate; physics remains 1000 Hz')
    p.add_argument('--duration',type=float,default=0.,help='exit after this many simulation seconds (0: unlimited)')
    p.add_argument('--demo',action='store_true',help='automatic movement sequence for performance checks')
    p.add_argument('--frames',type=int,default=0,help='close after this many GUI frames (0: unlimited)')
    p.add_argument('--capture',type=Path,help='save the last GUI frame as PNG')
    a=p.parse_args()
    if not np.isfinite(a.fps) or not 1<=a.fps<=120:p.error('--fps must be within 1..120')
    if not np.isfinite(a.duration) or a.duration<0:p.error('--duration must be finite and nonnegative')
    if a.design is None:a.design=ROOT/'assets'/('r9_fast_turn_v1' if a.profile=='r9' else 'r8_yaw_offset_flange_v1')
    if a.cad_design is None:a.cad_design=a.design/'reference' if a.profile=='r9' else ROOT/'design/teleop_reference'
    sim=Simulation(a.cad_design,a.design,fast_turn=a.profile=='r9')
    if a.headless:
        sequence=['stop','forward','stop','backward','left','right','stop']
        for i in range(1200):
            name=sequence[min(i//175,len(sequence)-1)]
            cmd=LiveFastTurnReference.commands[name] if a.profile=='r9' else name
            sim.step(cmd)
            if sim.failure:break
        print(json.dumps({'time_s':sim.d.time,'failure':sim.failure,'position':sim.d.qpos[:3].tolist()}))
        if sim.failure:raise SystemExit(1)
        return
    import glfw
    if not glfw.init():raise RuntimeError('GLFW initialization failed; a desktop display is required')
    window=glfw.create_window(1000,750,f'Tab5 {a.profile} - WASD move | release/Space stop | R reset | Esc quit',None,None)
    if not window:glfw.terminate();raise RuntimeError('Unable to create an OpenGL window')
    glfw.make_context_current(window);glfw.swap_interval(0)
    camera=mujoco.MjvCamera();camera.distance=.65;camera.azimuth=135;camera.elevation=-20
    scene=mujoco.MjvScene(sim.m,maxgeom=10000);context=mujoco.MjrContext(sim.m,mujoco.mjtFontScale.mjFONTSCALE_150)
    option=mujoco.MjvOption();option.geomgroup[3]=0
    glfw.set_scroll_callback(window,lambda w,x,y:setattr(camera,'distance',float(np.clip(camera.distance*np.exp(-.1*y),.2,5))))
    reset_down=False;last_mouse=None;frames=0
    start_wall=time.monotonic();deadline=start_wall;next_draw=start_wall
    rate_wall=start_wall;rate_sim=0.;rate=1.
    try:
        while not glfw.window_should_close(window):
            glfw.poll_events()
            if glfw.get_key(window,glfw.KEY_ESCAPE)==glfw.PRESS:break
            reset=glfw.get_key(window,glfw.KEY_R)==glfw.PRESS
            if reset and not reset_down:
                sim=Simulation(a.cad_design,a.design,fast_turn=a.profile=='r9')
                deadline=time.monotonic();rate_wall=deadline;rate_sim=0.
            reset_down=reset
            pressed={k for k in ['W','A','S','D','SPACE'] if glfw.get_key(window,getattr(glfw,'KEY_'+k))==glfw.PRESS}
            if not glfw.get_window_attrib(window,glfw.FOCUSED):pressed=set()
            command=keyboard_velocity(pressed) if a.profile=='r9' else requested_command(pressed)
            if a.demo:
                if a.profile=='r9':
                    command=[(0.,0.),(.025,.21),(-.012,.21),(-.012,-.21),(.025,-.21),(0.,-.55),(0.,0.)][min(int(sim.d.time/3.5),6)]
                else:command=['stop','forward','stop','backward','left','right','stop'][min(int(sim.d.time/3.5),6)]
            sim.step(command)
            now=time.monotonic()
            if now-rate_wall>=.5:
                rate=(sim.d.time-rate_sim)/(now-rate_wall);rate_wall=now;rate_sim=sim.d.time
            mouse=glfw.get_cursor_pos(window)
            if last_mouse and glfw.get_mouse_button(window,glfw.MOUSE_BUTTON_LEFT)==glfw.PRESS:
                camera.azimuth+=(mouse[0]-last_mouse[0])*.3;camera.elevation=float(np.clip(camera.elevation+(mouse[1]-last_mouse[1])*.3,-89,0))
            last_mouse=mouse
            camera.lookat[:]=sim.d.xpos[sim.plant.base]
            width,height=glfw.get_framebuffer_size(window)
            if width and height and now>=next_draw:
                next_draw=now+1/a.fps
                viewport=mujoco.MjrRect(0,0,width,height)
                mujoco.mjv_updateScene(sim.m,sim.d,option,None,camera,mujoco.mjtCatBit.mjCAT_ALL,scene)
                mujoco.mjr_render(viewport,scene,context)
                velocity_text=''
                if sim.velocity is not None:
                    ctl=sim.velocity
                    velocity_text='\nRequest / Target / Measured (m/s, deg/s)'
                    for label,val in [('Req',ctl.request),('Tgt',ctl.target),('Meas',ctl.measured)]:
                        velocity_text+=f'\n{label}: {val[0]:+.3f}, {np.rad2deg(val[1]):+.1f}'
                    velocity_text+=f'\n{ctl.reason or "within envelope"}'
                status=('STOPPED: '+sim.failure+' (R reset)') if sim.failure else sim.command
                mujoco.mjr_overlay(mujoco.mjtFontScale.mjFONTSCALE_150,mujoco.mjtGridPos.mjGRID_TOPLEFT,viewport,
                    'W/S forward/back + A/D turn\nRelease / Space: stop | R: reset\nDrag: orbit | Wheel: zoom',f'{a.profile}: {status}\nSimulation: {sim.d.time:.2f} s\nSpeed: {rate:.2f}x (target 1.00x){velocity_text}',context)
                frames+=1
                if a.capture and a.frames and frames>=a.frames:
                    from PIL import Image
                    pixels=np.empty((height,width,3),dtype=np.uint8)
                    mujoco.mjr_readPixels(pixels,None,viewport,context)
                    a.capture.parent.mkdir(parents=True,exist_ok=True)
                    Image.fromarray(pixels[::-1]).save(a.capture)
                glfw.swap_buffers(window)
                if a.frames and frames>=a.frames:break
            if a.duration and sim.d.time>=a.duration-1e-9:break
            deadline+=.02
            # Bound backlog without skipping any physics steps.
            now=time.monotonic()
            if now-deadline>.1:deadline=now
            time.sleep(max(0.,deadline-now))
    finally:
        elapsed=time.monotonic()-start_wall
        print(json.dumps({'simulation_s':float(sim.d.time),'wall_s':elapsed,'speed':float(sim.d.time)/elapsed,'failure':sim.failure}),flush=True)
        context.free();glfw.destroy_window(window);glfw.terminate()


if __name__=='__main__':main()
