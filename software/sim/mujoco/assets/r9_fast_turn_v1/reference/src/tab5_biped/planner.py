"""Slow straight-line walking REFERENCE, not a validated physical gait.
No root force, weld, adhesion or mocap assistance is used by the simulator.
"""
from __future__ import annotations
import json
from dataclasses import dataclass
import numpy as np
from .core import ROOT,PARAMS,KIN,SIDES,JOINT_TYPES,nominal,all_frames,fk_leg,solve_leg,smooth,jacobian
INERTIALS=json.loads((ROOT/'models/inertials.json').read_text())
MASS=sum(v['mass_kg'] for v in INERTIALS.values())
GRAVITY=PARAMS['simulation']['gravity_m_s2']

def centers(q,base):
    fs=all_frames(q,base)
    return {n:(T@np.r_[INERTIALS[n]['com_m'],1])[:3] for n,T in fs.items()}

def com(q,base):
    cs=centers(q,base)
    return sum(INERTIALS[n]['mass_kg']*c for n,c in cs.items())/MASS

def pose(feet,com_xy,seed=None,height=None):
    q,b=nominal() if seed is None else (seed[0].copy(),seed[1].copy())
    if height is not None:b[2,3]=height
    # Shift the seed with the requested COM before IK, so arbitrary timeline
    # seeks do not try to reach new feet from a stale, distant root position.
    b[:2,3]+=np.asarray(com_xy)-com(q,b)[:2]
    errs=[]
    for _ in range(30):
        for i,s in enumerate(SIDES):
            q[5*i:5*i+5],e,a=solve_leg(feet[i],s,b,q[5*i:5*i+5]);errs.append(e)
        delta=np.asarray(com_xy)-com(q,b)[:2]
        if np.linalg.norm(delta)<2e-7:break
        b[:2,3]+=1.2*delta
    else:raise ValueError('COM/IK fixed-point iteration did not converge')
    return q,b,max(errs)

def gravity_torque(q,base):
    cs=centers(q,base);out=np.zeros(10)
    for i,s in enumerate(SIDES):
        _,_,ps,axs=fk_leg(q[i*5:i*5+5],s,base)
        for j in range(5):
            for k in range(j,5):
                name=f'{s}_{JOINT_TYPES[k]}'
                out[i*5+j]+=INERTIALS[name]['mass_kg']*GRAVITY*np.cross(axs[j],cs[name]-ps[j])[2]
    return out

def static_torques(q,base,support):
    """Gravity minus support wrench projection; quasi-static, NO inertia forces.
    support is [left fraction, right fraction] summing to one.
    The overall COM projection is used as COP x; COP y is selected to make
    the floating-base moment equilibrium exact for the chosen force split.
    """
    support=np.asarray(support,float)
    if abs(support.sum()-1)>1e-8:raise ValueError('Support fractions must sum to 1')
    gc=com(q,base);tau=gravity_torque(q,base)
    soles=[fk_leg(q[5*i:5*i+5],s,base)[1][:3,3] for i,s in enumerate(SIDES)]
    y_avg=sum(w*p[1] for w,p in zip(support,soles))
    wrenches=[]
    for i,(s,w,p) in enumerate(zip(SIDES,support,soles)):
        force=np.array([0,0,MASS*GRAVITY*w]);cop=np.array([gc[0],p[1]+gc[1]-y_avg,0])
        moment=np.cross(cop-p,force);W=np.r_[force,moment]
        tau[i*5:i*5+5]-=jacobian(q[i*5:i*5+5],s,base).T@W
        wrenches.append({'force_N':force.tolist(),'moment_Nm':moment.tolist(),'cop_m':cop.tolist()})
    return tau,wrenches

@dataclass
class Reference:
    q:np.ndarray
    base:np.ndarray
    feet:np.ndarray
    support:np.ndarray
    phase:str
    ik_error_m:float

class Planner:
    def __init__(self,steps=6):
        self.steps=steps;self.g=PARAMS['gait'];q,b=nominal()
        self.initial_feet=np.array([fk_leg(q[i*5:i*5+5],s,b)[1][:3,3] for i,s in enumerate(SIDES)])
        self.initial_feet[:,2]=0
        self.q0,self.b0,_=pose(self.initial_feet,self.initial_feet.mean(axis=0)[:2])
        self.seed=(self.q0,self.b0)
        self.duration=self.g['initial_stand_s']+steps*(self.g['shift_s']+self.g['swing_s']+self.g['settle_s'])+self.g['shift_s']+1
    def sample(self,t):
        g=self.g;feet=self.initial_feet.copy();xy=feet.mean(axis=0)[:2];support=np.array([.5,.5]);phase='stand'
        r=t-g['initial_stand_s'];period=g['shift_s']+g['swing_s']+g['settle_s']
        prev_xy=xy.copy();prev_support=np.array([.5,.5])
        def support_xy(stance):
            xy=feet[stance,:2].copy();xy[1]-=(1 if stance==0 else -1)*g.get('com_inset_mm',0)/1000
            return xy
        if r>=0:
            completed=min(int(r//period),self.steps)
            for n in range(completed):
                stance=n%2;swing=1-stance
                feet[swing,0]=feet[stance,0]+g['step_length_m'];prev_xy=support_xy(stance);prev_support=np.eye(2)[stance]
            if completed<self.steps:
                n=completed;stance=n%2;swing=1-stance;u=r-completed*period
                if u<g['shift_s']:
                    a=smooth(u/g['shift_s']);xy=(1-a)*prev_xy+a*support_xy(stance)
                    phase='weight_shift'
                    # Static vertical-force split consistent with planned COM y.
                    support=(1-a)*prev_support+a*np.eye(2)[stance]
                else:
                    xy=support_xy(stance);support=np.eye(2)[stance]
                    v=u-g['shift_s']
                    if v<g['swing_s']:
                        a=v/g['swing_s'];x0=feet[swing,0];x1=feet[stance,0]+g['step_length_m']
                        feet[swing,0]=x0+(x1-x0)*smooth(a)
                        feet[swing,2]=g['step_height_m']*16*a*a*(1-a)*(1-a)
                        phase='swing_'+SIDES[swing]
                    else:
                        feet[swing,0]=feet[stance,0]+g['step_length_m'];phase='touchdown_settle'
            else:
                a=smooth((r-self.steps*period)/g['shift_s']);xy=(1-a)*prev_xy+a*feet.mean(axis=0)[:2]
                support=(1-a)*prev_support+a*np.array([.5,.5]);phase='finish'
        q,b,e=pose(feet,xy,self.seed,self.b0[2,3]);self.seed=(q,b)
        return Reference(q,b,feet,support,phase,e)
