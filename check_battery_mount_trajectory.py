#!/usr/bin/env python3
"""Check new tray and shifted battery against CAD at recorded joint poses.

Sampling is explicit; this is not a swept-volume or dynamics validation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design', type=Path, required=True)
    p.add_argument('--mount', type=Path, required=True)
    p.add_argument('--trial', type=Path, required=True)
    p.add_argument('--stride', type=int, default=250)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists() or a.stride < 1:
        p.error('positive stride and new output file required')
    design = a.design.resolve()
    sys.path[:0] = [str(design/'cad'), str(design/'src')]
    import cadquery as cq
    import numpy as np
    from build import build
    from r4_geometry import posed
    from tab5_biped.core import all_frames, nominal
    report = json.loads((a.trial/'report.json').read_text())
    state_path = a.trial/'states.npz'
    if sha(state_path) != report['trajectory_sha256']:
        raise ValueError('trajectory hash mismatch')
    with np.load(state_path, allow_pickle=False) as trace:
        states = trace['state']
    joints = states[:, 8:18]
    indices = sorted(set(range(0, len(states), a.stride)) | {len(states)-1} |
                     set(np.argmin(joints, axis=0).tolist()) | set(np.argmax(joints, axis=0).tolist()))
    parts = {x.name:x for x in build() if x.role != 'visual'}
    target_names = ['battery_tray', 'battery_2S_reservation']
    target_names += sorted(x.stem for x in a.mount.glob('battery_*envelope*.step'))
    targets = {name:cq.importers.importStep(str(a.mount/(name+'.step'))).val()
               for name in target_names}
    parts['body_shroud'].shape = cq.importers.importStep(str(a.mount/'body_shroud.step')).val()
    _, base = nominal()

    def bounds(shape):
        b = shape.BoundingBox()
        return np.array([[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]])

    rows = []
    for index in indices:
        frames = all_frames(joints[index], base)
        hits = []
        queries = 0
        for name, local in targets.items():
            shape = posed(local, frames['base']); bb = bounds(shape)
            for other, part in parts.items():
                if other in targets:
                    continue  # battery/tray intentional bottom contact checked by build script
                candidate = posed(part.shape, frames[part.link]); cb = bounds(candidate)
                overlap = np.minimum(bb[1],cb[1])-np.maximum(bb[0],cb[0])
                if np.min(overlap) <= 1e-5:
                    continue
                queries += 1
                volume = shape.intersect(candidate).Volume()
                if volume > .01:
                    hits.append({'a':name,'b':other,'overlap_mm3':volume})
        rows.append({'frame':index,'time_s':float(states[index,0]),'q_rad':joints[index].tolist(),
                     'brep_queries':queries,'findings':hits})
        print(f'frame {index}: {len(hits)} intersections', flush=True)
    result = {'scope':'Specified mount components against existing mechanical parts at sampled recorded poses; no swept-volume proof or dynamics rerun',
              'target_parts':target_names,
              'mount_internal_pairs':'Checked statically in mount build report; all mount components are on the same rigid base',
              'sample_selection':'stride plus terminal and per-joint minima/maxima', 'stride':a.stride,
              'recorded_frames':len(states),'checked_frames':len(rows),'threshold_mm3':.01,
              'sampled_poses_clear':all(not r['findings'] for r in rows),
              'source_trajectory_sha256':sha(state_path), 'source_report_sha256':sha(a.trial/'report.json'),
              'checker_sha256':sha(__file__),
              'cad_sha256':{name:sha(a.mount/(name+'.step')) for name in (*targets, 'body_shroud')},
              'design_sha256':{name:sha(design/name) for name in ('robot.json','cad/build.py','cad/r4_geometry.py','src/tab5_biped/core.py')},
              'results':rows}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    return 0 if result['sampled_poses_clear'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
