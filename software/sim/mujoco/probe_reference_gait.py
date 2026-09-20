#!/usr/bin/env python3
"""Screen a COM/IK reference and run it through unassisted MuJoCo servos.

This diagnostic has optional ideal attitude feedback; it is not hardware acceptance.
Reference base motion is used ONLY for IK and is never imposed on the simulator.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import xml.etree.ElementTree as ET
import numpy as np
import mujoco
from stackchan_rl.actuation import PostSlewLowPassBank
from stackchan_rl.walk_events import WalkEventTracker
from stackchan_rl.config import DEFAULT
from plant_variation import validate_variation, vary_model, vary_motors


class MovingCOMReference:
    """Advance COM between foot midpoints while shifting load laterally.

    Kinematic reference only: quasistatic CoP feasibility does not include the
    acceleration needed to execute these minimum-jerk motions.
    """
    def __init__(self, planner, pose, smooth, sides, com_forward_offset_m=0.):
        self.initial_feet = planner.initial_feet.copy()
        self.q0, self.b0 = planner.q0.copy(), planner.b0.copy()
        self.seed = (self.q0, self.b0)
        self.g, self.steps = planner.g, planner.steps
        self.pose, self.smooth, self.sides = pose, smooth, sides
        self.com_forward_offset_m = com_forward_offset_m

    def sample(self, time_s):
        g = self.g
        period = g["shift_s"]+g["swing_s"]+g["settle_s"]
        t = time_s-g["initial_stand_s"]
        feet = self.initial_feet.copy()
        xy, support = feet.mean(axis=0)[:2], np.array([.5, .5])
        phase = "stand"
        if t >= 0:
            completed = min(int(t/period), self.steps)
            previous_y = xy[1]
            previous_support = support.copy()
            for n in range(completed):
                stance, swing = n % 2, 1-n % 2
                feet[swing,0] = feet[stance,0]+g["step_length_m"]
                previous_y = feet[stance,1]-(1 if stance == 0 else -1)*g["com_inset_mm"]/1000
                previous_support = np.eye(2)[stance]
            if completed < self.steps:
                stance, swing = completed % 2, 1-completed % 2
                u = t-completed*period
                from_x = float(feet[:,0].mean())
                target_x = feet[stance,0]+g["step_length_m"]
                to_x = (feet[stance,0]+target_x)/2
                blend = self.smooth(u/g["shift_s"])
                stance_y = feet[stance,1]-(1 if stance == 0 else -1)*g["com_inset_mm"]/1000
                xy = np.array([from_x+(to_x-from_x)*self.smooth(u/period),
                               previous_y+(stance_y-previous_y)*blend])
                support = (1-blend)*previous_support+blend*np.eye(2)[stance]
                phase = "weight_shift"
                if u >= g["shift_s"]:
                    fraction = np.clip((u-g["shift_s"])/g["swing_s"],0,1)
                    feet[swing,0] += (target_x-feet[swing,0])*self.smooth(fraction)
                    feet[swing,2] = g["step_height_m"]*16*fraction**2*(1-fraction)**2
                    phase = "swing_"+self.sides[swing] if fraction < 1 else "touchdown_settle"
            else:
                blend = self.smooth((t-self.steps*period)/g["shift_s"])
                xy = feet.mean(axis=0)[:2]
                xy[1] = previous_y+(xy[1]-previous_y)*blend
                support = (1-blend)*previous_support+blend*np.array([.5,.5])
                phase = "finish"
        xy[0] += self.com_forward_offset_m
        q, base, error = self.pose(feet, xy, self.seed, self.b0[2,3])
        self.seed = (q, base)
        return SimpleNamespace(q=q, base=base, support=support, phase=phase)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--speed", type=float, default=.1)
    parser.add_argument("--step-period", type=float, default=.4, help="Seconds per left OR right step")
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--reference-mode", choices=["legacy", "moving-com"], default="moving-com")
    parser.add_argument("--com-inset-mm", type=float, default=20.)
    parser.add_argument("--static-compensation", action="store_true",
                        help="Add estimated static torque/kp to position targets, still subject to slew, LPF and torque limits")
    parser.add_argument("--slew", type=float, default=2.)
    parser.add_argument("--height-offset-mm", type=float, default=0.)
    parser.add_argument("--com-forward-offset-mm", type=float, default=0.,
                        help="Fore-aft COM offset relative to foot-midpoint reference; moving-com only")
    parser.add_argument("--imu-angle-gain", type=float, default=0.,
                        help="Ideal body attitude feedback to stance ankle targets, rad/rad")
    parser.add_argument("--imu-rate-gain", type=float, default=0.,
                        help="Ideal local angular-rate feedback to stance ankles, seconds")
    parser.add_argument("--plant-variation", type=Path,
                        help="JSON perturbation of the physical plant only; reference remains nominal")
    args = parser.parse_args()
    variation = validate_variation(json.loads(args.plant_variation.read_text()) if args.plant_variation else {})
    if any(not np.isfinite(v) or v < 0 or v > 2 for v in (args.imu_angle_gain,args.imu_rate_gain)):
        parser.error("IMU gains must be finite and in 0..2")
    if not np.isfinite(args.com_forward_offset_mm) or abs(args.com_forward_offset_mm) > 15:
        parser.error("COM forward offset must be finite and within +/-15 mm")
    if args.com_forward_offset_mm and args.reference_mode != "moving-com":
        parser.error("COM forward offset requires moving-com reference")
    if not np.isfinite(args.speed) or args.speed < 0 or not np.isfinite(args.step_period) or args.step_period <= 0 or args.steps < 1:
        parser.error("finite nonnegative speed, positive period and step count required")
    if not np.isfinite(args.com_inset_mm) or not 0 <= args.com_inset_mm < 26:
        parser.error("COM inset must be within the 26 mm half sole width")
    if not np.isfinite(args.slew) or args.slew <= 0 or not np.isfinite(args.height_offset_mm) or not -10 <= args.height_offset_mm <= 0:
        parser.error("positive finite slew and a height offset in -10..0 mm required")
    if args.out.exists():
        parser.error("use a new output directory to preserve previous runs")
    design = args.design.resolve()
    sys.path.insert(0, str(design / "src"))
    from tab5_biped.core import PARAMS, JOINT_NAMES, motor_spec, fk_leg, smooth, SIDES
    from tab5_biped.planner import Planner, static_torques, pose
    args.out.mkdir(parents=True)
    PARAMS["gait"].update(step_length_m=args.speed*args.step_period,
        step_height_m=.004 if args.speed > 0 else 0., initial_stand_s=1.,
        shift_s=.35*args.step_period, swing_s=.55*args.step_period, settle_s=.1*args.step_period,
        com_inset_mm=args.com_inset_mm)
    dt = .02
    planner = Planner(steps=args.steps)
    if args.height_offset_mm:
        planner.q0, planner.b0, _ = pose(planner.initial_feet, planner.initial_feet.mean(axis=0)[:2],
            (planner.q0, planner.b0), planner.b0[2,3]+args.height_offset_mm/1000)
        planner.seed = (planner.q0, planner.b0)
    if args.reference_mode == "moving-com":
        planner = MovingCOMReference(planner, pose, smooth, SIDES, args.com_forward_offset_mm/1000)
    end = 1.+args.steps*args.step_period+.5
    times = np.arange(0, end+dt/2, dt)
    samples, planning_failure = [], None
    for t in times:
        try:
            state = planner.sample(float(t))
            tau, wrenches = static_torques(state.q, state.base, state.support)
            margins = []
            for i, side in enumerate(("left", "right")):
                if state.support[i] <= 1e-8:
                    continue
                sole = fk_leg(state.q[5*i:5*i+5], side, state.base)[1]
                cop = sole[:3, :3].T @ (np.array(wrenches[i]["cop_m"])-sole[:3, 3])
                margins.append(float(min(PARAMS["kinematics"]["foot_length_mm"]/2000-abs(cop[0]),
                                         PARAMS["kinematics"]["foot_width_mm"]/2000-abs(cop[1]))))
            samples.append({"time_s": float(t), "q": state.q.tolist(), "base": state.base.tolist(),
                "support": state.support.tolist(), "phase": state.phase,
                "quasistatic_torque_Nm": tau.tolist(), "cop_edge_margin_m": min(margins)})
        except ValueError as exc:
            planning_failure = {"time_s": float(t), "reason": str(exc)}
            break
    xml = design / "models/scene.xml"
    report = {"scope": "Reference feasibility and unassisted servo diagnostic with optional ideal attitude feedback",
        "hardware_tested": False, "goal_acceptance": False, "physics_executed": False,
        "plant_variation":variation,
        "plant_variation_input_sha256":hashlib.sha256(args.plant_variation.read_bytes()).hexdigest() if args.plant_variation else None,
        "plant_variation_code_sha256":hashlib.sha256((Path(__file__).parent/'plant_variation.py').read_bytes()).hexdigest(),
        "steps_requested":args.steps,
        "speed_request_m_s": args.speed, "step_period_s": args.step_period,
        "reference_mode": args.reference_mode,
        "height_offset_mm": args.height_offset_mm,
        "com_forward_offset_mm": args.com_forward_offset_mm,
        "attitude_feedback": {"angle_gain":args.imu_angle_gain,"rate_gain_s":args.imu_rate_gain,
                              "sensor_model":"ideal MuJoCo body orientation and local angular velocity",
                              "support_weights":"planned support fractions"},
        "gait": PARAMS["gait"], "planning_failure": planning_failure,
        "source_sha256": {name: hashlib.sha256((design/name).read_bytes()).hexdigest()
                           for name in ("robot.json", "models/scene.xml", "models/inertials.json", "src/tab5_biped/core.py", "src/tab5_biped/planner.py")},
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "actuation_sha256": hashlib.sha256((Path(__file__).parent/"stackchan_rl/actuation.py").read_bytes()).hexdigest(),
        "mujoco_version": mujoco.__version__,
        "event_criteria": {k: DEFAULT["env"][k] for k in ("minimum_airtime_s", "minimum_lift_m",
                           "landing_contact_confirm_s", "minimum_foot_advance_m", "event_cooldown_s")},
        "supporting_implementation_sha256": {name: hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest()
            for name in ("stackchan_rl/walk_events.py", "stackchan_rl/ordered_steps.py", "stackchan_rl/config.py")}}
    (args.out/"reference.json").write_text(json.dumps(samples, indent=2)+"\n")
    specs = [motor_spec(n) for n in JOINT_NAMES]
    caps = np.array([s["simulation_torque_cap_Nm"] for s in specs])
    if len(samples) >= 2:
        q = np.array([s["q"] for s in samples])
        tau = np.array([s["quasistatic_torque_Nm"] for s in samples])
        peak_speed = np.max(np.abs(np.diff(q, axis=0)/dt), axis=0)
        report["reference_metrics"] = {
            "sample_count": len(samples), "complete": planning_failure is None,
            "peak_quasistatic_torque_Nm": np.max(np.abs(tau), axis=0).tolist(),
            "peak_quasistatic_cap_fraction": np.max(np.abs(tau)/caps, axis=0).tolist(),
            "peak_reference_joint_speed_rad_s": peak_speed.tolist(),
            "peak_reference_speed_no_load_fraction": (peak_speed/np.array([s["no_load_speed_rpm"]*np.pi/30 for s in specs])).tolist(),
            "minimum_cop_edge_margin_m": min(s["cop_edge_margin_m"] for s in samples)}
    if planning_failure is None:
        # Strip only visual assets for a lighter headless run.
        root = ET.parse(xml).getroot()
        for body in root.findall(".//body"):
            for geom in list(body.findall("geom")):
                if geom.get("name", "").startswith("vis_"):
                    assert geom.get("contype") == "0" and geom.get("conaffinity") == "0" and geom.get("mass") == "0"
                    body.remove(geom)
        asset = root.find("asset")
        collision_meshes = {g.get("mesh") for g in root.findall(".//geom") if g.get("mesh")}
        for mesh in list(asset):
            if mesh.tag == "mesh" and mesh.get("name") not in collision_meshes:
                asset.remove(mesh)
        root.find("compiler").set("meshdir", str((xml.parent/"meshes").resolve()))
        model = mujoco.MjModel.from_xml_string(ET.tostring(root, encoding="unicode"))
        data = mujoco.MjData(model)
        if args.plant_variation:
            vary_model(model,data,variation)
        assert (model.nq, model.nv, model.nu) == (17, 16, 10)
        assert model.neq == 0 and not np.any(model.body_gravcomp)
        mujoco.mj_resetDataKeyframe(model, data, model.key("home").id)
        qadr = np.array([model.joint(n).qposadr[0] for n in JOINT_NAMES])
        vadr = np.array([model.joint(n).dofadr[0] for n in JOINT_NAMES])
        aids = np.array([model.actuator(n+"_motor").id for n in JOINT_NAMES])
        data.qpos[:3] = np.array(samples[0]["base"])[:3,3]
        data.qpos[2] += .0005
        data.qpos[qadr] = np.array(samples[0]["q"])+np.array(variation["initial_joint_offset_rad"])
        mujoco.mj_forward(model, data)
        limits = np.array([model.joint(n).range for n in JOINT_NAMES])
        motor = {k: np.array([s[f] for s in specs]) for k, f in
                 {"cap":"simulation_torque_cap_Nm", "stall":"stall_torque_Nm", "kp":"kp_Nm_rad",
                  "kd":"kd_Nm_s_rad", "delay_s":"command_delay_s"}.items()}
        motor["omega"] = np.array([s["no_load_speed_rpm"]*np.pi/30 for s in specs])
        if args.plant_variation:
            vary_motors(model,motor,aids,variation)
        bank = PostSlewLowPassBank(motor, model.opt.timestep, args.slew, .04)
        bank.reset(data.qpos[qadr])
        report["effective_plant"] = {"total_mass_kg":float(sum(model.body_mass)),
            "sliding_friction_min_max": [float(model.geom_friction[:,0].min()),float(model.geom_friction[:,0].max())],
            "torque_caps_Nm":motor["cap"].tolist(),"stall_torques_Nm":motor["stall"].tolist(),
            "no_load_speeds_rad_s":motor["omega"].tolist(),"requested_delay_s":motor["delay_s"].tolist(),
            "quantized_delay_s":bank.delay_ticks*model.opt.timestep}
        floor = model.geom("floor").id
        sole_ids = [model.geom("col_"+side+"_sole_TPU_0").id for side in ("left", "right")]
        soles = set(sole_ids)
        tracker = WalkEventTracker(float(model.opt.timestep), DEFAULT["env"])
        base_id = model.body("base").id
        start = data.xpos[base_id].copy()
        max_tau, sum_tau2, sat = np.zeros(10), np.zeros(10), np.zeros(10)
        tilt, max_tilt, count, failure, failure_pairs = 0., 0., 0, None, []
        contact_metrics = {"self_penetration_steps":0,"nonsole_floor_penetration_steps":0,
                           "peak_self_contact_force_N":0.,"peak_nonsole_floor_force_N":0.,
                           "max_self_penetration_mm":0.,"max_nonsole_floor_penetration_mm":0.,
                           "penetration_tolerance_m":1e-8}
        force = np.zeros(6)
        loads, heights = np.zeros(2), np.zeros(2)
        clipped_targets = np.zeros(10, dtype=int)
        target_count = 0
        warnings = np.array([w.number for w in data.warning])
        initial_robot_contacts = [(model.geom(c.geom1).name, model.geom(c.geom2).name)
                                  for c in data.contact if floor not in (c.geom1, c.geom2) and c.dist < -1e-6]
        if initial_robot_contacts:
            failure, failure_pairs = "initial_self_penetration", initial_robot_contacts
        with (args.out/"trajectory.csv").open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["time_s", "forward_m", "lateral_m", "height_m", "tilt_deg"] + JOINT_NAMES +
                            ["left_load_N", "right_load_N", "left_sole_height_m", "right_sole_height_m"])
            if failure is None:
                for index in range(len(samples)-1):
                    target = np.array(samples[index]["q"])
                    if args.static_compensation:
                        target += np.array(samples[index]["quasistatic_torque_Nm"])/motor["kp"]
                    if args.imu_angle_gain or args.imu_rate_gain:
                        rotation = data.xmat[base_id].reshape(3,3)
                        angles = np.array([np.arctan2(rotation[2,1],rotation[2,2]),
                                           np.arcsin(np.clip(-rotation[2,0],-1,1))])
                        velocity = np.zeros(6)
                        mujoco.mj_objectVelocity(model,data,mujoco.mjtObj.mjOBJ_BODY,base_id,velocity,1)
                        correction = args.imu_angle_gain*angles+args.imu_rate_gain*velocity[:2]
                        for leg, weight in enumerate(samples[index]["support"]):
                            target[5*leg+3] += weight*correction[1]
                            target[5*leg+4] += weight*correction[0]
                    limited = np.clip(target, limits[:,0]+.015, limits[:,1]-.015)
                    clipped_targets += np.abs(target-limited) > 1e-12
                    target_count += 1
                    target = limited
                    for _ in range(round(dt/model.opt.timestep)):
                        tau, saturated, _ = bank.step(data.qpos[qadr], data.qvel[vadr], target)
                        data.ctrl[aids] = tau
                        old_time = data.time
                        mujoco.mj_step(model, data)
                        count += 1
                        max_tau = np.maximum(max_tau, np.abs(tau)); sum_tau2 += tau**2; sat += saturated
                        now_warnings = np.array([w.number for w in data.warning])
                        if not np.isfinite(data.qpos).all() or not np.isfinite(data.qvel).all() or np.any(now_warnings > warnings) or data.time < old_time:
                            failure = "invalid_physics"
                            break
                        mujoco.mj_forward(model, data)
                        tilt = float(np.rad2deg(np.arccos(np.clip(data.xmat[base_id].reshape(3,3)[2,2],-1,1))))
                        max_tilt = max(max_tilt, tilt)
                        loads[:] = 0
                        self_penetrating = False
                        nonsole_penetrating = False
                        for k in range(data.ncon):
                            c = data.contact[k]
                            mujoco.mj_contactForce(model, data, k, force)
                            norm = np.linalg.norm(force[:3])
                            if floor in (c.geom1, c.geom2):
                                other = c.geom2 if c.geom1 == floor else c.geom1
                                if other in soles:
                                    loads[sole_ids.index(other)] += abs((c.frame.reshape(3,3).T @ force[:3])[2])
                                if other not in soles:
                                    nonsole_penetrating |= c.dist < -1e-8
                                    contact_metrics["peak_nonsole_floor_force_N"] = max(contact_metrics["peak_nonsole_floor_force_N"],float(norm))
                                    contact_metrics["max_nonsole_floor_penetration_mm"] = max(contact_metrics["max_nonsole_floor_penetration_mm"],float(-1000*c.dist))
                                    if norm > .4:
                                        failure = "non_sole_floor_contact"
                            else:
                                self_penetrating |= c.dist < -1e-8
                                contact_metrics["peak_self_contact_force_N"] = max(contact_metrics["peak_self_contact_force_N"],float(norm))
                                contact_metrics["max_self_penetration_mm"] = max(contact_metrics["max_self_penetration_mm"],float(-1000*c.dist))
                                if norm > .8:
                                    failure = "self_contact"
                                    failure_pairs.append([model.geom(c.geom1).name, model.geom(c.geom2).name])
                        contact_metrics["self_penetration_steps"] += int(self_penetrating)
                        contact_metrics["nonsole_floor_penetration_steps"] += int(nonsole_penetrating)
                        if tilt > 35:
                            failure = failure or "excessive_tilt"
                        if failure:
                            break
                        for i, gid in enumerate(sole_ids):
                            heights[i] = data.geom_xpos[gid,2]-np.abs(data.geom_xmat[gid].reshape(3,3)[2]) @ model.geom_size[gid]
                        tracker.update(loads > .35, heights, data.geom_xpos[sole_ids,:2],
                                       float(data.xpos[base_id,0]-start[0]), data.time >= 1. and args.speed > 0)
                    position = data.xpos[base_id]
                    writer.writerow([float(data.time), float(position[0]-start[0]), float(position[1]-start[1]), float(position[2]), tilt]+data.qpos[qadr].tolist()+loads.tolist()+heights.tolist())
                    if failure:
                        break
        report["physics_executed"] = count > 0
        report["simulation"] = {"duration_s": float(data.time), "failure": failure, "failure_pairs": failure_pairs,
            "contact_metrics":contact_metrics,
            "forward_m": float(data.xpos[base_id,0]-start[0]) if np.isfinite(data.xpos[base_id,0]) else None, "max_tilt_deg": max_tilt,
            "peak_torque_Nm": max_tau.tolist(), "rms_torque_Nm": np.sqrt(sum_tau2/max(count,1)).tolist(),
            "saturation_fraction": (sat/max(count,1)).tolist(), "external_root_forces_used": False,
            "step_events": tracker.summary(), "valid_landings": tracker.counts.tolist(),
            "landing_sequence": tracker.sequence,
            "control": {"target_slew_rad_s": args.slew, "target_lowpass_s": .04,
                        "static_torque_position_compensation": args.static_compensation},
            "position_target_clipped_fraction": (clipped_targets/max(1,target_count)).tolist(),
            "completed_reference_without_model_failure": failure is None}
    (args.out/"report.json").write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(json.dumps({k: report.get(k) for k in ("planning_failure", "reference_metrics", "simulation")}, indent=2))


if __name__ == "__main__":
    main()
