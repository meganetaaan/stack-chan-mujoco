#!/usr/bin/env python3
"""Compare actual regenerated MJCF masses and COM at one identical pose."""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--designs", type=Path, nargs="+", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    rows, common_qpos = [], None
    for folder in args.designs:
        xml = folder / "models/scene.xml"
        model = mujoco.MjModel.from_xml_path(str(xml.resolve()))
        if (model.nq, model.nv, model.nu) != (17, 16, 10):
            p.error("expected the ten-hinge floating-base design")
        if common_qpos is None:
            common_qpos = model.key("home").qpos.copy()
        data = mujoco.MjData(model)
        data.qpos[:] = common_qpos
        mujoco.mj_forward(model, data)
        mass = float(model.body_mass.sum())
        com = data.subtree_com[0].copy()
        soles = np.array([data.site(name+"_sole").xpos for name in ("left", "right")])
        mid = soles.mean(axis=0)
        base = int(model.body("base").id)
        relative = data.xmat[base].reshape(3, 3).T @ (com-data.xpos[base])
        components = json.loads((folder / "models/components.json").read_text())["parts"]
        battery = next(c for c in components if c["name"] == "battery_2S_reservation")
        rows.append({"design": folder.name, "model_sha256": hashlib.sha256(xml.read_bytes()).hexdigest(),
                     "total_mass_kg": mass, "whole_robot_com_in_base_m": relative.tolist(),
                     "com_world_at_common_pose_m": com.tolist(),
                     "gravity_pitch_moment_about_sole_midpoint_Nm": float(mass*9.81*(com[0]-mid[0])),
                     "battery_mass_kg": battery["mass_kg"], "battery_com_base_m": battery["com_m"],
                     "base_inertia_principal_kg_m2": model.body_inertia[base].tolist(),
                     "dimensions_nq_nv_nu": [model.nq, model.nv, model.nu]})
    report = {"scope": "Mass/COM comparison, not gait, motor rating, mount or electrical validation",
              "same_qpos_for_all_models": common_qpos.tolist(),
              "gravity_pitch_moment_note": "Whole-body gravity moment about the midpoint of both soles, not a per-joint torque demand",
              "mujoco_version": mujoco.__version__, "results": rows}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    for row in rows:
        print(row["design"], row["total_mass_kg"], row["whole_robot_com_in_base_m"])


if __name__ == "__main__":
    main()
