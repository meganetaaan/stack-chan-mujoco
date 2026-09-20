#!/usr/bin/env python3
"""Compare regenerated R5 assets byte-for-byte, then compile the actual MJCF."""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rebuild", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    manifest = json.loads((ROOT / "assets/r5a/SOURCE_MANIFEST.json").read_text())
    rows = []
    for name in manifest["files"]:
        original = ROOT / "assets/r5a" / name
        regenerated = args.rebuild / (name if name == "robot.json" else "models/" + name)
        digest = hashlib.sha256(regenerated.read_bytes()).hexdigest()
        rows.append({"file": name, "sha256": digest,
                     "matches_baseline": digest == hashlib.sha256(original.read_bytes()).hexdigest(),
                     "matches_original_manifest": digest == manifest["files"][name]})
    model = mujoco.MjModel.from_xml_path(str((args.rebuild / "models/scene.xml").resolve()))
    dimensions = [model.nq, model.nv, model.nu]
    export_report = json.loads((args.rebuild / "reports/exports.json").read_text())
    passed = all(r["matches_baseline"] and r["matches_original_manifest"] for r in rows) and dimensions == [17, 16, 10]
    report = {"scope": "CAD export reconstruction and MuJoCo compilation, not walking or manufacturing validation",
              "passed": passed, "mujoco_version": mujoco.__version__, "dimensions_nq_nv_nu": dimensions,
              "assets": rows, "cad_export_report": export_report}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2)+"\n")
    print(f"{len(rows)} assets: {'PASS' if passed else 'FAIL'}; compiled dimensions {dimensions}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
