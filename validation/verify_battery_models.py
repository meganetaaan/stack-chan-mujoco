#!/usr/bin/env python3
"""Verify battery replacement, unchanged leg geometry, and box inertia."""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--candidates", type=Path, nargs="+", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    baseline = json.loads((args.baseline / "models/components.json").read_text())["parts"]
    original = {r["name"]: r for r in baseline}
    original_xml = ET.parse(args.baseline / "models/scene.xml").getroot()
    def joints(root):
        return [(body.get("name"), body.get("pos"), body.find("joint").attrib)
                for body in root.findall(".//body") if body.find("joint") is not None]
    results = []
    for folder in args.candidates:
        robot = json.loads((folder / "robot.json").read_text())
        spec = robot["battery_envelope"]
        parts = json.loads((folder / "models/components.json").read_text())["parts"]
        battery = [r for r in parts if r["name"] == "battery_2S_reservation"]
        checks = {"exactly_one_battery": len(battery) == 1,
                  "same_component_names": sorted(r["name"] for r in parts) == sorted(original),
                  "same_joint_origins_axes_limits": joints(ET.parse(folder / "models/scene.xml").getroot()) == joints(original_xml),
                  "replaced_not_added_mass": bool(np.isclose(sum(r["mass_kg"] for r in parts),
                      sum(r["mass_kg"] for r in baseline)-original["battery_2S_reservation"]["mass_kg"]+spec["mass_kg"], atol=1e-12, rtol=0))}
        unchanged = [r["name"] for r in baseline if r["name"] != "battery_2S_reservation"]
        checks["all_other_37_meshes_identical"] = all(
            (folder / "models/meshes" / (name+".stl")).read_bytes() ==
            (args.baseline / "models/meshes" / (name+".stl")).read_bytes() for name in unchanged)
        if len(battery) == 1:
            item = battery[0]
            size = np.array(spec["size_mm"])/1000
            inertia = np.diag(spec["mass_kg"]*(np.sum(size**2)-size**2)/12)
            checks["box_inertia_matches_analytic"] = bool(np.allclose(item["inertia_kg_m2"], inertia, rtol=0, atol=1e-12))
            checks["com_matches_requested_placement"] = bool(np.allclose(item["com_m"], np.array(spec["center_base_mm"])/1000, rtol=0, atol=1e-12))
        results.append({"candidate": folder.name, "checks": checks, "passed": all(checks.values()),
                        "robot_sha256": hashlib.sha256((folder / "robot.json").read_bytes()).hexdigest()})
    report = {"scope": "Mass and geometry generation checks, not physical validation", "results": results,
              "passed": all(row["passed"] for row in results)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+"\n")
    print("PASS" if report["passed"] else "FAIL")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    main()
