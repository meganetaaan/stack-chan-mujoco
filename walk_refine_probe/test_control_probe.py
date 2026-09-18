"""Pure numerical tests; none of these is a physics walking test."""
from pathlib import Path
import sys,unittest
import numpy as np
# Run from the existing v3 project root.
sys.path.insert(0,str(Path.cwd()))
from stackchan_rl.actuation import ServoBank
from control_probe import PostSlewLowPassBank

M={'cap':np.full(10,.26),'stall':np.full(10,.52),'omega':np.full(10,7.),
   'kp':np.full(10,2.0),'kd':np.full(10,.035),'delay_s':np.full(10,.010)}
class Tests(unittest.TestCase):
 def test_zero_filter_bitwise_original(self):
  a=ServoBank(M,.001,2.);b=PostSlewLowPassBank(M,.001,2.,0.)
  rng=np.random.default_rng(42);x=rng.normal(0,.1,10);a.reset(x);b.reset(x)
  for _ in range(500):
   q=rng.normal(0,.1,10);qd=rng.normal(0,.3,10);target=rng.normal(0,.3,10)
   for x,y in zip(a.step(q,qd,target),b.step(q,qd,target)):np.testing.assert_array_equal(x,y)
   np.testing.assert_array_equal(a.filtered,b.filtered);np.testing.assert_array_equal(a.delayed,b.delayed)
 def test_rate_bound(self):
  b=PostSlewLowPassBank(M,.001,2.,.04);rng=np.random.default_rng(1)
  old=b.filtered.copy()
  for t in range(1500):
   b.step(np.zeros(10),np.zeros(10),np.full(10,(-1)**(t//20)))
   self.assertLessEqual(float(abs(b.filtered-old).max()),.002+1e-12);old=b.filtered.copy()
 def test_constant_target_converges(self):
  b=PostSlewLowPassBank(M,.001,2.,.08)
  for _ in range(2500):b.step(np.zeros(10),np.zeros(10),np.full(10,.2))
  np.testing.assert_allclose(b.filtered,.2,atol=1e-10)
 def test_torque_bound_retained(self):
  b=PostSlewLowPassBank(M,.001,2.,.04)
  for speed in [0,3,8,-8]:
   for _ in range(30):
    tau,sat,cap=b.step(np.full(10,-3),np.full(10,speed),np.full(10,3))
    self.assertTrue((abs(tau)<=cap+1e-12).all());self.assertTrue((cap<=M['cap']).all())
 def test_strength_retained(self):
  b=PostSlewLowPassBank(M,.001,2.,.04);b.reset(np.zeros(10),strength=.8)
  for _ in range(500):tau,_,cap=b.step(np.full(10,-3),np.zeros(10),np.ones(10))
  np.testing.assert_allclose(tau,.26*.8)
 def test_reset_clears_filter_and_queue(self):
  b=PostSlewLowPassBank(M,.001,2.,.04)
  for _ in range(100):b.step(np.zeros(10),np.zeros(10),np.ones(10))
  t=np.full(10,-.4);b.reset(t)
  for v in [b.filtered,b.delayed,b.slew_stage,b.lowpass_stage,*b.queue]:np.testing.assert_array_equal(v,t)
 def test_high_frequency_target_attenuation(self):
  a=ServoBank(M,.001,2.);b=PostSlewLowPassBank(M,.001,2.,.04);raw=[];smooth=[]
  for t in range(2000):
   goal=np.full(10,1. if (t//20)%2 else -1.)
   a.step(np.zeros(10),np.zeros(10),goal);b.step(np.zeros(10),np.zeros(10),goal)
   if t>=500:raw.append(a.filtered[0]);smooth.append(b.filtered[0])
  self.assertLess(np.std(smooth),.2*np.std(raw))
 def test_invalid_tau_rejected(self):
  for x in [-.1,float('nan'),float('inf')]:
   with self.assertRaises(ValueError):PostSlewLowPassBank(M,.001,2.,x)
if __name__=='__main__':unittest.main()
