#!/usr/bin/env python3
"""Check every mechanical CAD pair at nominal and symmetric-splay poses.

No same-link or parent-child pairs are excluded. Not a swept-volume proof.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--design", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    args = p.parse_args()
    design = args.design.resolve()
    sys.path[:0] = [str(design / "cad"), str(design / "src")]
    import numpy as np
    from build import build, posed
    from tab5_biped.core import all_frames, nominal, PARAMS
    start = time.monotonic()
    parts = [part for part in build() if part.role != "visual"]
    q, base = nominal()
    rows = []
    for angle in [0, 6, 6.5, 10, 16]:
        qq = q.copy()
        a = np.deg2rad(angle)
        qq[[0, 4, 5, 9]] = [a, -a, -a, a]
        frames = all_frames(qq, base)
        shapes = [posed(part.shape, frames[part.link]) for part in parts]
        bounds = []
        for shape in shapes:
            b = shape.BoundingBox()
            bounds.append(np.array([[b.xmin, b.ymin, b.zmin], [b.xmax, b.ymax, b.zmax]]))
        hits, calls = [], 0
        for i, j in itertools.combinations(range(len(parts)), 2):
            overlap = np.minimum(bounds[i][1], bounds[j][1])-np.maximum(bounds[i][0], bounds[j][0])
            if np.min(overlap) <= 1e-5:
                continue
            calls += 1
            volume = shapes[i].intersect(shapes[j]).Volume()
            if volume > .01:
                hits.append({"a": parts[i].name, "b": parts[j].name, "overlap_mm3": volume})
        rows.append({"outward_hip_roll_deg_each": angle, "brep_calls": calls, "findings": hits})
        print(f"{angle:g} deg: {len(hits)} intersections, {calls} B-rep calls", flush=True)
    result = {"revision": PARAMS["revision"], "threshold_mm3": .01,
              "scope": "All mechanical pairs at five poses; no swept-volume, tolerance, cable or fastener proof",
              "mechanical_parts": len(parts), "same_link_and_adjacent_pairs_included": True,
              "manufacturing_release": False, "walking_validated": False,
              "input_sha256": {name: hashlib.sha256((design / name).read_bytes()).hexdigest()
                               for name in ["robot.json", "cad/build.py", "cad/r4_geometry.py",
                                            "src/tab5_biped/core.py", "docs/underside_cutouts.json"]},
              "sampled_poses_clear": all(not r["findings"] for r in rows),
              "elapsed_s": time.monotonic()-start, "results": rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+"\n")
    return 0 if result["sampled_poses_clear"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
