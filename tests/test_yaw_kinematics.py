import importlib.util
from pathlib import Path
import unittest
import numpy as np
from stackchan_rl.yaw_kinematics import YawLegKinematics,rz


class YawKinematicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path('outputs/design_r6_base_collisions/src/tab5_biped/core.py')
        if not path.exists():raise unittest.SkipTest('CAD-generated geometry required')
        spec=importlib.util.spec_from_file_location('yaw_test_legacy_core',path)
        cls.legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.legacy)
        cls.model=YawLegKinematics(cls.legacy,{'left':[-.025,.022,.062],'right':[-.025,-.022,.062]})

    def test_zero_yaw_preserves_original_link_frames_and_sole(self):
        q,base=self.legacy.nominal()
        for i,side in enumerate(('left','right')):
            old=self.legacy.fk_leg(q[i*5:i*5+5],side,base)
            new=self.model.fk_leg(np.r_[0.,q[i*5:i*5+5]],side,base)
            np.testing.assert_array_equal(old[0],new[0][1:])
            np.testing.assert_array_equal(old[1],new[1])
            np.testing.assert_array_equal(old[2],new[2][1:])

    def test_flat_foot_ik_round_trip_with_body_heading_and_both_yaw_signs(self):
        rng=np.random.default_rng(310401)
        for side in ('left','right'):
            for _ in range(30):
                roll=rng.uniform(-.1,.1);knee=rng.uniform(-1.4,-1.0)
                q=np.array([rng.uniform(-.15,.15),roll,-knee/2,knee,-knee/2,-roll])
                heading=rng.uniform(-np.pi,np.pi)
                base=np.eye(4);base[:3,:3]=rz(heading);base[:3,3]=rng.uniform(-.2,.2,3)
                sole=self.model.fk_leg(q,side,base)[1]
                solved,_,_=self.model.solve_flat_foot(sole[:3,3],heading+q[0],side,base)
                np.testing.assert_allclose(solved,q,atol=1e-9,rtol=0)
                np.testing.assert_allclose(self.model.fk_leg(solved,side,base)[1],sole,atol=1e-10)

    def test_rejects_yaw_limit_and_tilted_body(self):
        with self.assertRaisesRegex(ValueError,'yaw limit'):
            self.model.solve_flat_foot([0,0,0],.3,'left',np.eye(4))
        base=np.eye(4);a=.1;base[1:3,1:3]=[[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]]
        with self.assertRaisesRegex(ValueError,'upright'):
            self.model.solve_flat_foot([0,0,0],0,'left',base)


if __name__=='__main__':unittest.main()
