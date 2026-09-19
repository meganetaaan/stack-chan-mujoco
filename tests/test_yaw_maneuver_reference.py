import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import numpy as np
from yaw_maneuver_reference import YawCommandReference
from stackchan_rl.maneuver_protocol import validate


class YawCommandReferenceTests(unittest.TestCase):
    def test_c2_swing_has_smooth_floor_transitions_and_same_peak_height(self):
        initial=SimpleNamespace(initial_feet=np.array([[0.,.031,0.],[0.,-.031,0.]]),q0=np.zeros(10),b0=np.eye(4))
        protocol=json.loads(Path('configs/maneuver/acceptance_v1.json').read_text())
        def smooth(t):
            x=np.clip(t,0,1);return x**3*(10+x*(-15+6*x))
        planner=YawCommandReference(initial,None,smooth,protocol,None,.25,25.9,.32,.30,'c2')
        planner.begin(4.)
        start=planner.start+planner.shift_fraction*planner.period
        end=planner.start+.9*planner.period
        height=lambda t:planner.geometry(t)[0][planner.swing,2]
        self.assertEqual(height(start-.001),0.)
        self.assertEqual(height(end+.001),0.)
        self.assertAlmostEqual(height((start+end)/2),.004,places=12)
        h=1e-5
        for boundary,direction in [(start,1),(end,-1)]:
            self.assertLess(abs((height(boundary+direction*h)-height(boundary))/h),1e-6)
            self.assertLess(abs((height(boundary+direction*2*h)-2*height(boundary+direction*h)+height(boundary))/h**2),.01)

    def test_full_schedule_yaw_is_continuous_bounded_and_neutral_at_settled_stops(self):
        for fraction,period,forward in ((.25,.32,.30),(.25,.30,None),(.25,.32,None),(.35,.32,None),(.4,.32,None)):
            with self.subTest(shift_fraction=fraction,period=period,forward=forward):self.check_schedule(fraction,period,forward)

    def test_adaptive_width_uses_continuous_swing_and_returns_to_neutral_at_stops(self):
        self.check_schedule(.25,.32,.30,62.)

    def check_schedule(self,fraction,period,forward,width=None):
        # Isolate the heading scheduler from expensive CAD IK; separate tests
        # validate real six-axis IK and the generated reference uses that IK.
        initial=SimpleNamespace(initial_feet=np.array([[0.,.032,0.],[0.,-.032,0.]]),q0=np.zeros(10),b0=np.eye(4))
        def smooth(t):
            x=np.clip(t,0,1);return x**3*(10+x*(-15+6*x))
        def pose(feet,xy,seed,height):return seed[0],seed[1],0.
        def solve(xyz,yaw,side,base):
            if abs(yaw)>.075:raise ValueError('yaw limit exceeded')
            return np.r_[yaw,np.zeros(5)],0.,None
        kin=SimpleNamespace(legacy=SimpleNamespace(fk_leg=lambda *args:(None,np.eye(4))),solve_flat_foot=solve)
        protocol=json.loads(Path('configs/maneuver/acceptance_v1.json').read_text());bounds=validate(protocol)
        planner=YawCommandReference(initial,pose,smooth,protocol,kin,fraction,step_period=period,forward_period=forward,forward_stance_width_mm=width)
        angles=[];foot_y=[]
        for t in np.arange(0,bounds[-1]+.01,.02):
            sample=planner.sample(t);angles.append(sample.q12[[0,6]])
            feet=planner.geometry(t)[0];foot_y.append(feet[:,1].copy())
            index=min(np.searchsorted(bounds,t,side='right')-1,len(protocol['segments'])-1)
            if protocol['segments'][index]['mode']=='stop' and t>=bounds[index]+2:
                self.assertEqual(planner.mode,'stand')
                if width is not None:np.testing.assert_allclose(feet[:,1],initial.initial_feet[:,1],atol=1e-12)
                np.testing.assert_allclose(sample.q12[[0,6]],0,atol=1e-9)
                np.testing.assert_allclose(sample.support,[.5,.5],atol=1e-9)
            np.testing.assert_array_equal(sample.base[:3,:3],np.eye(3))
        if width is not None:
            self.assertLess(np.max(abs(np.diff(foot_y,axis=0))),.0004)
            np.testing.assert_allclose(np.min(np.abs(foot_y),axis=0),[.031,.031],atol=1e-12)
        self.assertLess(np.max(abs(np.diff(angles,axis=0))),.025)
        self.assertLess(np.max(np.abs(angles)),.075)


if __name__=='__main__':unittest.main()
