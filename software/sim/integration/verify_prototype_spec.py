"""Check that the editable digital specification agrees with the preserved plant."""
import csv
import json
import math
from pathlib import Path
import sys
import mujoco
import numpy as np
from result_bundle import ROOT,sha

SIM=ROOT/'software/sim/mujoco'
sys.path.insert(0,str(SIM))
from stackchan_rl.residual import runtime_xml


def verify():
    spec=ROOT/'board/mechanical/prototype'
    robot=json.loads((spec/'robot.json').read_text())
    joints=json.loads((spec/'joints.json').read_text())
    frames=json.loads((spec/'frames.json').read_text())
    masses=json.loads((spec/'mass_budget.json').read_text())
    scene=ROOT/robot['source']['path'];model=mujoco.MjModel.from_xml_string(runtime_xml(scene))
    assert robot['source']['sha256']==sha(scene),'source scene changed'
    assert len(joints)==model.nu==12
    assert [j['index'] for j in joints]==list(range(12))
    assert len({j['bus_id'] for j in joints})==12 and all(0<=j['bus_id']<=252 for j in joints)
    assert frames['handedness']=='right' and frames['hardware_calibration_required']
    placement=json.loads((ROOT/'validation/fast_turn_development_v1/packaging_cad_v5/report.json').read_text())['properties']
    for name,com in robot['component_com_base_m'].items():
        np.testing.assert_allclose(com,placement[name]['com_base_m'],rtol=0,atol=1e-12)
    np.testing.assert_allclose(robot['battery_envelope']['center_base_mm'],np.array(placement['battery_2S_reservation']['com_base_m'])*1000,rtol=0,atol=1e-12)
    assert robot['scope']['yaw_actuators'] and not robot['scope']['hardware_control_enabled']
    assert robot['kinematics']['thigh_mm']==50 and robot['kinematics']['shin_mm']==44
    assert robot['body']['width_mm']==robot['body']['depth_mm']==robot['body']['height_mm']==128
    for j in joints:
        name=j['name'];mj=model.joint(name);kind=name.split('_',1)[1]
        np.testing.assert_allclose(j['axis_joint_frame'],mj.axis,rtol=0,atol=1e-12)
        np.testing.assert_allclose(j['joint_position_body_m'],mj.pos,rtol=0,atol=1e-12)
        np.testing.assert_allclose(j['mechanical_range_rad'],mj.range,rtol=0,atol=1e-12)
        np.testing.assert_allclose(robot['joint_limits_rad'][kind],mj.range,rtol=0,atol=1e-12)
        assert j['zero_rad']==0
        assert mj.range[0]<=j['reference_range_rad'][0]<j['reference_range_rad'][1]<=mj.range[1]
        assert j['target_margin_rad']>0
        motor='XC330-M288-T' if kind in ['hip_roll','knee','ankle_pitch'] else 'XL330-M288-T'
        assert j['motor'].endswith(motor)
        assert j['simulation_torque_limit_Nm']==model.actuator(name+'_motor').ctrlrange[1]
        enc=j['encoder_mapping'];assert enc['design_sign'] in [-1,1]
        assert enc['calibrated_sign'] is None and enc['calibrated_zero_count'] is None
        counts=enc['design_zero_count']+enc['design_sign']*np.array(mj.range)*enc['counts_per_revolution']/(2*np.pi)
        assert np.all((counts>=0)&(counts<=4095))
    for link in masses['links']:
        body=model.body(link['body'])
        assert abs(body.mass[0]-link['mass_kg'])<1e-12
        np.testing.assert_allclose(body.ipos,link['com_body_m'],rtol=0,atol=1e-12)
    with (spec/'bom.csv').open() as f:bom=list(csv.DictReader(f))
    summed=sum(float(r['subtotal_mass_kg']) for r in bom)
    assert all(abs(float(r['quantity'])*float(r['unit_mass_kg'])-float(r['subtotal_mass_kg']))<1e-12 for r in bom)
    assert abs(summed-model.body_mass.sum())<1e-12
    assert abs(masses['total_mass_kg']-model.body_mass.sum())<1e-12
    assert {r['item']:int(r['quantity']) for r in bom if r['item'].startswith(('XL','XC'))}=={'XL330-M288-T':6,'XC330-M288-T':6}
    return {'passed':True,'joints':len(joints),'mass_kg':summed,
            'hardware_calibrated':False,'scope':'digital contract consistency; not physical assembly verification'}


if __name__=='__main__':print(json.dumps(verify(),indent=2))
