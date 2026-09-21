#!/usr/bin/env python3
"""Check whether captive boot screws can traverse the nut without hitting its roof."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
def main():
    hardware = ROOT/'validation/captive_boot_hardware_development_v1/plan.json'
    cavity = ROOT/'validation/boot_low_head_candidate_v1/cad/plan.json'
    assumptions = ROOT/'validation/boot_low_head_candidate_v1/plan.json'
    h, c, a = [json.loads(p.read_text()) for p in (hardware, cavity, assumptions)]
    seat = h['screw_envelope_mm']['shaft_z'][0]
    nut_bottom, roof = c['nut_cavity_z_mm']
    thickness = h['nut_envelope_mm']['thickness']
    length = h['screw_envelope_mm']['shaft_z'][1] - seat
    rows = []
    # Retain the existing +/-0.2 mm independent printed boundary assumption.
    # Do not pretend it is a qualified process or a purchased screw tolerance.
    for error in (0, a['print_error_assumption_mm']):
        minimum_length = nut_bottom + thickness - seat + 2*error
        maximum_length = roof - seat - 2*error
        rows.append({'printed_boundary_error_mm': error,
                     'minimum_length_to_traverse_clamped_nut_mm': minimum_length,
                     'maximum_length_without_roof_contact_mm': maximum_length,
                     'length_window_mm': maximum_length-minimum_length,
                     'candidate_length_mm': length,
                     'candidate_nut_traversal_margin_mm': length-minimum_length,
                     'candidate_roof_clearance_mm': maximum_length-length,
                     'nonempty_length_window': maximum_length > minimum_length})
    report = {'question': __doc__, 'rows': rows,
              'basis': 'Nut clamped against cavity bottom; maximum modeled nut thickness 1.2 mm. Screw tip/threads simplified.',
              'criteria': 'Positive roof clearance and full axial traversal of nominal nut envelope; necessary screening only, not thread strength.',
              'screw_length_tolerance_mm': None,
              'decision': 'Current cavity has no robust length window under retained independent boundary assumption, even before screw tolerance.',
              'manufacturing_release': False,
              'next_design_constraint': 'Increase axial space above the clamped nut or justify tighter correlated process capability. Do not select a longer screw without roof check.',
              'limitations': ['Full formed thread engagement and chamfers not modeled.', 'Print errors are Codex assumptions, not measured capability.', 'Nut material, preload, stripping and roof printability not verified.'],
              'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in (hardware,cavity,assumptions)}}
    out=ROOT/'validation/boot_screw_axial_budget_v1';out.mkdir(exist_ok=True)
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(rows))
if __name__ == '__main__': main()
