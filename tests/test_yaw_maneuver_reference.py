import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import numpy as np
from yaw_maneuver_reference import YawCommandReference
from stackchan_rl.maneuver_protocol import validate


class YawCommandReferenceTests(unittest.TestCase):
    def test_full_schedule_yaw_is_continuous_bounded_and_neutral_at_settled_stops(self):
        # Isolate the heading scheduler from expensive CAD IK; separate tests
        # validate real six-axis IK and the generated reference uses that IK.
        initial=SimpleNamespace(initial_feet=np.array([[0.,.022,0.],[0.,-.022,0.]]),q0=np.zeros(10),b0=np.eye(4))
        def smooth(t):
            x=np.clip(t,0,1);return x**3*(10+x*(-15+6*x))
        def pose(feet,xy,seed,height):return seed[0],seed[1],0.
        def solve(xyz,yaw,side,base):
            if abs(yaw)>.075:raise ValueError('yaw limit exceeded')
            return np.r_[yaw,np.zeros(5)],0.,None
        kin=SimpleNamespace(legacy=SimpleNamespace(fk_leg=lambda *args:(None,np.eye(4))),solve_flat_foot=solve)
        protocol=json.loads(Path('configs/maneuver/acceptance_v1.json').read_text());bounds=validate(protocol)
        planner=YawCommandReference(initial,pose,smooth,protocol,kin)
        angles=[]
        for t in np.arange(0,bounds[-1]+.01,.02):
            sample=planner.sample(t);angles.append(sample.q12[[0,6]])
            index=min(np.searchsorted(bounds,t,side='right')-1,len(protocol['segments'])-1)
            if protocol['segments'][index]['mode']=='stop' and t>=bounds[index]+2:
                self.assertEqual(planner.mode,'stand')
                np.testing.assert_allclose(sample.q12[[0,6]],0,atol=1e-9)
                np.testing.assert_allclose(sample.support,[.5,.5],atol=1e-9)
            np.testing.assert_array_equal(sample.base[:3,:3],np.eye(3))
        self.assertLess(np.max(abs(np.diff(angles,axis=0))),.025)
        self.assertLess(np.max(np.abs(angles)),.075)


if __name__=='__main__':unittest.main()
