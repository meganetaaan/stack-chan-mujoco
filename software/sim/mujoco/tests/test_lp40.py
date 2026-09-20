"""v4 mathematical/regression tests, not MuJoCo walking-success tests."""
from __future__ import annotations
from copy import deepcopy
import json
import math
import unittest
import numpy as np
from stackchan_rl.config import ROOT, load_config, validate, normalize_config
from stackchan_rl.spec import RobotSpec
from stackchan_rl.actuation import make_servo_bank, PostSlewLowPassBank, bounded_target
from stackchan_rl.checkpoints import assert_interface, assert_transfer_interface
from stackchan_rl.ordered_steps import OrderedStepCredit
from stackchan_rl.walk_events import WalkEventTracker
from stackchan_rl.rewards import reward_terms
from stackchan_rl.quality import quality_checks, quality_score_v4
from stackchan_rl.target_metrics import TargetMotionMetrics
from stackchan_rl.evaluation import aggregate
from tests.test_walk_v2 import snapshot
from tests.test_refine import episode, completed
from tests._actuation_v3_reference import ServoBank as OriginalBank
from tests._probe_reference import PostSlewLowPassBank as OriginalProbe


def config():
    return load_config(ROOT/'configs/walk_lp40.json')


def good_episode():
    s = episode(forward=.22)
    s.update(target_metric_samples=575, target_delta_rms_rad_mean=.008,
             distance_tracking_abs_error_m=0., step_repeat_fraction=0.,
             walk_objective_version=4, quality_scoring_limits=config()['success'])
    return s


class FilterRegression(unittest.TestCase):
    def setUp(self):
        self.c = config(); self.spec = RobotSpec.load(self.c)
    def test_40ms_and_80ms_match_original_probe_exactly(self):
        rng = np.random.default_rng(73)
        for tau in (.04, .08):
            e=deepcopy(self.c['env']); e['target_lowpass_time_constant_s']=tau
            a=make_servo_bank(self.spec.motor,.001,e)
            b=OriginalProbe(self.spec.motor,.001,e['target_slew_rad_s'],tau)
            for strength in (1., .9):
                a.reset(self.spec.home[7:],strength); b.reset(self.spec.home[7:],strength)
                for t in range(1500):
                    if t%20==0:
                        target=bounded_target(rng.uniform(-1,1,10),self.spec.home[7:],self.spec.limits,e)
                    q=self.spec.home[7:]+rng.normal(0,.04,10);qd=rng.normal(0,1,10)
                    xa=a.step(q,qd,target);xb=b.step(q,qd,target)
                    for x,y in zip(xa,xb): np.testing.assert_array_equal(x,y)
                    for key in ('filtered','delayed','slew_stage','lowpass_stage'):
                        np.testing.assert_array_equal(getattr(a,key),getattr(b,key))
    def test_disabled_matches_v3_bitwise(self):
        e=deepcopy(self.c['env']);e['target_lowpass_time_constant_s']=0.
        a=make_servo_bank(self.spec.motor,.001,e);b=OriginalBank(self.spec.motor,.001,2.)
        a.reset(self.spec.home[7:]); b.reset(self.spec.home[7:])
        for i in range(250):
            target=self.spec.home[7:]+.1*(-1)**(i//20)
            for x,y in zip(a.step(self.spec.home[7:],np.zeros(10),target),b.step(self.spec.home[7:],np.zeros(10),target)):
                np.testing.assert_array_equal(x,y)
    def test_exact_coefficient_at_physics_rate(self):
        b=make_servo_bank(self.spec.motor,.001,self.c['env'])
        self.assertAlmostEqual(b.alpha,1-math.exp(-.001/.04),places=15)
        b.reset(np.zeros(10));b.step(np.zeros(10),np.zeros(10),np.ones(10))
        np.testing.assert_allclose(b.filtered,np.full(10,.002*b.alpha),atol=1e-15)
    def test_filter_does_not_violate_slew_or_torque_caps(self):
        b=make_servo_bank(self.spec.motor,.001,self.c['env']);b.reset(np.zeros(10),.9)
        for k in range(1000):
            prior=b.filtered.copy();tau,_,bound=b.step(np.zeros(10),np.ones(10),np.full(10,(-1.)**(k//20)))
            self.assertLessEqual(np.max(np.abs(b.filtered-prior)),.002+1e-12)
            self.assertTrue(np.all(np.abs(tau)<=bound+1e-12))
            self.assertTrue(np.all(bound<=self.spec.motor['cap']*.9+1e-12))
    def test_constant_input_settles_and_preserves_delay(self):
        b=make_servo_bank(self.spec.motor,.001,self.c['env']);b.reset(np.zeros(10))
        history=[]
        for _ in range(600):
            b.step(np.zeros(10),np.zeros(10),np.full(10,.02)); history.append(b.filtered.copy())
            if len(history)>b.delay_ticks:
                np.testing.assert_array_equal(b.delayed,history[-1-b.delay_ticks])
        np.testing.assert_allclose(b.filtered,.02,atol=1e-7)
    def test_reset_clears_filter_and_transport_state(self):
        b=make_servo_bank(self.spec.motor,.001,self.c['env']);b.step(np.zeros(10),np.zeros(10),np.ones(10))
        b.reset(np.full(10,.13))
        for x in [b.filtered,b.delayed,b.slew_stage,b.lowpass_stage,*b.queue]:
            np.testing.assert_array_equal(x,np.full(10,.13))
    def test_invalid_tau_rejected(self):
        for v in (-.1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):PostSlewLowPassBank(self.spec.motor,.001,2,v)


class ContractTests(unittest.TestCase):
    def setUp(self):self.c=config();self.old=load_config(ROOT/'configs/walk_refine.json');self.s=RobotSpec.load(self.c)
    def test_legacy_interface_unchanged(self):
        fixture=json.loads((ROOT/'docs/interface.example.json').read_text())
        self.assertEqual(self.s.interface(self.old),fixture)
    def test_new_runtime_has_same_dimensions_but_distinct_contract(self):
        a=self.s.interface(self.old);b=self.s.interface(self.c)
        self.assertEqual(a['observation_fields'],b['observation_fields'])
        self.assertEqual(a['joint_order'],b['joint_order'])
        self.assertNotEqual(a,b)
        self.assertEqual(b['control']['target_lowpass_time_constant_s'],.04)
    def test_strict_loading_rejects_implicit_change(self):
        with self.assertRaises(ValueError):assert_interface(self.s.interface(self.old),self.c)
        with self.assertRaises(ValueError):assert_transfer_interface(self.s.interface(self.old),self.c)
    def test_explicit_migration_succeeds_and_is_recorded(self):
        i,m=assert_transfer_interface(self.s.interface(self.old),self.c,allow_lowpass_change=True)
        self.assertEqual(i,self.s.interface(self.c));self.assertTrue(m['control_changed'])
        self.assertEqual(m['source_time_constant_s'],0.);self.assertEqual(m['destination_time_constant_s'],.04)
    def test_migration_does_not_bypass_other_mismatches(self):
        for key in ('policy_hz','target_slew_rad_s','obs_clip'):
            old=self.s.interface(self.old);old['control'][key]*=2
            with self.assertRaises(ValueError):assert_transfer_interface(old,self.c,allow_lowpass_change=True)
        old=self.s.interface(self.old);old['model_fingerprint']='changed'
        with self.assertRaises(ValueError):assert_transfer_interface(old,self.c,allow_lowpass_change=True)
    def test_unknown_filter_refused(self):
        old=self.s.interface(self.c);old['control']['target_lowpass_kind']='other'
        with self.assertRaises(ValueError):assert_transfer_interface(old,self.c,allow_lowpass_change=True)
    def test_legacy_configuration_not_upgraded(self):
        raw=deepcopy(self.old);raw['env'].pop('target_lowpass_time_constant_s')
        raw['transfer'].pop('allow_target_lowpass_change')
        c=normalize_config(raw)
        self.assertEqual(c['env']['target_lowpass_time_constant_s'],0.)
        self.assertEqual(c['env']['walk_objective_version'],3)
    def test_bad_versions_and_bad_controls_rejected(self):
        for key,v in [('target_lowpass_time_constant_s',-.04),('target_lowpass_time_constant_s',True),('walk_objective_version',3)]:
            c=deepcopy(self.c);c['env'][key]=v
            with self.assertRaises(ValueError):validate(c)
    def test_all_configs_validate(self):
        for p in (ROOT/'configs').glob('*.json'):validate(load_config(p))


class OrderedCreditTests(unittest.TestCase):
    def setUp(self):self.tr=OrderedStepCredit(.25)
    def u(self,i,t,forward=True,active=True):
        return self.tr.update({'valid_landing_feet':[i], 'forward_landing_feet':[i] if forward else []},t,active)
    def test_first_then_opposite_then_repeat(self):
        self.assertEqual(self.u(0,1)['ordered_forward_landings_this_step'],1)
        self.assertEqual(self.u(1,2)['ordered_alternating_landings_this_step'],1)
        r=self.u(1,3);self.assertEqual(r['ordered_repeated_landings_this_step'],1)
        self.assertEqual(r['ordered_rewarded_landings_this_step'],0);self.assertEqual(r['ordered_forward_landings_this_step'],0)
    def test_repeated_steps_cannot_fake_alternation(self):
        for i,t in zip([0,0,0,1,1,0],[1,2,3,4,5,6]):self.u(i,t)
        self.assertEqual(self.tr.totals['ordered_alternating_landings'],2)
        self.assertEqual(self.tr.totals['ordered_repeated_landings'],3)
    def test_cooldown_suppressed_landing_still_changes_predecessor(self):
        self.u(0,1); r=self.u(1,1.02)
        self.assertEqual(r['ordered_rewarded_landings_this_step'],0)
        self.assertEqual(self.u(1,2)['ordered_repeated_landings_this_step'],1)
    def test_in_place_landing_is_not_forward_alternation(self):
        self.u(0,1);r=self.u(1,2,forward=False)
        self.assertEqual(r['ordered_alternating_landings_this_step'],0)
        self.assertEqual(r['ordered_forward_landings_this_step'],0)
    def test_simultaneous_no_invented_order(self):
        self.u(0,1)
        r=self.tr.update({'valid_landing_feet':[0,1],'forward_landing_feet':[0,1]},2,True)
        self.assertEqual(r['ordered_rewarded_landings_this_step'],0)
        self.assertEqual(r['simultaneous_landing_frames_this_step'],1)
        self.assertIsNone(self.tr.last)
    def test_stop_no_step_credit(self):
        self.u(0,1);r=self.u(1,2,active=False)
        self.assertEqual(sum(r.values()),0);self.assertIsNone(self.tr.last)
    def test_legacy_raw_counts_identical_under_v4(self):
        old=load_config(ROOT/'configs/walk_refine.json')['env'];new=config()['env']
        a=WalkEventTracker(.02,old);b=WalkEventTracker(.02,new)
        xy=np.array([[0.,.03],[0.,-.03]])
        def u(contact,height):
            aa=a.update(contact,height,xy,float(xy[:,0].mean()),True)
            bb=b.update(contact,height,xy,float(xy[:,0].mean()),True)
            for k in aa:self.assertEqual(aa[k],bb[k])
        for i in [0,0,1,1,0]:
            for _ in range(3):u([True,True],[0,0])
            contacts=[True,True];contacts[i]=False;heights=[0.,0.];heights[i]=.006
            for _ in range(8):u(contacts,heights)
            xy[i,0]+=.01
            for _ in range(3):u([True,True],[0,0])
        np.testing.assert_array_equal(a.counts,b.counts)
        self.assertEqual(a.sequence,b.sequence)
        self.assertGreater(b.ordered_credit.totals['ordered_repeated_landings'],0)


class RewardV4Tests(unittest.TestCase):
    def setUp(self):self.c=config()
    def s(self,cmd=.02,v=.02,d=.0004):
        s=snapshot(cmd,v);s.update(walk_objective_version=4,new_forward_distance_m=d,gait_quality={})
        return s
    def r(self,s,dt=.02):return reward_terms(s,self.c['reward'],'walk',dt,False)
    def test_progress_cap_matches_command_interval(self):
        a=self.r(self.s(d=.0004))['forward_progress']
        b=self.r(self.s(v=.04,d=.0008))['forward_progress']
        self.assertEqual(a,b);self.assertAlmostEqual(a,.5*.02)
    def test_progress_uses_ramped_current_command(self):
        s=self.s(cmd=.01,v=.02,d=.1);s['requested_forward_m_s']=.02
        self.assertAlmostEqual(self.r(s)['forward_progress'],.5*.01*.02/.02)
    def test_extra_distance_not_repaid_later(self):
        a=self.r(self.s(d=10.))['forward_progress'];b=self.r(self.s(d=0.))['forward_progress']
        self.assertAlmostEqual(a,.01);self.assertEqual(b,0.)
    def test_velocity_zero_not_rewarded_and_matching_beats_overspeed(self):
        self.assertEqual(self.r(self.s(v=0,d=0))['velocity'],0)
        def terms(s):r=self.r(s);return sum(r[k] for k in ('velocity','forward_progress','overspeed'))
        self.assertGreater(terms(self.s()),terms(self.s(v=.028,d=.00056)))
        self.assertGreater(terms(self.s()),terms(self.s(v=.04,d=.0008)))
    def test_high_overspeed_cost_bounded(self):
        self.assertAlmostEqual(self.r(self.s(v=100))['overspeed'],-self.c['reward']['overspeed']*4*.02)
    def test_stop_event_rewards_are_zero(self):
        s=self.s(0,0)
        for key in ('ordered_rewarded_landings_this_step','ordered_forward_landings_this_step','ordered_alternating_landings_this_step','ordered_repeated_landings_this_step'):s[key]=3
        r=self.r(s)
        for k in ('forward_progress','landing_event','forward_landing_event','alternating_event','repeated_step','no_step'):self.assertEqual(r[k],0.)
    def test_raw_chatter_penalty_not_hidden_by_filter(self):
        s=self.s();s['action_delta']=np.ones(10);s['action_second_delta']=np.full(10,2)
        r=self.r(s);self.assertAlmostEqual(r['action_rate'],-.6*.02)
        self.assertAlmostEqual(r['action_acceleration'],-.15*4*.02)
    def test_strict_events_not_legacy_event_numbers(self):
        s=self.s();s.update(forward_landings_this_step=1,alternating_landings_this_step=1,
                            ordered_forward_landings_this_step=0,ordered_repeated_landings_this_step=1)
        r=self.r(s);self.assertEqual(r['forward_landing_event'],0)
        self.assertEqual(r['alternating_event'],0);self.assertEqual(r['repeated_step'],-.25)
    def test_discrete_events_not_multiplied_by_dt(self):
        s=self.s();s.update(ordered_alternating_landings_this_step=1,ordered_forward_landings_this_step=1)
        self.assertEqual(self.r(s,.02)['alternating_event'],self.r(s,.01)['alternating_event'])
    def test_termination_only_penalty(self):
        self.assertEqual(reward_terms(self.s(),self.c['reward'],'walk',.02,True),{'termination':-self.c['reward']['termination']})


class TargetAndAcceptanceTests(unittest.TestCase):
    def test_target_rms_mean_and_global_explicitly_distinguished(self):
        m=TargetMotionMetrics(np.zeros(10),.0)
        t=np.arange(10)*.002;m.observe(t,.02)
        self.assertAlmostEqual(m.summary()['target_delta_rms_rad_mean'],np.mean(t))
        self.assertAlmostEqual(m.summary()['target_delta_global_rms_rad'],np.sqrt(np.mean(t*t)))
    def test_warmup_ignored_but_previous_target_tracks_it(self):
        m=TargetMotionMetrics(np.zeros(10),.5);m.observe(np.ones(10),.2);m.observe(np.ones(10)*1.01,.5)
        self.assertEqual(m.count,1);self.assertAlmostEqual(m.summary()['target_delta_rms_rad_mean'],.01)
    def test_target_missing_is_not_pass(self):
        s=good_episode();s.pop('target_metric_samples')
        self.assertFalse(quality_checks(s,config())['target_smoothness'])
    def test_smooth_overspeed_fails_distance_gate(self):
        s=good_episode();s['forward_m']=.307
        self.assertFalse(quality_checks(s,config())['distance_tracking'])
    def test_filtered_target_does_not_hide_raw_action_failure(self):
        s=good_episode();s['action_delta_rms']=.44
        q=quality_checks(s,config());self.assertFalse(q['action_smoothness']);self.assertTrue(q['target_smoothness'])
    def test_matching_gait_passes_new_gates(self):
        self.assertTrue(all(quality_checks(good_episode(),config()).values()))
    def test_quality_selection_prefers_tracking_and_alternation(self):
        good=good_episode();bad=deepcopy(good);bad['forward_m']=.307;bad['action_delta_rms']=.44
        bad['landing_sequence']=['left','left','right','right']*4
        self.assertGreater(quality_score_v4(good),quality_score_v4(bad))
    def test_motionless_cannot_win_selection(self):
        c=config();walk=completed(good_episode(),c);still=good_episode();still.update(forward_m=0,valid_landings=[0,0],forward_landings=[0,0],landing_sequence=[],return_=10000)
        still['return']=10000;still['action_delta_rms']=0
        still=completed(still,c)
        self.assertGreater(aggregate([walk],4)['selection_key'],aggregate([still],4)['selection_key'])


class WorkflowV4Tests(unittest.TestCase):
    def test_smoke_architectures_match_all_transfers(self):
        cfgs=[load_config(ROOT/'configs'/n) for n in ('smoke.json','walk_smoke.json','refine_smoke.json','lp40_smoke.json')]
        for c in cfgs:self.assertEqual(c['ppo']['net_arch'],cfgs[0]['ppo']['net_arch'])
    def test_new_diagnosis_accepts_less_distance_when_tracking_improves(self):
        import diagnose_gait as dg
        c=config();old=good_episode();old.update(forward_m=.307,distance_tracking_abs_error_m=.087,
             target_delta_rms_rad_mean=.012,step_repeat_fraction=.35,action_delta_rms=.437)
        old['landing_sequence']=['left','left','right','right']*3
        new=good_episode()
        def report(s):return {'physics_executed':True,'config':c,'interface':RobotSpec.load(c).interface(c),
                              'no_noise':False,'results':[{'episode_results':[completed(s,c)]}]}
        r=dg.compare(report(old),report(new))
        self.assertNotIn('0.020000/retain_forward_85pct',r['checks'])
        self.assertTrue(r['criteria_met'])
    def test_same_seed_comparison_rejects_different_filter(self):
        import diagnose_gait as dg
        c=config();s=completed(good_episode(),c)
        a={'physics_executed':True,'config':c,'interface':RobotSpec.load(c).interface(c),
           'no_noise':False,'results':[{'episode_results':[s]}]}
        b=deepcopy(a);b['config']['env']['target_lowpass_time_constant_s']=.08
        with self.assertRaises(ValueError):dg.compare(a,b)
    def test_pipeline_contains_v4_train_and_eval(self):
        text=(ROOT/'smoke_test.py').read_text()
        self.assertIn('configs/lp40_smoke.json',text)
        self.assertIn('lp40/final',text)

class PromotionV4Tests(unittest.TestCase):
    def report(self):
        s=completed(good_episode(),config())
        return {'physics_executed':True,'results':[{'command_forward_m_s':.02,'episode_results':[deepcopy(s) for _ in range(5)]}]}
    def test_eighty_percent_does_not_hide_contact(self):
        from check_stage import check_report
        r=self.report();s=r['results'][0]['episode_results'][-1]
        s.update(self_contact_steps=1,is_success=False,terminated=True,time_limit_reached=False)
        self.assertFalse(check_report(r,.8)[0])
    def test_good_trials_can_promote(self):
        from check_stage import check_report
        self.assertTrue(check_report(self.report(),.8)[0])
    def test_partial_not_accepted(self):
        from check_stage import check_report
        r=self.report();r['status']='IN_PROGRESS'
        with self.assertRaises(ValueError):check_report(r,.8)

if __name__=='__main__':unittest.main()
