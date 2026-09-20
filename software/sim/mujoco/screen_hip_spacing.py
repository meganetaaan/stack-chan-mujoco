#!/usr/bin/env python3
"""B-rep cross-leg clearance study; excludes body interfaces and fabrication fit.

Moves each unchanged leg assembly outward, including its base-mounted parts.
This is a packaging experiment, not a released robot variant.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "design/r5a_source"
sys.path[:0] = [str(SOURCE / "cad"), str(SOURCE / "src")]
import numpy as np
from r4_geometry import build, posed
from tab5_biped.core import KIN, all_frames, nominal, fk_leg


def bounds(shape):
    b = shape.BoundingBox()
    return np.array([[b.xmin, b.ymin, b.zmin], [b.xmax, b.ymax, b.zmax]])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--half-spacings-mm", type=float, nargs="+", default=[19, 22, 25, 28])
    parser.add_argument("--angles-deg", type=float, nargs="+", default=[0, 6, 6.5, 10, 16])
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if any(not np.isfinite(x) or x < 19 for x in args.half_spacings_mm):
        parser.error("half spacings must be finite and at least 19 mm")
    if any(not np.isfinite(x) or not 0 <= x <= np.rad2deg(.28) for x in args.angles_deg):
        parser.error("angles must be in the existing 0..0.28 rad hip-roll range")
    start = time.monotonic()
    legs = [p for p in build() if p.name.startswith(("left_", "right_"))]
    original_spacing = KIN["hip_half_spacing_mm"]
    q, base = nominal()
    pairs = [(i, j) for i, j in itertools.combinations(range(len(legs)), 2)
             if legs[i].name.split("_")[0] != legs[j].name.split("_")[0]]
    rows = []
    for spacing in args.half_spacings_mm:
        KIN["hip_half_spacing_mm"] = spacing
        local = [p.shape.translate((0, (1 if p.name.startswith("left_") else -1) *
                                   (spacing-original_spacing), 0)) if p.link == "base" else p.shape
                 for p in legs]
        for angle in args.angles_deg:
            qq = q.copy()
            a = np.deg2rad(angle)
            qq[[0, 4, 5, 9]] = [a, -a, -a, a]
            frames = all_frames(qq, base)
            shapes = [posed(s, frames[p.link]) for p, s in zip(legs, local)]
            boxes = [bounds(s) for s in shapes]
            hits, narrow = [], 0
            for i, j in pairs:
                overlap = np.minimum(boxes[i][1], boxes[j][1])-np.maximum(boxes[i][0], boxes[j][0])
                if np.min(overlap) <= 1e-5:
                    continue
                narrow += 1
                volume = shapes[i].intersect(shapes[j]).Volume()
                if volume > .01:
                    hits.append({"a": legs[i].name, "b": legs[j].name, "overlap_mm3": volume})
            feet = [fk_leg(qq[i*5:i*5+5], side, base)[1][:3, 3]
                    for i, side in enumerate(("left", "right"))]
            row = {"hip_half_spacing_mm": spacing, "outward_hip_roll_deg_each": angle,
                   "sole_center_spacing_mm": float(abs(feet[0][1]-feet[1][1])*1000),
                   "cross_leg_pair_count": len(pairs), "brep_calls": narrow,
                   "findings": hits, "sample_clear": not hits}
            rows.append(row)
            print(f"half-spacing={spacing:g} mm, angle={angle:g} deg: {len(hits)} intersections", flush=True)
    KIN["hip_half_spacing_mm"] = original_spacing
    report = {"scope": "cross-leg B-rep intersection study at sampled poses only",
              "manufacturing_release": False, "walking_validated": False,
              "threshold_mm3": .01, "elapsed_s": time.monotonic()-start,
              "source_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [Path(__file__).resolve(), SOURCE / "robot.json",
                                          SOURCE / "cad/r4_geometry.py", SOURCE / "src/tab5_biped/core.py"]},
              "excluded": ["body and mounting bridges", "same-leg pairs", "fasteners and cables",
                           "manufacturing tolerances", "continuous swept volume", "dynamics"],
              "results": rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")


if __name__ == "__main__":
    main()
