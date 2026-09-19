#!/usr/bin/env python3
"""Check every mechanical CAD pair at nominal and symmetric-splay poses.

No same-link or parent-child pairs are excluded. Not a swept-volume proof.
"""
import argparse
import hashlib
import csv
import itertools
import json
from pathlib import Path
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--design", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--trajectory-terminal-csv", type=Path,
                   help="Check the actual last joint pose of a diagnostic CSV instead of five splay poses")
    args = p.parse_args()
    design = args.design.resolve()
    sys.path[:0] = [str(design / "cad"), str(design / "src")]
    import numpy as np
    from build import build, posed
    from tab5_biped.core import all_frames, nominal, PARAMS, JOINT_NAMES
    start = time.monotonic()
    parts = [part for part in build() if part.role != "visual"]
    q, base = nominal()
    rows, states = [], []
    if args.trajectory_terminal_csv is not None:
        with args.trajectory_terminal_csv.open() as handle:
            trajectory = list(csv.DictReader(handle))
        if not trajectory:
            p.error("trajectory has no samples")
        qq = np.array([float(trajectory[-1][name]) for name in JOINT_NAMES])
        if not np.isfinite(qq).all():
            p.error("terminal joint state is nonfinite")
        states = [("trajectory_terminal", qq)]
    else:
        for angle in [0, 6, 6.5, 10, 16]:
            qq = q.copy()
            a = np.deg2rad(angle)
            qq[[0, 4, 5, 9]] = [a, -a, -a, a]
            states.append((angle, qq))
    for angle, qq in states:
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
        rows.append({"pose": angle, "q_rad": qq.tolist(), "brep_calls": calls, "findings": hits})
        print(f"pose={angle}: {len(hits)} intersections, {calls} B-rep calls", flush=True)
    result = {"revision": PARAMS["revision"], "threshold_mm3": .01,
              "scope": "All mechanical pairs at supplied sampled poses; no swept-volume, tolerance, cable or fastener proof",
              "trajectory_sha256": hashlib.sha256(args.trajectory_terminal_csv.read_bytes()).hexdigest() if args.trajectory_terminal_csv else None,
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
