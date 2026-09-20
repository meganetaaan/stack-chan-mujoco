#!/usr/bin/env python3
"""Query added collision shapes at recorded states; does not rerun dynamics."""
import argparse
import json
from pathlib import Path
import mujoco
import numpy as np
from stackchan_rl.residual import runtime_xml,STATE_SPEC,sha


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--design',type=Path,required=True)
    p.add_argument('--trial',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('use a new output path')
    patch=json.loads((a.design/'BASE_COLLISION_PATCH.json').read_text())
    report=json.loads((a.trial/'report.json').read_text());path=a.trial/'states.npz'
    if sha(path)!=report['trajectory_sha256']:raise ValueError('trajectory hash mismatch')
    if report['interface']['model_sha256']!=patch['source_model_sha256']:raise ValueError('trajectory is from another source model')
    model=mujoco.MjModel.from_xml_string(runtime_xml(a.design/'models/scene.xml'))
    data=mujoco.MjData(model)
    prefixes=tuple('col_'+part['part']+'_' for part in patch['parts'])
    added={i for i in range(model.ngeom) if (model.geom(i).name or '').startswith(prefixes)}
    if len(added)!=sum(x['convex_boxes'] for x in patch['parts']):raise ValueError('added collision count mismatch')
    trace=np.load(path,allow_pickle=False)
    states=trace['state']
    if int(trace['state_spec'])!=int(STATE_SPEC) or states.shape[1]!=mujoco.mj_stateSize(model,STATE_SPEC):
        raise ValueError('incompatible recorded state layout')
    pairs={};hit_frames=0
    for index,state in enumerate(states):
        mujoco.mj_setState(model,data,state,STATE_SPEC);mujoco.mj_forward(model,data)
        hit=False
        for contact in data.contact:
            if not ({contact.geom1,contact.geom2}&added) or contact.dist>=-1e-8:continue
            hit=True
            pair=tuple(sorted((model.geom(contact.geom1).name,model.geom(contact.geom2).name)))
            entry=pairs.setdefault(pair,{'pair':list(pair),'first_frame':index,'first_time_s':float(data.time),
                                        'maximum_penetration_mm':0.})
            entry['maximum_penetration_mm']=max(entry['maximum_penetration_mm'],float(-1000*contact.dist))
        hit_frames+=int(hit)
    result={'scope':'Geometric replay of added collision shapes at recorded policy-boundary states only',
        'dynamics_rerun':False,'physics_substeps_rechecked':False,'mass_variations_needed_for_geometry':False,
        'source_state_sha256':sha(path),'source_report_sha256':sha(a.trial/'report.json'),
        'augmented_model_sha256':sha(a.design/'models/scene.xml'),'audit_source_sha256':sha(__file__),
        'frames_checked':len(states),'new_collision_geoms':len(added),'penetrating_frames':hit_frames,
        'penetration_tolerance_m':1e-8,'sampled_added_shapes_clear':hit_frames==0,'pairs':list(pairs.values())}
    a.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
