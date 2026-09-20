"""Joint-count independent version of the frozen residual plant variation.

Use the predeclared baseline ranges. Never alter the nominal reference or its
feedforward torques to reveal the sampled plant parameters to the controller.
"""
import numpy as np
import mujoco


def sample_parameters(config,rng,randomized,nominal_friction,joint_count):
    if joint_count<1:raise ValueError('positive joint count required')
    p={'mass_scale':1.,'base_com_shift_m':[0.,0.,0.],'friction':float(nominal_friction),
       'torque_scale':1.,'speed_scale':1.,'extra_delay_s':0.,**config['fixed_noise']}
    if randomized:
        for key in p:
            lo,hi=config['ranges'][key]
            p[key]=rng.uniform(lo,hi,size=3).tolist() if key=='base_com_shift_m' else float(rng.uniform(lo,hi))
    offsets=rng.uniform(-config['initial_joint_offset_rad'],config['initial_joint_offset_rad'],joint_count) if randomized else np.zeros(joint_count)
    return {**p,'initial_joint_offsets_rad':offsets.tolist(),'randomized':bool(randomized)}


def apply_model_parameters(model,data,actuator_ids,base_id,parameters):
    """Apply recorded variation once, including during state replay."""
    p=parameters
    if p['randomized']:
        model.body_mass[:]*=p['mass_scale'];model.body_inertia[:]*=p['mass_scale']
        model.body_ipos[base_id]+=p['base_com_shift_m']
        model.geom_friction[:,0]=p['friction']
    model.actuator_ctrlrange[actuator_ids]*=p['torque_scale']
    model.actuator_forcerange[actuator_ids]*=p['torque_scale']
    mujoco.mj_setConst(model,data)


def apply_parameters(model,data,motor,actuator_ids,base_id,parameters):
    """Apply once to a fresh nominal model; return varied servo arrays."""
    apply_model_parameters(model,data,actuator_ids,base_id,parameters)
    p=parameters
    varied={k:v.copy() for k,v in motor.items()}
    varied['cap']*=p['torque_scale'];varied['stall']*=p['torque_scale']
    varied['omega']*=p['speed_scale'];varied['delay_s']+=p['extra_delay_s']
    return varied
