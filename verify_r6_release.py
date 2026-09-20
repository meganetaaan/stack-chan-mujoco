#!/usr/bin/env python3
"""Audit a paired evaluation against its published policy, model and seed plan.

This checks provenance and recorded acceptance conditions, not an independent
integration replay of every physics substep.
"""
import argparse
import json
from pathlib import Path
from audit_residual_batch import audit
from stackchan_rl.r6_factory import make_env
from stackchan_rl.residual import ROOT, sha


def read(path):return json.loads(Path(path).read_text())
def same(a,b):return json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)
def require(condition,message):
    if not condition:raise ValueError(message)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkpoint',type=Path,required=True)
    p.add_argument('--evaluation',type=Path,required=True)
    p.add_argument('--seed-plan',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    require(not a.out.exists(),'use a new output file')
    config=read(a.checkpoint/'config.json');training=read(a.checkpoint/'training_result.json')
    policy_hash=sha(a.checkpoint/'policy.zip');config_hash=sha(a.checkpoint/'config.json')
    require(training['trained'] and training['policy_sha256']==policy_hash,'policy provenance')
    require(training['initial_policy_sha256']==sha(a.checkpoint/'initial_policy.zip'),'initial policy provenance')
    require(training['training_config_sha256']==config_hash,'training config provenance')
    plan=read(a.seed_plan);paired=read(a.evaluation/'manifest.json')
    require(paired['complete'] and paired['simulation_criteria_met'],'paired acceptance incomplete or failed')
    require(paired['policy_sha256']==policy_hash and paired['training_config_sha256']==config_hash,'paired policy/config provenance')
    require(paired['seed_plan_sha256']==sha(a.seed_plan) and same(paired['seed_plan'],plan),'seed plan provenance')
    require(config['training']['seed']==plan['heading_training_seed'],'training seed')
    require(not set(plan['fixed_seeds']) & set(plan['randomized_seeds']),'overlapping evaluation seeds')
    design=ROOT/config['design'];frozen=read(design/'FROZEN_FILES.json')
    files=frozen.get('files',frozen.get('sha256'))
    require(isinstance(files,dict) and bool(files),'missing frozen file inventory')
    for name,digest in files.items():require(sha(design/name)==digest,f'changed model artifact: {name}')
    env=make_env(config);results={}
    try:
        require(same(env.fingerprint,read(a.checkpoint/'interface.json')),'checkpoint source/model interface')
        for domain,threshold in [('fixed',20),('randomized',18)]:
            batch=a.evaluation/domain;m=read(batch/'manifest.json');c=read(batch/'config.json')
            require(sha(batch/'manifest.json')==paired['batches'][domain]['manifest_sha256'],'paired batch hash')
            require(m['purpose']=='acceptance' and m['controller']=='trained' and m['domain']==domain,'batch purpose/domain')
            require(m['policy_sha256']==policy_hash and m['training_config_sha256']==config_hash,'batch policy/config provenance')
            expected=json.loads(json.dumps(config));expected.update(episode_s=109.5,randomize=domain=='randomized')
            require(same(c,expected),'evaluation changed more than duration/randomization')
            require(m['seeds']==plan[domain+'_seeds'] and len(m['seeds'])==20 and len(set(m['seeds']))==20,'evaluation seed list')
            state_audit=audit(batch)
            require([x['seed'] for x in m['results']]==m['seeds'],'report seed order')
            success=0
            for entry in m['results']:
                r=read(batch/entry['trial']/'report.json')
                require(same(r['interface'],env.fingerprint),'trial model/source mismatch')
                require(r['domain']==domain and r['controller']=='trained','trial domain/controller')
                env.reset(seed=r['seed'],options={'randomize':domain=='randomized'})
                require(same(env.parameters,r['parameters']),'seeded plant parameters differ')
                ok=(r['failure'] is None and r['time_s']>=109.5-1e-9 and r['crossing_time_s'] is not None
                    and r['crossing_time_s']<=100 and min(r['valid_landings'])>=20)
                require(ok==r['simulation_trial_pass'],'recorded acceptance conditions disagree')
                success+=int(ok)
            require(success>=threshold and success==m['successes'],'acceptance threshold')
            results[domain]={'trials':20,'successes':success,'required':threshold,
                             'state_audit_consistent':state_audit['hashes_and_recorded_states_consistent'],
                             'seeded_parameters_reconstructed':True,'batch_manifest_sha256':sha(batch/'manifest.json')}
    finally:env.close()
    result={'scope':'Policy/model/seed/parameter/recorded-state consistency and declared acceptance criteria',
            'verified':True,'substep_physics_independently_rerun':False,'hardware_tested':False,
            'policy_sha256':policy_hash,'config_sha256':config_hash,'seed_plan_sha256':sha(a.seed_plan),
            'model_file_count':len(files),'batches':results,'verification_source_sha256':sha(__file__)}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
