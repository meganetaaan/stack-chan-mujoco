"""Necessary two-hole spacing condition; rigid-body registration cannot change distance."""
import hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
source=ROOT/'validation/dual_pololu_drill_v1/report.json'
specpath=ROOT/'schematics/power/dual_pololu_mechanical.json'
raw=source.read_bytes();d=json.loads(raw);spec=json.loads(specpath.read_text())
x,y=d['mount_pitch_mm'];t=spec['drill_location_tolerance']
# Engineering interpretation: independent +/-0.1mm Cartesian drill location.
# Opposite diagonal holes move outward at opposite corners of the tolerance boxes.
nominal=math.hypot(x,y);wide=math.hypot(x+2*t,y+2*t)
increase=wide-nominal
hole=spec['mount_hole_diameter'];screw=2.0
available=hole-screw
out=ROOT/'validation/pololu_hole_tolerance_v1';out.mkdir(exist_ok=True)
plan={'question':'Can fixed nominal screw axes accommodate a permitted diagonal hole-spacing error even after rigid translation/rotation?',
 'necessary_condition':'spacing change <= hole diameter minus screw envelope diameter for equal circular holes',
 'stop':'One analytic counterexample using published position allowance; no tolerance relaxation or FE.',
 'assumptions':['independent Cartesian +/-0.1mm hole-position intervals; drawing interpretation needs confirmation','2.18mm nominal bore, no bore diameter tolerance supplied','2.0mm screw envelope, not a measured thread diameter','rigid board and fixed axes, no tilt/elastic fitting/independent screw float']}
(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
r={'source_sha256':{str(source.relative_to(ROOT)):hashlib.sha256(raw).hexdigest(),str(specpath.relative_to(ROOT)):hashlib.sha256(specpath.read_bytes()).hexdigest()},
 'nominal_diagonal_mm':nominal,'outward_tolerance_diagonal_mm':wide,'spacing_increase_mm':increase,
 'available_pair_radial_accommodation_mm':available,
 'necessary_condition_margin_mm':available-increase,
 'fixed_axes_screen_pass':available>=increase,
 'largest_screw_envelope_diameter_for_this_case_mm':hole-increase,
 'additional_independent_float_per_screw_at_least_mm':max(0,(increase-available)/2),
 'interpretation':'Nominal CAD non-overlap does not establish tolerance-robust assembly. This conditional counterexample does not prove actual hardware cannot be assembled.',
 'unresolved':['drawing location tolerance interpretation','minimum finished PCB bore and actual screw major diameter bounds','nut pocket and spacer clearances allowing independent screw movement','print positioning error, slot geometry, retention and bearing area'],
 'manufacturing_release':False}
(out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
