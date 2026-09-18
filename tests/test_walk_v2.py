"""Objective/event regression tests. Synthetic states, NOT physics rollouts."""
from __future__ import annotations
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import unittest
import numpy as np
from stackchan_rl.config import ROOT, load_config, normalize_config, validate
from stackchan_rl.spec import RobotSpec
from stackchan_rl.walk_events import WalkEventTracker
from stackchan_rl.rewards import reward_terms, success_checks
from stackchan_rl.evaluation import aggregate, classify_behavior


def snapshot(cmd=.02, speed=0.):
    return {"command":np.array([cmd,0.,0.]),"velocity":np.array([speed,0.,0.]),
            "tilt_rad":0.,"height_error":0.,"heading_error":0.,"position_error":np.zeros(2),
            "contacts":np.array([True,True]),"pose_normalized":np.zeros(10),"gyro":np.zeros(3),
            "qd":np.zeros(10),"torque_fraction_sq":.05,"power_W":0.,"action_delta":np.zeros(10),
            "slip_speed_sq":0.,"saturation":0.,"self_contact":False,"swing_mask":np.array([True,False]),
            "foot_height":np.zeros(2),"loads":np.array([4.,4.]),"valid_landings_this_step":0,
            "walk_objective_version":2,"requested_forward_m_s":cmd,"no_step_elapsed_s":4.,
            "no_step_grace_s":1.5,"no_step_ramp_s":1.}


class WalkRewardTests(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(ROOT/'configs/walk_step1.json')
        self.w = self.cfg['reward']

    def terms(self,s,dt=.02):return reward_terms(s,self.w,'walk',dt,False)

    def test_stationary_gets_zero_velocity_credit_for_all_commands(self):
        for c in (.004,.01,.02,.04,.06):
            self.assertAlmostEqual(self.terms(snapshot(c,0.))['velocity'],0.)

    def test_partial_forward_motion_is_better_than_stop(self):
        a,b,c = [sum(self.terms(snapshot(.02,v)).values()) for v in (0,.01,.02)]
        self.assertLess(a,b);self.assertLess(b,c)

    def test_backward_motion_scores_less_than_stop(self):
        self.assertLess(self.terms(snapshot(.02,-.01))['velocity'], self.terms(snapshot())['velocity'])

    def test_no_gait_contact_partial_credit_when_both_feet_stay_down(self):
        self.assertEqual(self.terms(snapshot())['gait_contact'],0.)

    def test_correct_swing_contact_is_rewarded(self):
        s=snapshot();s['contacts'][:]=[False,True]
        self.assertGreater(self.terms(s)['gait_contact'],0.)

    def test_unloading_has_continuous_signal(self):
        s=snapshot();equal=self.terms(s)['unload']
        s['loads'][:]=[2.,6.];partial=self.terms(s)['unload']
        s['loads'][:]=[0.,8.];full=self.terms(s)['unload']
        self.assertEqual(equal,0.);self.assertLess(equal,partial);self.assertLess(partial,full)

    def test_unloading_reward_requires_other_foot_support(self):
        s=snapshot();s['contacts'][:]=False;s['loads'][:]=0
        self.assertEqual(self.terms(s)['unload'],0.)

    def test_clearance_needs_air_and_other_foot_support(self):
        s=snapshot();s['foot_height'][0]=.006
        self.assertEqual(self.terms(s)['clearance'],0.)
        s['contacts'][:]=[False,True]
        self.assertGreater(self.terms(s)['clearance'],0.)
        s['contacts'][:]=[False,False]
        self.assertEqual(self.terms(s)['clearance'],0.)

    def test_excessive_lift_not_rewarded_over_target(self):
        s=snapshot();s['contacts'][:]=[False,True];s['foot_height'][0]=.006
        target=self.terms(s)['clearance'];s['foot_height'][0]=.04
        self.assertLess(self.terms(s)['clearance'],target)

    def test_no_forward_position_hold_in_walk(self):
        s=snapshot();r=self.terms(s)['position'];s['position_error'][0]=.3
        self.assertEqual(self.terms(s)['position'],r)
        s['position_error'][1]=.03;self.assertLess(self.terms(s)['position'],r)

    def test_stuck_penalty_bounded_and_has_grace(self):
        s=snapshot();s['no_step_elapsed_s']=1.
        self.assertEqual(self.terms(s)['no_step'],0.)
        s['no_step_elapsed_s']=2.;p=self.terms(s)['no_step']
        s['no_step_elapsed_s']=100.;q=self.terms(s)['no_step']
        self.assertLess(q,p);self.assertAlmostEqual(q,-self.w['no_step']*.02)

    def test_standing_with_no_steps_better_than_immediate_fall(self):
        # Sanity check on these synthetic states, not a global reward guarantee.
        self.assertGreater(sum(self.terms(snapshot()).values()),0.)
        self.assertEqual(reward_terms(snapshot(),self.w,'walk',.02,True), {'termination':-3.})

    def test_events_zero_at_stop_command(self):
        s=snapshot(0,0)
        for key in ('valid_landings_this_step','rewarded_liftoffs_this_step','rewarded_landings_this_step',
                    'forward_landings_this_step','alternating_landings_this_step'):s[key]=1
        t=self.terms(s)
        for k in ('landing_event','liftoff_event','forward_landing_event','alternating_event','no_step','clearance'):
            self.assertEqual(t[k],0.)

    def test_events_are_discrete_not_scaled_by_dt(self):
        s=snapshot();s['rewarded_landings_this_step']=1;s['forward_landings_this_step']=1
        a,b=self.terms(s,.02),self.terms(s,.01)
        self.assertEqual(a['landing_event'],b['landing_event'])
        self.assertEqual(a['forward_landing_event'],b['forward_landing_event'])
        self.assertAlmostEqual(a['upright'],2*b['upright'])

    def test_velocity_upper_bound(self):
        for v in (-1,.001,.02,.5):
            self.assertLessEqual(abs(self.terms(snapshot(.02,v))['velocity']),self.w['velocity']*.02+1e-10)


class WalkEventTests(unittest.TestCase):
    def setUp(self):
        self.cfg=load_config(ROOT/'configs/walk_step1.json')
        self.tr=WalkEventTracker(.02,self.cfg['env'])
        self.xy=np.array([[0.,.03],[0.,-.03]])
        self.base=0.

    def u(self,c=(True,True),h=(0.,0.),active=True):
        return self.tr.update(c,h,self.xy,self.base,active)

    def settle(self):
        for _ in range(3):self.u()

    def swing(self,i,advance=.01,ticks=8):
        events=[]
        for t in range(ticks):
            c=[True,True];c[i]=False;h=[0.,0.];h[i]=.006
            events.append(self.u(c,h))
        self.xy[i,0]+=advance
        events.append(self.u());events.append(self.u())
        return events

    def test_initial_drop_not_a_step(self):
        for _ in range(10):self.u((False,False),(.01,.01))
        self.settle();self.assertEqual(self.tr.counts.tolist(),[0,0])

    def test_no_steps_for_sliding(self):
        self.settle()
        for _ in range(30):self.xy[:,0]+=.002;self.u()
        self.assertEqual(self.tr.counts.tolist(),[0,0]);self.assertEqual(self.tr.liftoffs.tolist(),[0,0])

    def test_landing_waits_for_contact_confirmation(self):
        self.settle()
        for _ in range(5):self.u((False,True),(.006,0))
        self.xy[0,0]=.01
        self.u();self.assertEqual(self.tr.counts[0],0)
        self.u();self.assertEqual(self.tr.counts[0],1)

    def test_chatter_not_accumulated_as_airtime(self):
        self.settle()
        for _ in range(20):self.u((False,True),(.003,0));self.u()
        self.u();self.assertEqual(self.tr.counts.tolist(),[0,0])

    def test_unconfirmed_touch_not_repeated_landing(self):
        self.settle()
        for _ in range(5):self.u((False,True),(.006,0))
        self.u();self.u((False,True),(.006,0));self.settle()
        self.assertEqual(self.tr.counts[0],0)
        self.assertGreater(self.tr.rejected['unconfirmed_touch'],0)

    def test_hopping_without_other_support_rejected(self):
        self.settle()
        for _ in range(10):self.u((False,False),(.01,.01))
        self.xy[:,0]+=.01;self.settle()
        self.assertEqual(self.tr.counts.tolist(),[0,0])
        self.assertEqual(self.tr.forward_counts.tolist(),[0,0])

    def test_alternating_footsteps_and_forward_steps(self):
        self.settle();a=self.swing(0,ticks=12);b=self.swing(1,ticks=12)
        self.assertEqual(self.tr.counts.tolist(),[1,1]);self.assertEqual(self.tr.forward_counts.tolist(),[1,1])
        self.assertEqual(self.tr.liftoffs.tolist(),[1,1]);self.assertEqual(self.tr.sequence,['left','right'])
        self.assertEqual(sum(x['alternating_landings_this_step'] for x in a+b),1)

    def test_repeated_same_leg_no_lift_or_alternation_bonus(self):
        self.settle();a=self.swing(0,ticks=12);b=self.swing(0,ticks=12)
        self.assertEqual(sum(x['rewarded_liftoffs_this_step'] for x in a),1)
        self.assertEqual(sum(x['rewarded_liftoffs_this_step'] for x in b),0)
        self.assertEqual(sum(x['rewarded_landings_this_step'] for x in b),0)

    def test_foot_lift_in_place_not_forward_landing(self):
        self.settle();self.swing(0,advance=0)
        self.assertEqual(self.tr.counts[0],1);self.assertEqual(self.tr.forward_counts[0],0)

    def test_foot_forward_backward_cannot_refarm_old_record(self):
        self.settle();self.swing(0,.01);self.swing(0,-.01);self.swing(0,.01)
        self.assertEqual(self.tr.forward_counts[0],1)

    def test_body_rocking_does_not_refarm_progress(self):
        self.settle();self.base=.01;a=self.u();self.base=0;self.u();self.base=.01;b=self.u()
        self.assertAlmostEqual(a['new_forward_distance_m'],.01)
        self.assertEqual(b['new_forward_distance_m'],0.)

    def test_bare_unload_is_diagnostic_not_qualified_lift(self):
        self.settle()
        for _ in range(10):self.u((False,True),(0,0))
        self.settle();self.assertEqual(self.tr.liftoffs[0],0)
        self.assertEqual(self.tr.raw_unloads[0],1)
        self.assertGreater(self.tr.rejected['low_clearance'],0)

    def test_hanging_one_foot_does_not_reset_no_step_timer(self):
        self.settle()
        for _ in range(150):r=self.u((False,True),(.006,0))
        self.assertGreater(r['no_step_elapsed_s'],2.9)
        self.assertEqual(self.tr.liftoffs[0],1)
        self.assertEqual(self.tr.counts[0],0)

    def test_no_stagnation_penalty_timer_when_stopped(self):
        for _ in range(100):r=self.u(active=False)
        self.assertEqual(r['no_step_elapsed_s'],0.)


class CompatibilityAndSelectionTests(unittest.TestCase):
    def test_old_checkpoint_config_remains_legacy(self):
        raw=json.loads((ROOT/'docs/resolved_walk_config.json').read_text())
        c=normalize_config(raw)
        self.assertEqual(c['env']['walk_objective_version'],1)
        self.assertEqual(c['train']['selection_version'],1)
        self.assertFalse(c['transfer']['actor_only'])
        self.assertEqual(c['reward']['velocity'],raw['reward']['velocity'])

    def test_actor_interface_unchanged_for_all_stages(self):
        c=load_config(ROOT/'configs/stand.json');orig=RobotSpec.load(c).interface(c)
        for i in (1,2,3):
            c=load_config(ROOT/f'configs/walk_step{i}.json')
            self.assertEqual(orig,RobotSpec.load(c).interface(c))

    def test_curriculum_commands_and_no_stop_at_first(self):
        c=[load_config(ROOT/f'configs/walk_step{i}.json') for i in (1,2,3)]
        self.assertEqual(c[0]['env']['command_forward_range_m_s'],[.02,.02])
        self.assertEqual(c[0]['env']['command_zero_probability'],0.)
        self.assertEqual(c[1]['env']['command_forward_range_m_s'],[.02,.04])
        self.assertIn(0.,c[2]['train']['eval_commands_m_s'])
        self.assertGreater(c[2]['env']['command_zero_probability'],0.)

    def test_invalid_objective_and_transfer_rejected(self):
        c=load_config();c['transfer']['reset_log_std']=10
        with self.assertRaises(ValueError):validate(c)
        c=load_config();c['env']['walk_objective_version']=999
        with self.assertRaises(ValueError):validate(c)

    @staticmethod
    def summary(forward=0.,landings=(0,0),forward_landings=(0,0),reward=1000.):
        return {'task':'walk','is_success':False,'return':reward,'duration_s':12.,'episode_limit_s':12.,
                'requested_forward_m_s':.02,'commanded_distance_m':.22,'time_limit_reached':True,
                'terminated':False,'failure_reason':None,'forward_m':forward,'lateral_m':0.,
                'valid_landings':list(landings),'forward_landings':list(forward_landings),
                'mean_abs_forward_velocity_error_m_s':.02,'bad_contact_steps':0,'self_contact_steps':0,
                'min_height_ratio':1.,'max_tilt_deg':3.,'max_heading_deg':0.,'max_horizontal_drift_m':abs(forward),
                'double_support_fraction':1.,'flight_fraction':0.,'landing_sequence':['left','right','left','right'] if min(landings)>=2 else []}

    def test_high_reward_stationary_not_preferred_to_physical_progress(self):
        stuck=self.summary();walk=self.summary(.05,(2,2),(1,1),reward=10.)
        self.assertGreater(aggregate([walk],2)['selection_key'],aggregate([stuck],2)['selection_key'])

    def test_synthetic_ranking_does_not_claim_physical_execution(self):
        r=aggregate([self.summary()],2)
        # aggregate is an evaluation helper; synthetic audit explicitly labels
        # its own report not-physics and does not reuse this field as evidence.
        self.assertFalse(r['physics_executed'])
        self.assertEqual(r['behavior_counts'],{'no_verified_steps':1})

    def test_success_still_requires_real_steps(self):
        c=load_config(ROOT/'configs/walk_step1.json')
        s=self.summary(.22,(0,0),(0,0))
        self.assertFalse(all(success_checks(s,c).values()))
        s=self.summary(.03,(2,2),(1,1));self.assertTrue(all(success_checks(s,c).values()))

    def test_stationary_not_called_stand_success_under_forward_command(self):
        self.assertEqual(classify_behavior(self.summary(-.005)), 'no_verified_steps')

    def test_stop_evaluation_not_rejected_for_zero_landings(self):
        c=load_config(ROOT/'configs/walk_step3.json');s=self.summary()
        s['requested_forward_m_s']=0.;s['commanded_distance_m']=0.
        self.assertTrue(all(success_checks(s,c).values()))


@unittest.skipUnless(importlib.util.find_spec('torch'), 'PyTorch missing')
class TransferTensorTests(unittest.TestCase):
    """Real torch tensors in a small SB3-shaped module, NOT SB3 execution."""
    def test_actor_only_preserves_mean_and_reinitializes_critic_and_noise(self):
        import torch
        from torch import nn
        from stackchan_rl.transfer import transfer_policy
        class Policy(nn.Module):
            def __init__(self):
                super().__init__();self.mlp_extractor=nn.Module()
                self.mlp_extractor.policy_net=nn.Sequential(nn.Linear(61,8),nn.Tanh())
                self.mlp_extractor.value_net=nn.Sequential(nn.Linear(61,8),nn.Tanh())
                self.action_net=nn.Linear(8,10);self.value_net=nn.Linear(8,1)
                self.log_std=nn.Parameter(torch.full((10,),-5.))
        src,dst=Policy(),Policy()
        before={k:v.clone() for k,v in dst.state_dict().items() if 'value' in k}
        obs=torch.zeros(1,61)
        mean=src.action_net(src.mlp_extractor.policy_net(obs))
        transfer_policy(src,dst,actor_only=True,reset_log_std=-1.)
        torch.testing.assert_close(mean,dst.action_net(dst.mlp_extractor.policy_net(obs)))
        for k,v in before.items():torch.testing.assert_close(v,dst.state_dict()[k])
        torch.testing.assert_close(dst.log_std,torch.full((10,),-1.))
        self.assertFalse(torch.equal(src.value_net.weight,dst.value_net.weight))

class WorkflowTests(unittest.TestCase):
    def test_smoke_configs_can_transfer_architecture_and_interface(self):
        a=load_config(ROOT/'configs/smoke.json');b=load_config(ROOT/'configs/walk_smoke.json')
        self.assertEqual(a['ppo']['net_arch'],b['ppo']['net_arch'])
        self.assertEqual(RobotSpec.load(a).interface(a),RobotSpec.load(b).interface(b))

    def test_stage_gate_rejects_success_flag_without_steps(self):
        from check_stage import check_report
        s=CompatibilityAndSelectionTests.summary();s.update(is_success=True,success_checks={'mock':True})
        report={'physics_executed':True,'results':[{'command_forward_m_s':.02,'episode_results':[s]}]}
        self.assertFalse(check_report(report,.6)[0])
        s.update(forward_m=.03,valid_landings=[2,2],forward_landings=[1,1])
        self.assertTrue(check_report(report,.6)[0])

    def test_stop_group_cannot_hide_failed_walk_in_gate(self):
        from check_stage import check_report
        stop=CompatibilityAndSelectionTests.summary();stop.update(is_success=True,success_checks={'standing':True},requested_forward_m_s=0.)
        walk=CompatibilityAndSelectionTests.summary()
        report={'physics_executed':True,'results':[
            {'command_forward_m_s':0.,'episode_results':[stop]*10},
            {'command_forward_m_s':.02,'episode_results':[walk]}]}
        self.assertFalse(check_report(report,.6)[0])
