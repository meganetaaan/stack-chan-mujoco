"""Explicit diagnostic plant variations; never adapt the nominal reference to them."""
import math

DEFAULT_VARIATION = {'mass_scale':1., 'sliding_friction':None, 'torque_scale':1.,
                     'speed_scale':1., 'extra_delay_s':0., 'initial_joint_offset_rad':[0.]*10}


def validate_variation(value):
    if not isinstance(value,dict) or set(value)-set(DEFAULT_VARIATION):
        raise ValueError('unknown plant variation field or non-object')
    result = {**DEFAULT_VARIATION,**value}
    for key,lo,hi in [('mass_scale',.5,1.5),('torque_scale',.5,1.5),('speed_scale',.5,1.5),
                      ('extra_delay_s',0.,.05),('sliding_friction',.1,1.5)]:
        v = result[key]
        if key == 'sliding_friction' and v is None:
            continue
        if type(v) not in (int,float) or not math.isfinite(v) or not lo <= v <= hi:
            raise ValueError(f'invalid {key}')
    offsets = result['initial_joint_offset_rad']
    if not isinstance(offsets,list) or len(offsets)!=10 or any(
        type(v) not in (int,float) or not math.isfinite(v) or abs(v)>.05 for v in offsets):
        raise ValueError('initial joint offsets require ten finite angles in +/-0.05 rad')
    return result


def vary_model(model, data, variation):
    import mujoco
    model.body_mass[:] *= variation['mass_scale']
    model.body_inertia[:] *= variation['mass_scale']
    if variation['sliding_friction'] is not None:
        # Both contacting geoms must change: MuJoCo normally combines equal-
        # priority friction by maximum, so changing only the floor is insufficient.
        model.geom_friction[:,0] = variation['sliding_friction']
    mujoco.mj_setConst(model,data)


def vary_motors(model, motor, actuator_ids, variation):
    motor['cap'] *= variation['torque_scale']
    motor['stall'] *= variation['torque_scale']
    motor['omega'] *= variation['speed_scale']
    motor['delay_s'] += variation['extra_delay_s']
    model.actuator_ctrlrange[actuator_ids] *= variation['torque_scale']
    model.actuator_forcerange[actuator_ids] *= variation['torque_scale']
