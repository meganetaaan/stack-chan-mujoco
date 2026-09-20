import copy
import json
from pathlib import Path
import unittest
import numpy as np
from stackchan_rl.maneuver_protocol import validate,command_at,score_motion


class ManeuverProtocolTests(unittest.TestCase):
    def test_partial_diagnostics_never_pass_the_full_schedule(self):
        t, xy, yaw = self.perfect_trace()
        keep = t <= 7.00000001
        result = score_motion(self.p, t[keep], xy[keep], yaw[keep], allow_partial=True)
        self.assertFalse(result['motion_pass'])
        self.assertFalse(result['complete_schedule'])
        self.assertEqual(len(result['segments']), 1)
        self.assertTrue(result['segments'][0]['motion_pass'])

    def setUp(self):
        self.p=json.loads((Path(__file__).resolve().parents[1]/'configs/maneuver/acceptance_v1.json').read_text())

    def perfect_trace(self):
        times=[0.];positions=[[0.,0.]];yaw=[3.13]
        for segment in self.p['segments']:
            for _ in range(round(segment['duration_s']/.02)):
                heading=yaw[-1]+segment['yaw_rate_rad_s']*.01
                positions.append((np.array(positions[-1])+segment['vx_m_s']*.02*np.array([np.cos(heading),np.sin(heading)])).tolist())
                yaw.append(yaw[-1]+segment['yaw_rate_rad_s']*.02)
                times.append(times[-1]+.02)
        return np.array(times),np.array(positions),(np.array(yaw)+np.pi)%(2*np.pi)-np.pi

    def test_predeclared_all_directed_transitions_and_boundaries(self):
        b=validate(self.p);self.assertEqual(b[-1],205.)
        index,c=command_at(self.p,4.)
        self.assertEqual(index,1);self.assertEqual(c[0],.1)
        self.assertEqual(command_at(self.p,205.)[1].tolist(),[0,0,0])
        bad=copy.deepcopy(self.p);bad['segments']=bad['segments'][:-8]
        with self.assertRaises(ValueError):validate(bad)

    def test_exact_motion_including_wrapped_heading_passes_motion_only(self):
        result=score_motion(self.p,*self.perfect_trace())
        self.assertTrue(result['motion_pass'],result)
        self.assertIn('physics safety',result['scope'])

    def test_forward_only_does_not_pass_backward_turns_or_stop(self):
        t,_,_=self.perfect_trace()
        result=score_motion(self.p,t,np.c_[.1*t,np.zeros_like(t)],np.zeros_like(t))
        self.assertFalse(result['motion_pass'])
        for s,r in zip(self.p['segments'],result['segments']):
            if s['mode'] in ('stop','backward','left','right'):self.assertFalse(r['motion_pass'])

    def test_missing_tail_and_large_recording_gap_are_rejected(self):
        t,xy,yaw=self.perfect_trace()
        with self.assertRaises(ValueError):score_motion(self.p,t[:-1],xy[:-1],yaw[:-1])
        keep=np.r_[np.arange(20),np.arange(22,len(t))]
        with self.assertRaises(ValueError):score_motion(self.p,t[keep],xy[keep],yaw[keep])


if __name__=='__main__':unittest.main()
