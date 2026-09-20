"""Create an unassisted full-body load case using the preserved turn reference."""
from pathlib import Path
import sys
from unittest.mock import patch
import numpy as np

SIM=Path(__file__).resolve().parents[1]/'mujoco'
sys.path.insert(0,str(SIM))
import teleop_yaw
from fast_turn_reference import FastTurnReference
from stackchan_rl.yaw_kinematics import YawLegKinematics
from drive import CurrentPositionBank


def full_body(sign=1,drive_model="current",**parameters):
    class Reference(FastTurnReference):
        initial_inset_mm=25.5
        heading_goal_rad=sign*np.deg2rad(91.5)
        def __init__(self,*args):
            args=list(args);args[5:11]=[.45,25.5,.4,.4,'quartic',None]
            super().__init__(*args)
        def set_command(self,name,t):
            moving=name!='stop' and abs(self.heading-self.heading_goal_rad)>1e-8
            rate=sign*np.deg2rad(40) if moving else 0.
            self.protocol['segments'][0].update(vx_m_s=0.,yaw_rate_rad_s=rate)
            if self.mode=='stand' and moving:self.end=t
    class Kin(YawLegKinematics):
        def __init__(self,legacy,axes,limits):super().__init__(legacy,axes,(-.245,.245))
    model=SIM/'assets/r9_fast_turn_v1'
    with patch.object(teleop_yaw,'LiveReference',Reference),patch.object(teleop_yaw,'YawLegKinematics',Kin):
        sim=teleop_yaw.Simulation(model/'reference',model)
    names=[sim.m.joint(int(sim.m.actuator(a).trnid[0])).name for a in sim.aids]
    models=['XC330-M288-T' if n.split('_',1)[1] in ['hip_roll','knee','ankle_pitch'] else 'XL330-M288-T' for n in names]
    target=sim.bank.filtered.copy()
    if drive_model=="current":
        sim.bank=CurrentPositionBank(models,sim.motor,**parameters)
        sim.bank.reset(target)
    elif drive_model!="legacy":raise ValueError("unknown drive model")
    if sign<0:sim.reference.stance=1
    return sim,names
