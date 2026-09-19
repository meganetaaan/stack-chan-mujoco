#!/usr/bin/env python3
"""Rebuild the archived R5-A CAD and physics model in a new output directory."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
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
    p.add_argument("--battery-layout", type=Path,
                   help="Planning-envelope JSON; requires an experimental hip spacing")
    p.add_argument("--underside-cutouts", type=Path,
                   help="Sample-derived opening polygons; requires experimental hip spacing")
    p.add_argument("--leg-clearance-relief", action="store_true",
                   help="Experimental cradle notch and rerouted gimbal arm; requires gait opening")
    p.add_argument("--boot-collar-relief", action="store_true",
                   help="Local inner collar recess; requires leg relief")
    args = p.parse_args()
    if args.leg_clearance_relief and args.underside_cutouts is None:
        p.error("--leg-clearance-relief requires --underside-cutouts")
    if args.boot_collar_relief and not args.leg_clearance_relief:
        p.error("--boot-collar-relief requires --leg-clearance-relief")
    source = ROOT / "design/r5a_source"
    out = args.out.resolve()
    if out == source or source in out.parents:
        p.error("output must be outside the immutable source archive")
    if out.exists():
        p.error("output already exists; use a new directory to preserve previous evidence")
    spacing = args.hip_half_spacing_mm
    if spacing is not None and (not math.isfinite(spacing) or not 19 <= spacing <= 28):
        p.error("experimental half spacing must be between 19 and 28 mm")
    cutouts = None
    if args.underside_cutouts is not None:
        if spacing is None:
            p.error("--underside-cutouts requires --hip-half-spacing-mm")
        cutouts = json.loads(args.underside_cutouts.read_text())
        if set(cutouts) != {"left", "right"}:
            p.error("cutouts must contain left and right polygons")
        for points in cutouts.values():
            if not isinstance(points, list) or len(points) < 3:
                p.error("each cutout requires at least three points")
            for point in points:
                if not isinstance(point, list) or len(point) != 2 or any(
                    type(v) not in (int, float) or not math.isfinite(v) or abs(v) > 60
                    for v in point
                ):
                    p.error("cutout coordinates must be finite and within +/-60 mm")
    battery = None
    if args.battery_layout is not None:
        if spacing is None:
            p.error("--battery-layout requires --hip-half-spacing-mm")
        battery = json.loads(args.battery_layout.read_text())
        if not isinstance(battery.get("layout_id"), str) or not re.fullmatch(r"[a-z0-9_-]+", battery["layout_id"]):
            p.error("battery layout_id must be a lowercase identifier")
        for key in ("size_mm", "center_base_mm"):
            value = battery.get(key)
            if not isinstance(value, list) or len(value) != 3 or any(type(v) not in (int, float) or not math.isfinite(v) for v in value):
                p.error(f"battery {key} must contain three finite numbers")
        if any(v <= 0 for v in battery["size_mm"]):
            p.error("battery dimensions must be positive")
        if type(battery.get("mass_kg")) not in (int, float) or not math.isfinite(battery["mass_kg"]) or battery["mass_kg"] <= 0:
            p.error("battery mass_kg must be positive and finite")
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
        if battery is not None:
            robot["revision"] += "-" + battery["layout_id"]
            robot["battery_envelope"] = battery
            robot["mass_assumptions"]["upper_2s_battery_kg"] = battery["mass_kg"]
        if cutouts is not None:
            robot["revision"] += "-gait-opening"
        if args.leg_clearance_relief:
            robot["revision"] += "-leg-relief"
        if args.boot_collar_relief:
            robot["revision"] += "-collar-relief"
        robot["kinematics"]["hip_half_spacing_mm"] = spacing
        (out / "robot.json").write_text(json.dumps(robot, indent=2)+"\n")
        # Every leg and base-mounted cradle moves rigidly by the same delta.
        # Translate the inherited sampled bottom-opening envelope with each leg.
        path = out / "docs/underside_cutouts.json"
        polygons = json.loads(path.read_text())
        for side, points in polygons.items():
            for point in points:
                point[1] += delta * (1 if side == "left" else -1)
        path.write_text(json.dumps(cutouts if cutouts is not None else polygons)+"\n")
        path = out / "cad/build.py"
        text = path.read_text()
        marker = "(-50.2,sg*19,51)"
        if text.count(marker) != 1:
            raise RuntimeError("Archived mounting-rail implementation changed; review adaptation")
        path.write_text(text.replace(marker, "(-50.2,sg*KIN['hip_half_spacing_mm'],51)"))
        if battery is not None:
            path = out / "cad/r4_geometry.py"
            lines = path.read_text().splitlines()
            indices = [i for i, line in enumerate(lines) if line.strip().startswith("add('battery_2S_reservation',")]
            if len(indices) != 1:
                raise RuntimeError("Archived battery implementation changed; review adaptation")
            lines[indices[0]] = "    add('battery_2S_reservation','base',box(P['battery_envelope']['size_mm'],P['battery_envelope']['center_base_mm']),'hardware','battery',P['battery_envelope']['mass_kg'],note='Planning box envelope, not a validated battery mount; electrical compatibility unverified')"
            path.write_text("\n".join(lines)+"\n")
    if args.leg_clearance_relief:
        path = out / "cad/r4_geometry.py"
        text = path.read_text()
        adaptations = {
            "        add(side+'_fixed_roll_cradle'":
                "        # Local lower-lip relief; upper web and bearing axis retained.\n"
                "        holder=holder.cut(box((7,28,5),(-11,y,14.5)))\n"
                "        add(side+'_fixed_roll_cradle'",
            "(-44,19),(-55,19)": "(-44,15),(-55,19)",
            "(-49,13),(-8,2)": "(-49,9),(-8,2)",
        }
        if args.boot_collar_relief:
            adaptations["    # Inboard sweep channel: the two-axis ankle needs lateral clearance."] = (
                "    # Local internal top-collar recess; external sole and side outline retained.\n"
                "    out=out.cut(box((42,56,8),(1,0,38),r=2,edge='|Z'))\n"
                "    # Inboard sweep channel: the two-axis ankle needs lateral clearance.")
        for old, new in adaptations.items():
            if text.count(old) != 1:
                raise RuntimeError("Archived leg implementation changed; review relief adaptation")
            text = text.replace(old, new)
        path.write_text(text)
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
            "battery_planning_envelope": battery,
            "leg_clearance_relief": args.leg_clearance_relief,
            "boot_collar_relief": args.boot_collar_relief,
            "underside_cutouts_sha256": hashlib.sha256(args.underside_cutouts.read_bytes()).hexdigest() if cutouts is not None else None,
            "changes": ["leg joint origins and fixed cradles", "body mounting rails",
                        "supplied gait opening" if cutouts is not None else "translated sampled underside opening", "CAD-derived mass and inertia"],
            "needs_validation": ["full assembly clearance", "mount strength and tolerances",
                                 "collision proxy conservatism", "gait dynamics", "hardware"]
        }, indent=2)+"\n")
    print(f"CAD rebuilt at {out}; no physical walking or manufacturing validation claimed")


if __name__ == "__main__":
    main()
