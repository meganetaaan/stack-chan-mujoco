import sys
from pathlib import Path
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from drive import CurrentPositionBank,CATALOG


def drive(**kwargs):
    motor={k:np.array(v) for k,v in {'cap':[.26,.45],'stall':[.52,.93],
        'omega':[103*np.pi/30,81*np.pi/30],'kp':[3.,3.],'kd':[.065,.065],'delay_s':[.01,.01]}.items()}
    return CurrentPositionBank(['XL330-M288-T','XC330-M288-T'],motor,**kwargs)


class DriveTests(unittest.TestCase):
    def test_endpoint_fit(self):
        for voltage in [3.7,5.,6.]:
            d=drive(voltage=voltage)
            np.testing.assert_allclose(d.eta*d.K*d.stall_current,d.stall)
            np.testing.assert_allclose(d.K*d.omega,voltage)
            np.testing.assert_allclose(d.resistance*d.stall_current,voltage)

    def test_bounds_and_energy_both_directions(self):
        for speed in [-5.,-1.,0.,1.,5.]:
            d=drive(delay_s=0,backlash=0)
            for i in range(500):
                tau,_,_=d.step(np.zeros(2),np.full(2,speed),np.full(2,.8 if i<250 else -.8))
                t=d.telemetry
                self.assertTrue(np.all(abs(tau)<=d.cap+1e-12))
                self.assertTrue(np.all(abs(t['motor_current_A'])<=d.ilimit+1e-12))
                self.assertTrue(np.all(abs(t['motor_terminal_V'])<=d.voltage+1e-12))
                self.assertTrue(np.all(t['gear_loss_W']>=-1e-12))
                np.testing.assert_allclose(t['supply_power_W'],t['mechanical_power_W']+t['copper_loss_W']+t['gear_loss_W']+t['idle_loss_W'],atol=1e-12)

    def test_delay_prevents_instantaneous_response(self):
        d=drive(delay_s=.020,backlash=0,lowpass=0)
        for _ in range(20):
            tau,_,_=d.step(np.zeros(2),np.zeros(2),np.full(2,.5))
            np.testing.assert_array_equal(tau,0)
        tau,_,_=d.step(np.zeros(2),np.zeros(2),np.full(2,.5))
        self.assertTrue(np.all(tau>0))

    def test_thermal_model_has_heating_and_cooling(self):
        d=drive(delay_s=0,thermal_capacity=6.,backlash=0)
        for _ in range(1000):d.step(np.zeros(2),np.zeros(2),np.ones(2))
        self.assertTrue(np.all(d.temperature>d.ambient))
        d.temperature[:]=60.
        for _ in range(1000):d.step(np.zeros(2),np.zeros(2),np.zeros(2))
        self.assertTrue(np.all(d.temperature<60.))

    def test_rejects_out_of_range_voltage(self):
        with self.assertRaises(ValueError):drive(voltage=12.)


if __name__=='__main__':unittest.main()
