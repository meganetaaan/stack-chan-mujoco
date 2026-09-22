"""Bounded dimensional comparison: heat-set inserts instead of service-loose nuts.
Run with the engineering environment from the repository root.
"""
import hashlib
import json
from pathlib import Path
import cadquery as cq

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "validation/tab5_insert_candidate_v1"
OUT.mkdir(exist_ok=True)
plan = {
    "candidate": "CNC Kitchen TC-M3x5.7, four; retain NBK SLH-M3-10, four",
    "manufacturer_mm": {"length": 5.7, "outer_diameter": 4.6,
                        "hole_diameter": 4.0, "minimum_wall_from_hole": 1.6},
    "engineering_choices": {"insert_abs_y": [55, 60.7], "through_bore_mm": 4.0,
                            "ear_height_mm": 8, "ear_x_mm": [37, 50]},
    "criteria": ["Single valid carrier", "No new carrier overlap above 0.01 mm3",
                 "Nominal bore wall >= manufacturer minimum",
                 "Screw spans insert length; no screw bottoming in blind polymer"],
    "stop": "One candidate and nominal dimensional/interference comparison; no mesh study",
    "limits": ["Hole compensation requires a same-process coupon",
               "Knurls, thread runout, tolerances, heat distortion and pullout not modeled",
               "Installed polymer envelope is a subtraction approximation, not melt simulation"]
}
(OUT / "plan.json").write_text(json.dumps(plan, indent=2) + "\n")
files = []
def read(rel):
    path = ROOT / rel
    files.append(path)
    return cq.importers.importStep(str(path)).val()

carrier = read("validation/tab5_carrier_v1/carrier.step")
fixed = read("validation/tab5_carrier_hardware_v2/fixed_shell.step")
hardware = {}
insert_outer = []
for sign in [-1, 1]:
    for z in [88, 112]:
        def cyl(r, length, y):
            return cq.Solid.makeCylinder(r, length, cq.Vector(42, sign*y, z), cq.Vector(0, sign, 0))
        ear = cq.Workplane("XY").box(13, 6, 8).translate((43.5, sign*58, z)).val()
        bridge = cq.Workplane("XY").box(3.7, 2, 8).translate((48.15, sign*61.5, z)).val()
        carrier = carrier.fuse(ear).fuse(bridge).fuse(cyl(3.5, 1.2, 61))
        carrier = carrier.cut(cyl(2, 8, 54.5))
        outer = cyl(2.3, 5.7, 55)
        insert_outer.append(outer)
        hardware[f"{sign}_{z}_insert"] = outer.cut(cyl(1.5, 5.7, 55))
        hardware[f"{sign}_{z}_screw"] = read(f"validation/tab5_carrier_hardware_v2/{sign}_{z}_screw.step")
carrier = carrier.clean()
installed = carrier
for outer in insert_outer:
    installed = installed.cut(outer)
installed = installed.clean()
report_path = ROOT / "validation/serviceable_torso_v1/report.json"
files.append(report_path)
r = json.loads(report_path.read_text())
assembly = read("validation/serviceable_torso_v1/assembly.step")
solids = assembly.Solids()
assert len(solids) == len(r["parts"])
for row, solid in zip(r["parts"], solids):
    assert abs(solid.Volume() - row["volume_mm3"]) < 1e-5, row["name"]
others = {row["name"]: s for row, s in zip(r["parts"], solids)
          if row["name"] != "new_carrier" and not row["name"].endswith("_nut")}
hits = []
for name, shape in others.items():
    v = carrier.intersect(shape).Volume()
    if v > .01:
        hits.append({"part": name, "volume_mm3": v})
insert_hits = []
for name, shape in hardware.items():
    if not name.endswith("_insert"):
        continue
    for other, body in others.items():
        v = shape.intersect(body).Volume()
        if v > .01:
            insert_hits.append({"insert": name, "part": other, "volume_mm3": v})
result = {
    "carrier_valid": carrier.isValid(), "carrier_solids": len(carrier.Solids()),
    "installed_approximation_valid": installed.isValid(),
    "installed_approximation_solids": len(installed.Solids()),
    "new_carrier_overlaps": hits, "insert_external_overlaps": insert_hits,
    "bore_wall_z_mm": (8-4)/2, "outer_insert_wall_z_mm": (8-4.6)/2,
    "minimum_bore_wall_along_insert_mm": (8-4)/2,
    "minimum_wall_guideline_met_nominally": (8-4)/2 >= 1.6,
    "screw_tip_abs_y_mm": 54, "insert_inner_abs_y_mm": 55,
    "nominal_tip_protrusion_mm": 1, "nominal_insert_length_spanned_mm": 5.7,
    "width_mm": 132, "carrier_pre_install_volume_mm3": carrier.Volume(),
    "intended_insert_polymer_overlap_mm3": [carrier.intersect(s).Volume() for s in insert_outer],
    "retention_strength_qualified": False, "manufacturing_release": False,
    "source_sha256": {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest() for f in files}
}
for name, shape in {"carrier_print": carrier, "carrier_installed_approximation": installed,
                    "fixed_shell": fixed, **hardware}.items():
    cq.exporters.export(shape, str(OUT / (name + ".step")))
(OUT / "report.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
