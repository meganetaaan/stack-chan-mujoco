#!/usr/bin/env python3
"""Rebuild the archived R5-A CAD and physics model in a new output directory."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--hip-half-spacing-mm", type=float,
                   help="Experimental 19..28 mm leg-spacing variant; not a fabrication release")
    args = p.parse_args()
    source = ROOT / "design/r5a_source"
    out = args.out.resolve()
    if out == source or source in out.parents:
        p.error("output must be outside the immutable source archive")
    if out.exists():
        p.error("output already exists; use a new directory to preserve previous evidence")
    spacing = args.hip_half_spacing_mm
    if spacing is not None and (not math.isfinite(spacing) or not 19 <= spacing <= 28):
        p.error("experimental half spacing must be between 19 and 28 mm")
    manifest = json.loads((source / "SOURCE_MANIFEST.json").read_text())
    for name, digest in manifest["unmodified_source_sha256"].items():
        if hashlib.sha256((source / name).read_bytes()).hexdigest() != digest:
            p.error(f"archived source changed: {name}")
    shutil.copytree(source, out, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (out / "hardware").mkdir()
    if spacing is not None:
        robot = json.loads((out / "robot.json").read_text())
        delta = spacing - robot["kinematics"]["hip_half_spacing_mm"]
        robot["revision"] = f"r6-experimental-hip-{spacing:g}mm"
        robot["kinematics"]["hip_half_spacing_mm"] = spacing
        (out / "robot.json").write_text(json.dumps(robot, indent=2)+"\n")
        # Every leg and base-mounted cradle moves rigidly by the same delta.
        # Translate the inherited sampled bottom-opening envelope with each leg.
        path = out / "docs/underside_cutouts.json"
        polygons = json.loads(path.read_text())
        for side, points in polygons.items():
            for point in points:
                point[1] += delta * (1 if side == "left" else -1)
        path.write_text(json.dumps(polygons)+"\n")
        path = out / "cad/build.py"
        text = path.read_text()
        marker = "(-50.2,sg*19,51)"
        if text.count(marker) != 1:
            raise RuntimeError("Archived mounting-rail implementation changed; review adaptation")
        path.write_text(text.replace(marker, "(-50.2,sg*KIN['hip_half_spacing_mm'],51)"))
    for script in ("cad/build.py", "export_models.py", "cad/validate_export.py"):
        subprocess.run([sys.executable, str(out / script)], cwd=out, check=True)
    if spacing is not None:
        import xml.etree.ElementTree as ET
        path = out / "models/scene.xml"
        tree = ET.parse(path)
        tree.getroot().set("model", robot["revision"])
        ET.indent(tree, space="  ")
        tree.write(path, encoding="utf-8", xml_declaration=True)
        (out / "DESIGN_VARIANT.json").write_text(json.dumps({
            "revision": robot["revision"], "hip_half_spacing_mm": spacing,
            "base_source_manifest": manifest, "manufacturing_release": False,
            "walking_validated": False,
            "changes": ["leg joint origins and fixed cradles", "body mounting rails",
                        "translated sampled underside opening", "CAD-derived mass and inertia"],
            "needs_validation": ["full assembly clearance", "mount strength and tolerances",
                                 "collision proxy conservatism", "gait dynamics", "hardware"]
        }, indent=2)+"\n")
    print(f"CAD rebuilt at {out}; no physical walking or manufacturing validation claimed")


if __name__ == "__main__":
    main()
