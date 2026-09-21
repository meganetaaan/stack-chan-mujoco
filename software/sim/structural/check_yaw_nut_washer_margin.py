"""Check complete square-nut footprint containment under known washer limits."""
import argparse,hashlib,json,math
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
wp=Path('docs/prototype/mechanical/sole_spacer/specification.json');np=Path('docs/prototype/mechanical/sole_spacer/nut_candidate.json');sp=Path('docs/prototype/mechanical/sole_spacer/screw_candidate.json')
w=json.loads(wp.read_text());n=json.loads(np.read_text());s=json.loads(sp.read_text())
plan={'question':'Does the complete square-nut envelope stay over the flat washer face when the washer shifts within its bore?',
 'sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [wp,np,sp]},
 'criterion':'Full outer footprint containment requires radius margin >=0. This is geometric, not a strength or allowable-pressure criterion.',
 'assumptions':['Nut square envelope uses maximum across-flats 4 mm; actual corner and face chamfers unknown.','Nut coaxial with a nominal 2 mm screw; nut/thread radial play omitted.','Washer may shift to one side of its maximum bore clearance, along a nut corner direction.','Flat bearing edge uses specified maximum radial edge break.'],
 'stop':'One limiting-dimension calculation; no FE and no strength verdict.'}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
r=w['outer_diameter']['min']/2-w['edge_break_radial_max'];corner=n['across_flats_mm'][1]/math.sqrt(2);shift=(w['inner_diameter']['max']-2)/2
result={'flat_outer_radius_min_mm':r,'square_corner_radius_max_mm':corner,'washer_shift_at_nominal_shank_mm':shift,'centred_outer_margin_mm':r-corner,'shifted_outer_margin_mm':r-corner-shift,'complete_outer_envelope_supported':r>=corner+shift,
 'necessary_OD_min_for_this_case_mm':2*(corner+shift+w['edge_break_radial_max']),
 'not_proven':['Actual nut bearing footprint (chamfer dimensions absent)','Real bolt and thread tolerances','Allowable pressure and pull-through/creep','Required assembly preload and remaining preload'],
 'manufacturing_release':False}
(a.out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
