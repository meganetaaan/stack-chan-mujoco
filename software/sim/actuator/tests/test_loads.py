import sys
from pathlib import Path
import unittest
import numpy as np
import mujoco
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from load_export import joint_wrenches,circuit_load,structural_load


class LoadTests(unittest.TestCase):
    def test_static_offset_mass_has_correct_joint_reaction(self):
        m=mujoco.MjModel.from_xml_string('''<mujoco><option gravity="0 0 -9.81"/><worldbody>
        <body name="beam" pos="0 0 1"><joint name="hinge" axis="0 1 0"/>
        <inertial pos=".1 0 0" mass="1" diaginertia=".01 .01 .01"/></body></worldbody>
        <actuator><motor joint="hinge"/></actuator></mujoco>''')
        d=mujoco.MjData(m);d.ctrl[0]=-.981;mujoco.mj_forward(m,d)
        force=joint_wrenches(m,d,['hinge'])[0]
        np.testing.assert_allclose(d.qacc,0,atol=1e-10)
        np.testing.assert_allclose(force,[0,0,9.81,0,-.981,0],atol=1e-10)

    def test_same_trace_serves_circuit_and_structure(self):
        trace={'supply_current_A':np.array([[1.,-.2],[.5,.2]]),
               'joint_wrench_local_force_moment':np.arange(24.).reshape(2,2,6)}
        loads=circuit_load(trace)
        np.testing.assert_allclose(loads['draw_A'],[1.,.7])
        np.testing.assert_allclose(loads['regeneration_A'],[.2,0])
        np.testing.assert_array_equal(structural_load(trace),trace['joint_wrench_local_force_moment'])


if __name__=='__main__':unittest.main()
