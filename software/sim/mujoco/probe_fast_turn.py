#!/usr/bin/env python3
"""Unassisted r9 turn development probe; records failures, never acceptance by itself."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import mujoco
import teleop_yaw as teleop
from fast_turn_reference import FastTurnReference
from stackchan_rl.yaw_kinematics import YawLegKinematics
from stackchan_rl.walk_events import WalkEventTracker
from stackchan_rl.config import DEFAULT


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--rate-deg-s',type=float,default=37.5)
    p.add_argument('--period',type=float,default=.4)
    p.add_argument('--inset-mm',type=float,default=22)
    p.add_argument('--initial-inset-mm',type=float,default=24.)
    p.add_argument('--shift-fraction',type=float,default=.25)
    p.add_argument('--duration',type=float,default=7)
    p.add_argument('--stop-after-s',type=float,default=0,help='seconds after the turn command; zero keeps turning')
    p.add_argument('--heading-goal-deg',type=float,default=None,help='finite reference angle; measured outcome is scored against 90 degrees')
    p.add_argument('--mass-scale',type=float,default=1.)
    p.add_argument('--friction',type=float,default=None)
    a=p.parse_args()
    if a.out.exists():p.error('new output required')
    if not np.isfinite(a.mass_scale) or a.mass_scale<=0 or (a.friction is not None and (not np.isfinite(a.friction) or a.friction<=0)):
        p.error('positive finite mass scale and friction required')
    class Reference(FastTurnReference):
        initial_inset_mm=a.initial_inset_mm
        heading_goal_rad=None if a.heading_goal_deg is None else np.deg2rad(a.heading_goal_deg)
        def __init__(self,*args):
            args=list(args);args[5]=a.shift_fraction;args[6]=a.inset_mm;args[7]=a.period;args[8]=a.period;args[10]=None
            super().__init__(*args)
        def set_command(self,name,t):
            if self.heading_goal_rad is not None and abs(self.heading-self.heading_goal_rad)<1e-8:name='stop'
            vx,wz=teleop.COMMANDS[name]
            self.protocol['segments'][0].update(vx_m_s=vx,yaw_rate_rad_s=wz)
            if self.mode=='stand' and (vx or wz):self.end=t
    class Kinematics(YawLegKinematics):
        def __init__(self,legacy,axes,limits):super().__init__(legacy,axes,(-.245,.245))
    teleop.LiveReference=Reference;teleop.YawLegKinematics=Kinematics
    teleop.COMMANDS['left']=(0,np.deg2rad(a.rate_deg_s))
    sim=teleop.Simulation(a.design/'reference',a.design)
    # Change only the plant; the controller retains nominal mass/feedforward.
    if a.mass_scale!=1. or a.friction is not None:
        initial_q=sim.d.qpos.copy();initial_v=sim.d.qvel.copy()
        sim.m.body_mass[:]*=a.mass_scale;sim.m.body_inertia[:]*=a.mass_scale
        if a.friction is not None:sim.m.geom_friction[:,0]=a.friction
        mujoco.mj_setConst(sim.m,sim.d)
        sim.d.qpos[:]=initial_q;sim.d.qvel[:]=initial_v
        mujoco.mj_forward(sim.m,sim.d)
    # Mirror the first support foot with turn direction, as well as yaw signs.
    if a.rate_deg_s<0:sim.reference.stance=1
    tracker=WalkEventTracker(sim.m.opt.timestep,DEFAULT['env'])
    contacts=[];landings=[]
    def observe(s):
        heights=np.array([s.d.geom_xpos[g,2]-np.abs(s.d.geom_xmat[g].reshape(3,3)[2])@s.m.geom_size[g] for g in s.plant.soles])
        moving=s.command!='stop'
        events=tracker.update(s.plant.loads>.35,heights,s.d.geom_xpos[s.plant.soles,:2],float(s.d.xpos[s.plant.base,0]),moving)
        for foot in events['valid_landing_feet']:landings.append([float(s.d.time),int(foot)])
        contacts.append([float(s.d.time),*s.plant.loads,*heights,*tracker.counts])
    sim.physics_observer=observe
    rows=[];yaw0=None;first90=None
    for i in range(int(a.duration/.02)):
        command='stop' if a.stop_after_s>0 and sim.d.time>=2+a.stop_after_s-1e-8 else 'left'
        sim.step(command)
        q=sim.d.qpos[:7];w,x,y,z=q[3:7]
        yaw=float(np.arctan2(2*(w*z+x*y),1-2*(y*y+z*z)))
        t=float(sim.d.time)
        if yaw0 is None and t>=2:yaw0=yaw
        angle=0 if yaw0 is None else float(np.rad2deg(np.arctan2(np.sin(yaw-yaw0),np.cos(yaw-yaw0))))
        if first90 is None and abs(angle)>=90:first90=t-2
        rows.append((t,sim.d.qpos.copy(),sim.d.qvel.copy(),angle,sim.plant.loads.copy()))
        if sim.failure:break
    a.out.mkdir(parents=True)
    np.savez_compressed(a.out/'states.npz',time=[r[0] for r in rows],qpos=[r[1] for r in rows],
                        qvel=[r[2] for r in rows],yaw_deg=[r[3] for r in rows],loads=[r[4] for r in rows])
    np.savez_compressed(a.out/'contact_trace.npz',trace=contacts,landings=np.array(landings).reshape(-1,2))
    report={'scope':__doc__,'duration_s':rows[-1][0],'failure':sim.failure,
            'final_penetrations':[{'pair':[sim.m.geom(c.geom1).name,sim.m.geom(c.geom2).name],
                                   'depth_mm':float(-1000*c.dist)} for c in sim.d.contact
                                  if c.dist<0 and 'floor' not in [sim.m.geom(c.geom1).name,sim.m.geom(c.geom2).name]],
            'first_90_deg_time_s':first90,'final_yaw_deg':rows[-1][3],
            'qualified_landings':tracker.counts.tolist(),'landing_events':landings,
            'last_second_yaw_range_deg':[min(r[3] for r in rows if r[0]>=rows[-1][0]-1),max(r[3] for r in rows if r[0]>=rows[-1][0]-1)],
            'settings':{k:str(v) if isinstance(v,Path) else v for k,v in vars(a).items()},
            'limitations':['development trial only; final heading tolerance and stability not yet acceptance-scored'],
            'source_sha256':{str(path):hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in [Path(__file__),Path('fast_turn_reference.py'),Path('teleop_yaw.py'),a.design/'models/scene.xml']}}
    (a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
