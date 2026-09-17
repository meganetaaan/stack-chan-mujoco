"""Read the actual R5-A model, rather than guessing joint/actuator indices."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from .config import resolve_path

JOINT_TYPES = ("hip_roll", "hip_pitch", "knee", "ankle_pitch", "ankle_roll")
JOINT_NAMES = tuple(f"{side}_{kind}" for side in ("left", "right") for kind in JOINT_TYPES)
SOLE_GEOMS = ("col_left_sole_TPU_0", "col_right_sole_TPU_0")
SOLE_SITES = ("left_sole", "right_sole")
OBS_FIELDS = (
    ("projected_gravity_body", 3),
    ("linear_velocity_episode_heading", 3),
    ("angular_velocity_body", 3),
    ("joint_position_offset", 10),
    ("joint_velocity", 10),
    ("previous_action", 10),
    ("filtered_target_offset", 10),
    ("command_vx_vy_wz", 3),
    ("base_height_error", 1),
    ("position_tracking_error", 2),
    ("heading_error_sin_cos", 2),
    ("sole_contacts", 2),
    ("gait_phase_sin_cos", 2),
)
OBS_DIM = sum(n for _, n in OBS_FIELDS)


def observation_schema() -> list[dict]:
    result, i = [], 0
    for name, n in OBS_FIELDS:
        result.append({"name": name, "start": i, "stop": i + n})
        i += n
    return result


@dataclass
class RobotSpec:
    xml_path: Path
    xml_text: str
    name: str
    home: np.ndarray
    limits: np.ndarray
    motor: dict[str, np.ndarray]
    physics_dt: float
    mass: float
    fingerprint: str

    @classmethod
    def load(cls, config: dict) -> "RobotSpec":
        path = resolve_path(config["model_xml"])
        text = path.read_text(encoding="utf-8")
        root = ET.fromstring(text)
        robot = json.loads(resolve_path(config["robot_spec"]).read_text(encoding="utf-8"))
        mapping = json.loads(resolve_path(config["joint_map"]).read_text(encoding="utf-8"))
        if "A_landscape_cube" not in root.get("model", "") or robot.get("revision") != "r5-A_landscape_cube":
            raise ValueError("This kit targets R5-A (landscape cube). A/B models must not be mixed.")
        if tuple(x["name"] for x in sorted(mapping, key=lambda x: x["index"])) != JOINT_NAMES:
            raise ValueError("joint_map.json does not describe the expected ten R5-A joints")
        joints = {j.get("name"): j for j in root.findall(".//worldbody//joint")}
        if set(joints) != set(JOINT_NAMES):
            raise ValueError("Expected exactly the ten named hinge joints")
        free = root.findall(".//worldbody//freejoint")
        if len(free) != 1 or free[0].get("name") != "floating_base":
            raise ValueError("Expected the original unassisted floating_base freejoint")
        if root.find("equality") is not None or root.find("tendon") is not None:
            raise ValueError("Unexpected constraints/tendons: review the model before training")
        if any(float(b.get("gravcomp", "0")) != 0 for b in root.findall(".//body")):
            raise ValueError("Gravity compensation is not allowed in this environment")
        motors = {a.get("name"): a for a in root.findall("actuator/*")}
        if len(motors) != 10:
            raise ValueError("Expected ten torque motors, not position servos")
        limits = np.array([np.fromstring(joints[n].get("range", ""), sep=" ") for n in JOINT_NAMES])
        if limits.shape != (10, 2) or np.any(limits[:, 0] >= limits[:, 1]):
            raise ValueError("Invalid joint limits")
        home_node = root.find("keyframe/key[@name='home']")
        if home_node is None:
            raise ValueError("Missing 'home' keyframe; zero joint angles are NOT a valid reset pose")
        home = np.fromstring(home_node.attrib["qpos"], sep=" ")
        if home.shape != (17,) or not np.isfinite(home).all():
            raise ValueError("Expected 17 finite home qpos values")
        if np.any(home[7:] <= limits[:, 0]) or np.any(home[7:] >= limits[:, 1]):
            raise ValueError("Home joints violate the model limits")
        specs = []
        for name in JOINT_NAMES:
            s = dict(robot["motor"])
            override = robot["motor_overrides"]
            if name.split("_", 1)[1] in override["joint_types"]:
                s.update(override)
            a = motors.get(name + "_motor")
            if a is None or a.tag != "motor" or a.get("joint") != name or a.get("gear") != "1":
                raise ValueError(f"{name}: expected a direct gear=1 torque motor")
            cap = s["simulation_torque_cap_Nm"]
            for attr in ("ctrlrange", "forcerange"):
                if not np.allclose(np.fromstring(a.get(attr, ""), sep=" "), [-cap, cap]):
                    raise ValueError(f"{name}: {attr} disagrees with robot.json")
            specs.append(s)
        fields = {
            "cap": "simulation_torque_cap_Nm", "stall": "stall_torque_Nm",
            "kp": "kp_Nm_rad", "kd": "kd_Nm_s_rad", "delay_s": "command_delay_s",
        }
        motor = {key: np.array([s[f] for s in specs], dtype=float) for key, f in fields.items()}
        motor["omega"] = np.array([s["no_load_speed_rpm"] * np.pi / 30 for s in specs])
        digest = hashlib.sha256()
        for payload in (path.read_bytes(), resolve_path(config["robot_spec"]).read_bytes(), resolve_path(config["joint_map"]).read_bytes()):
            digest.update(payload)
        compiler = root.find("compiler")
        meshdir = compiler.get("meshdir", ".") if compiler is not None else "."
        for mesh in root.findall("asset/mesh"):
            f = path.parent / meshdir / mesh.attrib["file"]
            if not f.is_file():
                raise FileNotFoundError(f"Missing mesh: {f}; copy the whole assets/r5a directory")
            digest.update(mesh.attrib["file"].encode())
            digest.update(f.read_bytes())
        for name in SOLE_GEOMS:
            if root.find(f".//geom[@name='{name}']") is None:
                raise ValueError(f"Missing sole collision geom: {name}")
        mass = sum(float(x.attrib["mass"]) for x in root.findall(".//inertial"))
        return cls(path, text, root.get("model", ""), home, limits, motor,
                   float(root.find("option").attrib["timestep"]), mass, digest.hexdigest())

    def runtime_xml(self, visuals: bool) -> str:
        """Only visual meshes are stripped in headless mode. Physics is not changed."""
        root = ET.fromstring(self.xml_text)
        compiler = root.find("compiler")
        if compiler is not None:
            compiler.set("meshdir", str((self.xml_path.parent / compiler.get("meshdir", ".")).resolve()))
        if not visuals:
            for body in root.findall(".//body"):
                for g in list(body.findall("geom")):
                    if g.get("name", "").startswith("vis_"):
                        if g.get("contype") != "0" or g.get("conaffinity") != "0" or g.get("mass") != "0":
                            raise ValueError("Refusing to remove a physical geometry as a visual")
                        body.remove(g)
            asset = root.find("asset")
            if asset is not None:
                for mesh in list(asset.findall("mesh")):
                    asset.remove(mesh)
        return ET.tostring(root, encoding="unicode")

    def interface(self, config: dict) -> dict:
        # Task, reward and reset noise may change; action/observation meanings may not.
        e = config["env"]
        control_keys = ("policy_hz", "action_scale_rad", "target_slew_rad_s",
                        "target_joint_margin_rad", "max_outward_hip_spread_rad", "obs_clip")
        return {
            "schema_version": 1,
            "model_fingerprint": self.fingerprint,
            "joint_order": list(JOINT_NAMES),
            "observation_fields": observation_schema(),
            "observation_scaling_version": 1,
            "home_joints": self.home[7:].tolist(),
            "control": {k: e[k] for k in control_keys},
            "normalization": "fixed physical scales; no VecNormalize state",
        }
