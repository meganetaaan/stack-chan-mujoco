"""Tests executable without MuJoCo/Gymnasium/SB3; not a physics substitute."""
from __future__ import annotations
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import numpy as np
from stackchan_rl.config import ROOT, DEFAULT, load_config, validate, save_json
from stackchan_rl.spec import RobotSpec, OBS_DIM, JOINT_NAMES, observation_schema
from stackchan_rl.actuation import ServoBank, bounded_target
from stackchan_rl.math_utils import euler_quat, quat_mul, quat_matrix, yaw_matrix, command_at
from stackchan_rl.rewards import reward_terms, success_checks
from stackchan_rl.steps import FootStepTracker
from stackchan_rl.checkpoints import save_bundle, bundle_info, assert_interface


class ConfigAndModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config(ROOT / "configs/stand.json")
        cls.spec = RobotSpec.load(cls.cfg)

    def test_all_configs_validate(self):
        for p in (ROOT / "configs").glob("*.json"):
            with self.subTest(p=p):
                validate(load_config(p))

    def test_unknown_config_is_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "c.json"
            p.write_text('{"env":{"polcy_hz":50}}')
            with self.assertRaises(ValueError):
                load_config(p)

    def test_inheritance_cycle_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "c.json"
            p.write_text('{"extends":"c.json"}')
            with self.assertRaises(ValueError):
                load_config(p)

    def test_defaults_not_mutated(self):
        c = load_config()
        c["env"]["action_scale_rad"][0] = 100
        self.assertNotEqual(DEFAULT["env"]["action_scale_rad"][0], 100)

    def test_exact_source_hashes(self):
        folder = ROOT / "assets/r5a"
        m = json.loads((folder / "SOURCE_MANIFEST.json").read_text())
        for f, sha in m["files"].items():
            self.assertEqual(hashlib.sha256((folder/f).read_bytes()).hexdigest(), sha, f)

    def test_actual_A_mass_and_ten_motors(self):
        self.assertIn("A_landscape_cube", self.spec.name)
        self.assertAlmostEqual(self.spec.mass, 0.8260386995994603, places=5)
        self.assertEqual(len(JOINT_NAMES), 10)
        np.testing.assert_array_equal(self.spec.motor["cap"], [0.45, .26, .45, .26, .26]*2)

    def test_home_not_invalid_zero_pose(self):
        self.assertEqual(self.spec.home.shape, (17,))
        self.assertLess(self.spec.home[9], -1.0)
        self.assertGreater(self.spec.home[8], 0.3)
        self.assertGreater(self.spec.home[2], 0.08)

    def test_inertias_positive_and_physical(self):
        root = ET.fromstring(self.spec.xml_text)
        for n in root.findall(".//inertial"):
            a, b, c, d, e, f = np.fromstring(n.attrib["fullinertia"], sep=" ")
            values = np.linalg.eigvalsh([[a,d,e],[d,b,f],[e,f,c]])
            self.assertTrue(np.all(values > 0))
            self.assertLessEqual(values[-1], values[0]+values[1]+1e-9)

    def test_headless_only_removes_visuals(self):
        original = ET.fromstring(self.spec.runtime_xml(True))
        headless = ET.fromstring(self.spec.runtime_xml(False))
        orig_geom = {x.attrib["name"]: x.attrib for x in original.findall(".//worldbody//geom") if not x.get("name", "").startswith("vis_")}
        stripped = {x.attrib["name"]: x.attrib for x in headless.findall(".//worldbody//geom")}
        self.assertEqual(orig_geom, stripped)
        for tag in ("inertial", "joint", "freejoint", "site", "motor", "key"):
            self.assertEqual([e.attrib for e in original.iter(tag)], [e.attrib for e in headless.iter(tag)])

    def test_independent_xml_forward_kinematics(self):
        root = ET.fromstring(self.spec.xml_text)
        q = dict(zip(JOINT_NAMES, self.spec.home[7:]))
        base = np.eye(4)
        base[:3, :3] = quat_matrix(self.spec.home[3:7])
        base[:3, 3] = self.spec.home[:3]
        feet = {}
        def walk(body, T):
            for site in body.findall("site"):
                if site.attrib["name"].endswith("_sole"):
                    feet[site.attrib["name"]] = (T @ np.r_[np.fromstring(site.attrib["pos"], sep=" "), 1])[:3]
            for child in body.findall("body"):
                H = np.eye(4)
                H[:3,3] = np.fromstring(child.attrib["pos"], sep=" ")
                joint = child.find("joint")
                if joint is not None:
                    axis = np.fromstring(joint.attrib["axis"], sep=" ")
                    angle = q[joint.attrib["name"]]
                    K = np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]])
                    H[:3,:3] = np.eye(3)+np.sin(angle)*K+(1-np.cos(angle))*(K@K)
                walk(child,T@H)
        walk(root.find("worldbody/body"), base)
        self.assertEqual(len(feet), 2)
        self.assertLess(max(abs(v[2]) for v in feet.values()), 1e-8)
        self.assertGreater(feet["left_sole"][1], feet["right_sole"][1])

    def test_observation_dimension(self):
        self.assertEqual(OBS_DIM, 61)
        schema = observation_schema()
        self.assertEqual(schema[0]["start"], 0)
        self.assertEqual(schema[-1]["stop"], OBS_DIM)
        for a,b in zip(schema,schema[1:]):
            self.assertEqual(a["stop"], b["start"])

    def test_stand_walk_same_policy_interface(self):
        w = load_config(ROOT / "configs/walk.json")
        self.assertEqual(self.spec.interface(self.cfg), RobotSpec.load(w).interface(w))

    def test_model_fingerprint_rejects_wrong_scaling(self):
        c = deepcopy(self.cfg)
        c["env"]["action_scale_rad"][0] *= 2
        with self.assertRaises(ValueError):
            assert_interface(self.spec.interface(self.cfg), c)

    def test_no_root_assistance_in_step_source(self):
        import ast
        root = ast.parse((ROOT / "stackchan_rl/env.py").read_text())
        step = next(x for x in ast.walk(root) if isinstance(x, ast.FunctionDef) and x.name == "step")
        for node in ast.walk(step):
            if isinstance(node, (ast.Assign, ast.AugAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    self.assertNotIn("data.qpos[", ast.unparse(target))
                    self.assertNotIn("qfrc_applied", ast.unparse(target))
                    self.assertNotIn("xfrc_applied", ast.unparse(target))


class ServoTests(unittest.TestCase):
    def setUp(self):
        self.c = load_config()
        self.s = RobotSpec.load(self.c)
        self.bank = ServoBank(self.s.motor, .001, 2)
        self.bank.reset(self.s.home[7:])

    def test_action_nan_rejected(self):
        with self.assertRaises(ValueError):
            bounded_target(np.full(10,np.nan),self.s.home[7:],self.s.limits,self.c["env"])

    def test_action_shape_rejected(self):
        with self.assertRaises(ValueError):
            bounded_target(np.zeros(9),self.s.home[7:],self.s.limits,self.c["env"])

    def test_target_limit_and_splay_guard(self):
        a = np.full(10,100.0);a[5] = -100
        t = bounded_target(a,self.s.home[7:],self.s.limits,self.c["env"])
        self.assertLessEqual(t[0]-t[5],self.c["env"]["max_outward_hip_spread_rad"]+1e-10)
        self.assertTrue(np.all(t >= self.s.limits[:,0]))
        self.assertTrue(np.all(t <= self.s.limits[:,1]))

    def test_zero_action_is_home(self):
        t = bounded_target(np.zeros(10),self.s.home[7:],self.s.limits,self.c["env"])
        np.testing.assert_allclose(t,self.s.home[7:])

    def test_slew_is_physics_time_based(self):
        home = self.s.home[7:]
        self.bank.step(home,np.zeros(10),home+1)
        np.testing.assert_allclose(self.bank.filtered-home,0.002)

    def test_ten_ms_delay(self):
        bank = ServoBank(self.s.motor,.001,1000)
        bank.reset(np.zeros(10))
        for i in range(10):
            tau,_,_ = bank.step(np.zeros(10),np.zeros(10),np.full(10,0.02))
            np.testing.assert_allclose(tau,0,atol=1e-10,err_msg=f"delay tick {i}")
        tau,_,_ = bank.step(np.zeros(10),np.zeros(10),np.full(10,0.02))
        np.testing.assert_allclose(tau,0.06)

    def test_torque_cap(self):
        for _ in range(200):
            tau,_,bound = self.bank.step(np.zeros(10),np.zeros(10),np.full(10,100.0))
            self.assertTrue(np.all(abs(tau)<=self.s.motor["cap"]+1e-12))
            self.assertTrue(np.all(bound<=self.s.motor["cap"]+1e-12))

    def test_torque_speed_envelope(self):
        bank = ServoBank(self.s.motor,.001,1000)
        bank.reset(np.full(10,10.0))
        tau,_,bound = bank.step(np.zeros(10),self.s.motor["omega"]*1.1,np.full(10,10.0))
        np.testing.assert_allclose(bound,0)
        np.testing.assert_allclose(tau,0)

    def test_braking_is_still_available(self):
        bank = ServoBank(self.s.motor,.001,1000)
        bank.reset(np.zeros(10))
        tau,_,_ = bank.step(np.zeros(10),self.s.motor["omega"]*1.1,np.zeros(10))
        self.assertTrue(np.all(tau<0))

    def test_reset_clears_delay_and_strength(self):
        self.bank.reset(np.ones(10),strength=.9)
        for _ in range(50):self.bank.step(np.zeros(10),np.zeros(10),np.ones(10))
        self.bank.reset(np.zeros(10),strength=1)
        tau,_,_ = self.bank.step(np.zeros(10),np.zeros(10),np.zeros(10))
        np.testing.assert_allclose(tau,0)


class FramesAndMetricsTests(unittest.TestCase):
    def test_wxyz_convention(self):
        q = euler_quat(0,0,np.pi/2)
        np.testing.assert_allclose(quat_matrix(q)@np.array([1,0,0]),[0,1,0],atol=1e-12)
        np.testing.assert_allclose(quat_matrix(q),yaw_matrix(np.pi/2),atol=1e-12)

    def test_quaternion_composition(self):
        a,b = euler_quat(.1,.2,.3),euler_quat(.2,-.1,.5)
        np.testing.assert_allclose(quat_matrix(quat_mul(a,b)),quat_matrix(a)@quat_matrix(b),atol=1e-12)

    def test_command_ramp(self):
        np.testing.assert_allclose(command_at(0,.04,.5,1),0)
        self.assertAlmostEqual(command_at(1,.04,.5,1)[0],.02)
        self.assertAlmostEqual(command_at(2,.04,.5,1)[0],.04)

    def test_reset_fall_not_counted_as_step(self):
        f = FootStepTracker(.02,.08,.002)
        for _ in range(20):f.update([False,False],[.01,.01])
        f.update([True,True],[0,0])
        self.assertEqual(sum(f.counts),0)

    def test_slide_not_counted_as_step(self):
        f = FootStepTracker(.02,.08,.002)
        for _ in range(20):f.update([True,True],[0,0])
        self.assertEqual(sum(f.counts),0)

    def test_hop_not_counted_as_supported_steps(self):
        f = FootStepTracker(.02,.08,.002)
        f.update([True,True],[0,0])
        for _ in range(20):f.update([False,False],[.01,.01])
        f.update([True,True],[0,0])
        self.assertEqual(sum(f.counts),0)

    def test_alternating_true_liftoffs_count(self):
        f = FootStepTracker(.02,.08,.002)
        f.update([True,True],[0,0])
        for _ in range(10):f.update([False,True],[.005,0])
        f.update([True,True],[0,0])
        for _ in range(10):f.update([True,False],[0,.005])
        f.update([True,True],[0,0])
        self.assertEqual(f.counts.tolist(),[1,1])
        self.assertEqual(f.sequence,["left","right"])

    def test_contact_chatter_not_steps(self):
        f = FootStepTracker(.02,.08,.002)
        f.update([True,True],[0,0])
        for _ in range(10):
            f.update([False,True],[.003,0]);f.update([True,True],[0,0])
        self.assertEqual(sum(f.counts),0)


class RewardTests(unittest.TestCase):
    def setUp(self):
        self.c = load_config()
        self.w = self.c["reward"]
        self.s = {"command":np.zeros(3),"velocity":np.zeros(3),"tilt_rad":0.,"height_error":0.,
                  "heading_error":0.,"position_error":np.zeros(2),"contacts":np.array([True,True]),
                  "pose_normalized":np.zeros(10),"gyro":np.zeros(3),"qd":np.zeros(10),
                  "torque_fraction_sq":0.,"power_W":0.,"action_delta":np.zeros(10),"slip_speed_sq":0.,
                  "saturation":0.,"self_contact":False,"swing_mask":np.array([True,False]),
                  "foot_height":np.zeros(2),"valid_landings_this_step":0}

    def test_fall_is_terminal_penalty_only(self):
        r = reward_terms(self.s,self.w,"stand",.02,True)
        self.assertEqual(r,{"termination":-2.0})

    def test_reward_rate_integrates_with_dt(self):
        a = sum(reward_terms(self.s,self.w,"stand",.02,False).values())
        b = sum(reward_terms(self.s,self.w,"stand",.01,False).values())
        self.assertAlmostEqual(a,2*b)

    def test_sliding_is_penalized(self):
        a = sum(reward_terms(self.s,self.w,"stand",.02,False).values())
        self.s["slip_speed_sq"] = .05**2
        b = sum(reward_terms(self.s,self.w,"stand",.02,False).values())
        self.assertLess(b,a)

    def test_airtime_cannot_farm_reward_at_zero_speed(self):
        c = load_config(ROOT/"configs/walk.json")
        self.s["valid_landings_this_step"] = 2
        r = reward_terms(self.s,c["reward"],"walk",.02,False)
        self.assertEqual(r["landing_event"],0)
        self.assertEqual(r["clearance"],0)

    def test_tracking_beats_standing_for_forward_command(self):
        self.s["command"][0]=.06
        r0 = sum(reward_terms(self.s,self.w,"walk",.02,False).values())
        self.s["velocity"][0]=.06
        r1 = sum(reward_terms(self.s,self.w,"walk",.02,False).values())
        self.assertGreater(r1,r0)

    def test_high_return_is_not_success(self):
        summary={"return":999999,"time_limit_reached":False,"terminated":True,"bad_contact_steps":0,
                 "self_contact_steps":0,"min_height_ratio":.95,"requested_forward_m_s":0,
                 "max_tilt_deg":5,"max_horizontal_drift_m":0.001,"double_support_fraction":1.}
        self.assertFalse(all(success_checks(summary,self.c).values()))


class CheckpointTests(unittest.TestCase):
    def test_bundle_roundtrip_and_staged_replacement_without_SB3(self):
        # This tests FILE PACKAGING, not SB3 serialization/inference.
        class FakeSerializer:
            num_timesteps=123
            def save(self,path):Path(path).write_bytes(b"packaging-test-only")
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"best"
            cfg=load_config()
            interface=RobotSpec.load(cfg).interface(cfg)
            save_bundle(FakeSerializer(),p,cfg,interface,{"selection_key":[0,1,2]})
            save_bundle(FakeSerializer(),p,cfg,interface,{"selection_key":[1,2,3]})
            folder,c,i,m=bundle_info(p)
            self.assertEqual(i,interface)
            self.assertEqual(m["num_timesteps"],123)
            self.assertEqual(m["metrics"]["selection_key"],[1,2,3])
            self.assertEqual([x.name for x in Path(t).iterdir()],["best"])

    def test_incomplete_checkpoint_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(FileNotFoundError):bundle_info(t)

if __name__=="__main__":unittest.main()
