"""Synthetic/structural v3 tests. These are NOT physical walking trials."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import unittest
import numpy as np
from stackchan_rl.config import ROOT, load_config, validate, normalize_config
from stackchan_rl.spec import RobotSpec
from stackchan_rl.quality import GaitQuality, body_angles, quality_checks, quality_score
from stackchan_rl.rewards import reward_terms, success_checks
from stackchan_rl.evaluation import aggregate, classify_behavior
from stackchan_rl.walk_events import WalkEventTracker
from tests.test_walk_v2 import snapshot

# The v2 helper may have a different test-class name; use an independent fixture.
def episode(forward=.194, counts=(4,4)):
    return {'task':'walk','is_success':False,'return':20.,'duration_s':12.,'episode_limit_s':12.,
        'requested_forward_m_s':.02,'commanded_distance_m':.22,'time_limit_reached':True,
        'terminated':False,'failure_reason':None,'forward_m':forward,'lateral_m':0.,
        'valid_landings':list(counts),'forward_landings':list(counts),
        'mean_abs_forward_velocity_error_m_s':.007,'bad_contact_steps':0,'self_contact_steps':0,
        'min_height_ratio':1.,'max_tilt_deg':15.,'max_heading_deg':0.,'max_horizontal_drift_m':abs(forward),
        'double_support_fraction':.5,'flight_fraction':0.,'landing_sequence':['left','right']*4,
        'quality_samples':11000,'pitch_rate_rms_rad_s':.6,'roll_rate_rms_rad_s':.5,
        'body_pitch_peak_to_peak_deg':15.,'action_delta_rms':.10,'action_second_difference_rms':.1,
        'mean_excess_load_cost':.01,'mean_recent_step_imbalance_cost':0.,'repeated_valid_landings':0,
        'peak_sole_load_bw':[2.5,2.5], 'seed':20000, 'no_noise':False}


def completed(s,c):
    s=deepcopy(s)
    s['success_checks']=success_checks(s,c)
    s['locomotion_pass']=all(s['success_checks'].values())
    s['quality_checks']=quality_checks(s,c)
    s['is_success']=s['locomotion_pass'] and all(s['quality_checks'].values())
    s['failed_checks']=[k for k,v in s['success_checks'].items() if not v]+['quality/'+k for k,v in s['quality_checks'].items() if not v]
    return s


class QualityMeasurementTests(unittest.TestCase):
    def setUp(self):
        self.c=load_config(ROOT/'configs/walk_refine.json')
        self.e=deepcopy(self.c['env']);self.e['measurement_start_s']=0.
        self.q=GaitQuality(self.e,self.c['reward'],8.)
        self.time=0.
    def sample(self,gyro=(0,0,0),pitch=0.,loads=(4,4),speed=(0,0),dt=.001):
        self.time+=dt
        self.q.observe(time_s=self.time,dt=dt,gyro=gyro,roll=0.,pitch=pitch,loads=loads,contact_down_speed=speed)
    def finish(self,events=None,time=None,moving=True):
        return self.q.finish_interval(time_s=self.time if time is None else time,dt=.02,moving=moving,
            events=events or {},action_delta=np.zeros(10),action_delta2=np.zeros(10),target_error=np.zeros(10))
    def test_body_axes_roll_pitch(self):
        from stackchan_rl.math_utils import yaw_matrix
        pitch=.2;roll=.3
        Ry=np.array([[np.cos(pitch),0,np.sin(pitch)],[0,1,0],[-np.sin(pitch),0,np.cos(pitch)]])
        Rx=np.array([[1,0,0],[0,np.cos(roll),-np.sin(roll)],[0,np.sin(roll),np.cos(roll)]])
        np.testing.assert_allclose(body_angles(yaw_matrix(.8)@Ry@Rx),[roll,pitch],atol=1e-12)
    def test_pitch_and_roll_rates_separated(self):
        for _ in range(20):self.sample(gyro=(2,3,4))
        s=self.q.summary();self.assertAlmostEqual(s['pitch_rate_rms_rad_s'],3)
        self.assertAlmostEqual(s['roll_rate_rms_rad_s'],2)
        self.assertAlmostEqual(self.finish()['pitch_rate_sq'],9)
    def test_substep_oscillation_does_not_cancel(self):
        for i in range(20):self.sample(gyro=(0,10*(-1)**i,0))
        self.assertAlmostEqual(self.finish()['pitch_rate_sq'],100.)
        self.assertAlmostEqual(self.q.summary()['pitch_rate_rms_rad_s'],10.)
    def test_interval_reset_retains_episode_metrics(self):
        self.sample(gyro=(0,2,0));self.q.begin_interval();self.sample(gyro=(0,0,0))
        self.assertEqual(self.finish()['pitch_rate_sq'],0)
        self.assertAlmostEqual(self.q.summary()['pitch_rate_rms_rad_s'],2**.5)
    def test_initial_drop_is_not_touchdown_event(self):
        for _ in range(80):self.sample(loads=(0,0))
        self.sample(loads=(20,20),speed=(.3,.3))
        self.assertEqual(self.finish()['raw_touchdowns'].tolist(),[0,0])
    def test_short_contact_chatter_not_touchdown_event(self):
        self.sample()
        for _ in range(10):self.sample(loads=(0,4))
        self.sample(loads=(8,4),speed=(.3,0))
        self.assertEqual(self.finish()['raw_touchdowns'].tolist(),[0,0])
    def test_valid_raw_touchdown_speed_cost(self):
        self.sample()
        for _ in range(50):self.sample(loads=(0,8))
        self.sample(loads=(16,8),speed=(.15,0))
        v=self.finish();self.assertEqual(v['raw_touchdowns'].tolist(),[1,0])
        self.assertAlmostEqual(v['touchdown_speed_cost'],1.)
        self.assertAlmostEqual(self.q.summary()['touchdown_speed_rms_m_s'][0],.15)
    def test_static_bodyweight_load_not_penalized(self):
        self.sample(loads=(8,0));self.assertEqual(self.finish()['impact_load_cost'],0.)
    def test_large_load_penalized_and_normalized_by_bodyweight(self):
        self.sample(loads=(28,0));self.assertAlmostEqual(self.finish()['impact_load_cost'],1.)
        q=GaitQuality(self.e,self.c['reward'],16.)
        q.observe(time_s=1,dt=.001,gyro=[0,0,0],roll=0,pitch=0,loads=[56,0],contact_down_speed=[0,0])
        self.assertAlmostEqual(q.i_load_excess,1.)
    def test_initial_settling_excluded(self):
        e=deepcopy(self.e);e['measurement_start_s']=.5
        q=GaitQuality(e,self.c['reward'],8.)
        q.observe(time_s=.1,dt=.001,gyro=[0,10,0],roll=0,pitch=.5,loads=[40,0],contact_down_speed=[0,0])
        self.assertEqual(q.summary()['quality_samples'],0)
    def test_pitch_deadband(self):
        self.sample(pitch=np.deg2rad(7));self.assertEqual(self.finish()['pitch_excursion_cost'],0)
        self.q.begin_interval();self.sample(pitch=np.deg2rad(16))
        self.assertAlmostEqual(self.finish()['pitch_excursion_cost'],1.)
    def test_first_extra_step_not_punished(self):
        v=self.finish({'valid_landing_feet':[0],'forward_landing_feet':[0]},time=1.)
        self.assertEqual(v['recent_step_imbalance_cost'],0.)
        self.assertEqual(v['repeated_landing_events'],0)
    def test_repeated_steps_and_recent_imbalance(self):
        self.finish({'valid_landing_feet':[0],'forward_landing_feet':[0]},time=1.)
        v=self.finish({'valid_landing_feet':[0],'forward_landing_feet':[0]},time=2.)
        self.assertEqual(v['repeated_landing_events'],1)
        self.assertEqual(v['recent_step_imbalance_cost'],.25)
        v=self.finish({'valid_landing_feet':[1],'forward_landing_feet':[1]},time=3.)
        self.assertEqual(v['repeated_landing_events'],0)
        self.assertEqual(v['recent_step_imbalance_cost'],0.)
    def test_recent_window_forgives_past_bias(self):
        self.finish({'forward_landing_feet':[0,0,0]},time=1.)
        self.assertEqual(self.finish(time=6.)['recent_step_imbalance_cost'],0.)
    def test_stop_clears_sequence_penalty(self):
        self.finish({'valid_landing_feet':[0],'forward_landing_feet':[0,0]},time=1.)
        v=self.finish(time=2.,moving=False)
        self.assertEqual(v['recent_step_imbalance_cost'],0.)
        self.assertIsNone(self.q.last_landing)
    def test_finite_telemetry_validation(self):
        with self.assertRaises(ValueError):self.sample(gyro=[0,float('nan'),0])
    def test_action_and_tracking_error_statistics(self):
        self.q.finish_interval(time_s=1,dt=.02,moving=True,events={},action_delta=np.full(10,.2),
            action_delta2=np.full(10,.4),target_error=np.full(10,.1))
        s=self.q.summary();self.assertAlmostEqual(s['action_delta_rms'],.2)
        np.testing.assert_allclose(s['target_error_rms_rad'],.1)
    def test_fresh_episode_resets_metrics(self):
        self.sample(gyro=(0,2,0));q=GaitQuality(self.e,self.c['reward'],8.)
        self.assertEqual(q.summary()['quality_samples'],0)


class RefineRewardTests(unittest.TestCase):
    def setUp(self):self.c=load_config(ROOT/'configs/walk_refine.json')
    def state(self):
        s=snapshot(.02,.02);s['walk_objective_version']=3;s['no_step_elapsed_s']=0.
        s['gait_quality']={};return s
    def reward(self,s,dt=.02):return reward_terms(s,self.c['reward'],'walk',dt,False)
    def test_v2_reward_unchanged_when_v3_fields_added(self):
        c=load_config(ROOT/'configs/walk_step1.json');s=snapshot(.02,.02)
        a=reward_terms(s,c['reward'],'walk',.02,False)
        s['gait_quality']={'pitch_rate_sq':100.};s['action_second_delta']=np.ones(10)
        self.assertEqual(a,reward_terms(s,c['reward'],'walk',.02,False))
    def test_forward_velocity_and_step_reward_preserved(self):
        s=self.state();a=self.reward(s);s['walk_objective_version']=2;b=self.reward(s)
        for k in ('velocity','forward_progress','liftoff_event','landing_event','forward_landing_event','no_step'):
            self.assertEqual(a[k],b[k])
    def test_pitch_oscillation_penalized_more_than_roll(self):
        p=self.state();p['gait_quality']={'pitch_rate_sq':4};p['gyro']=np.array([0,2,0])
        r=self.state();r['gait_quality']={'pitch_rate_sq':0};r['gyro']=np.array([2,0,0])
        self.assertLess(sum(self.reward(p).values()),sum(self.reward(r).values()))
    def test_static_lean_within_band_has_no_pitch_cost(self):
        self.assertEqual(self.reward(self.state())['pitch_excursion'],0)
    def test_normalized_action_second_difference_penalty(self):
        s=self.state();s['action_second_delta']=np.ones(10)
        self.assertLess(self.reward(s)['action_acceleration'],0)
    def test_event_cost_not_scaled_by_dt(self):
        s=self.state();s['gait_quality']={'touchdown_speed_cost':2,'repeated_landing_events':1}
        for k in ('touchdown_speed','repeated_step'):
            self.assertAlmostEqual(self.reward(s,.02)[k],self.reward(s,.01)[k])
    def test_rate_costs_integrate_dt(self):
        s=self.state();s['gait_quality']={'pitch_rate_sq':2,'impact_load_cost':1,'recent_step_imbalance_cost':1}
        for k in ('pitch_rate','impact_load','step_imbalance'):
            self.assertAlmostEqual(self.reward(s,.02)[k],2*self.reward(s,.01)[k])
    def test_stop_has_no_step_or_touchdown_cost(self):
        s=self.state();s['command'][:]=0;s['gait_quality']={'touchdown_speed_cost':2,'recent_step_imbalance_cost':1,'repeated_landing_events':2}
        for k in ('touchdown_speed','step_imbalance','repeated_step'):self.assertEqual(self.reward(s)[k],0)
    def test_termination_remains_penalty_only(self):
        s=self.state();self.assertEqual(reward_terms(s,self.c['reward'],'walk',.02,True),{'termination':-3.})
    def test_standing_does_not_gain_velocity_reward(self):
        s=self.state();s['velocity'][:]=0
        self.assertAlmostEqual(self.reward(s)['velocity'],0)
    def test_smooth_measured_walking_scores_above_shaky_same_progress(self):
        s=self.state();r=deepcopy(s);r['gait_quality']={'pitch_rate_sq':9,'impact_load_cost':1,'touchdown_speed_cost':2}
        self.assertGreater(sum(self.reward(s).values()),sum(self.reward(r).values()))


class RefineSelectionTests(unittest.TestCase):
    def setUp(self):self.c=load_config(ROOT/'configs/walk_refine.json')
    def test_smooth_stopping_never_outranks_real_walking(self):
        a=completed(episode(0,(0,0)),self.c)
        b=episode();b['pitch_rate_rms_rad_s']=4.;b=completed(b,self.c)
        self.assertGreater(aggregate([b],3)['selection_key'],aggregate([a],3)['selection_key'])
    def test_smooth_walk_preferred_over_shaky_walk(self):
        a=completed(episode(),self.c);b=episode();b['pitch_rate_rms_rad_s']=3.;b=completed(b,self.c)
        self.assertGreater(aggregate([a],3)['selection_key'],aggregate([b],3)['selection_key'])
    def test_nonmoving_failed_recovery_ranked_by_motion_not_stillness(self):
        a=completed(episode(0,(0,0)),self.c)
        b=episode(.15,(5,2));b['max_tilt_deg']=26;b['pitch_rate_rms_rad_s']=4.;b=completed(b,self.c)
        self.assertGreater(aggregate([b],3)['selection_key'],aggregate([a],3)['selection_key'])
    def test_moving_but_uneven_counts_fail_quality_not_locomotion(self):
        s=completed(episode(.194,(5,2)),self.c)
        self.assertTrue(s['locomotion_pass']);self.assertFalse(s['quality_checks']['step_balance'])
        self.assertFalse(s['is_success']);self.assertEqual(classify_behavior(s),'walking_needs_refinement')
    def test_one_extra_step_at_end_allowed(self):
        self.assertTrue(quality_checks(episode(.194,(5,4)),self.c)['step_balance'])
    def test_missing_measurement_never_passes_quality(self):
        s=episode();s.pop('quality_samples')
        self.assertFalse(all(quality_checks(s,self.c).values()));self.assertEqual(quality_score(s),0.)
    def test_quality_not_applied_to_legacy_objective(self):
        self.assertEqual(quality_checks(episode(),load_config(ROOT/'configs/walk_step1.json')), {})
    def test_failed_checks_names_exposed_by_aggregate(self):
        s=episode();s['pitch_rate_rms_rad_s']=4.;s=completed(s,self.c)
        a=aggregate([s],3);self.assertEqual(a['failed_check_counts']['quality/pitch_rate'],1)
        self.assertIn('pitch_rate_rms_rad_s',a['mean_quality'])
    def test_high_reward_not_enough(self):
        a=episode(0,(0,0));a['return']=10000.;a=completed(a,self.c)
        b=completed(episode(),self.c)
        self.assertGreater(aggregate([b],3)['selection_key'],aggregate([a],3)['selection_key'])
    def test_one_sided_steps_not_eligible(self):
        s=completed(episode(.20,(10,0)),self.c)
        self.assertFalse(s['locomotion_pass']);self.assertEqual(aggregate([s],3)['selection_key'][0],0.)


class RefineConfigTests(unittest.TestCase):
    def test_refine_interface_identical_to_v2_and_stand(self):
        base=load_config(ROOT/'configs/walk_step1.json');interface=RobotSpec.load(base).interface(base)
        for path in ('walk_refine','walk_step2_smooth','walk_step3_smooth','stand'):
            c=load_config(ROOT/f'configs/{path}.json');self.assertEqual(interface,RobotSpec.load(c).interface(c))
    def test_actor_distribution_preserved_and_value_reinitialized(self):
        c=load_config(ROOT/'configs/walk_refine.json')
        self.assertTrue(c['transfer']['actor_only']);self.assertIsNone(c['transfer']['reset_log_std'])
        self.assertTrue(c['transfer']['evaluate_before_learning'])
        self.assertEqual(c['env']['command_forward_range_m_s'],[.02,.02])
    def test_no_new_physical_limits_or_gain(self):
        a=load_config(ROOT/'configs/walk_step1.json');b=load_config(ROOT/'configs/walk_refine.json')
        for k in ('target_slew_rad_s','action_scale_rad','max_outward_hip_spread_rad','fall_tilt_deg'):
            self.assertEqual(a['env'][k],b['env'][k])
        self.assertEqual(RobotSpec.load(a).fingerprint,RobotSpec.load(b).fingerprint)
    def test_legacy_config_does_not_silently_upgrade(self):
        c=load_config(ROOT/'configs/walk_step1.json');c['env'].pop('gait_quality_metrics')
        n=normalize_config(c);self.assertEqual(n['env']['walk_objective_version'],2)
        self.assertFalse(n['env']['gait_quality_metrics'])
    def test_no_quality_sampling_rejected_for_v3(self):
        c=load_config(ROOT/'configs/walk_refine.json');c['env']['gait_quality_metrics']=False
        with self.assertRaises(ValueError):validate(c)
    def test_zero_quality_scale_rejected(self):
        c=load_config(ROOT/'configs/walk_refine.json');c['reward']['pitch_scale_deg']=0
        with self.assertRaises(ValueError):validate(c)
    def test_refine_smoke_can_transfer_from_walk_smoke(self):
        a=load_config(ROOT/'configs/walk_smoke.json');b=load_config(ROOT/'configs/refine_smoke.json')
        self.assertEqual(a['ppo']['net_arch'],b['ppo']['net_arch'])
        self.assertEqual(RobotSpec.load(a).interface(a),RobotSpec.load(b).interface(b))
    def test_telemetry_can_measure_old_without_new_rewards(self):
        c=load_config(ROOT/'configs/walk_step1.json');c['env']['gait_quality_metrics']=True;validate(c)


class RefineDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.c=load_config(ROOT/'configs/walk_refine.json')
        self.interface=RobotSpec.load(self.c).interface(self.c)
    def report(self, s):
        return {'physics_executed':True,'config':self.c,'no_noise':False,'interface':self.interface,
                'results':[{'episode_results':[completed(s,self.c)]}]}
    def test_old_results_have_failed_checks_but_missing_quality(self):
        from diagnose_gait import summarize
        s=episode();s.pop('pitch_rate_rms_rad_s');r=self.report(s)
        a=summarize(r);self.assertIn('pitch_rate_rms_rad_s',a['missing_metrics'])
    def test_comparison_requires_same_seeds(self):
        from diagnose_gait import compare
        a=episode();b=episode();b['seed']=1
        with self.assertRaises(ValueError):compare(self.report(a),self.report(b))
    def test_comparison_identifies_forward_regression(self):
        from diagnose_gait import compare
        a=episode();b=episode(.09);b['pitch_rate_rms_rad_s']=.1
        result=compare(self.report(a),self.report(b));self.assertFalse(result['checks']['0.020000/retain_forward_85pct'])
    def test_comparison_identifies_improvement(self):
        from diagnose_gait import compare
        a=episode();b=episode();b['pitch_rate_rms_rad_s']=.3
        self.assertTrue(compare(self.report(a),self.report(b))['criteria_met'])
    def test_partial_reports_not_treated_as_complete(self):
        from diagnose_gait import summarize
        r=self.report(episode());r['status']='IN_PROGRESS'
        with self.assertRaises(ValueError):summarize(r)


if __name__=='__main__':unittest.main()
