"""Test whether small-strain-calibrated incompressible neo-Hookean fits tensile points."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);a=p.parse_args();d=json.loads((a.source/'source_review.json').read_text());rows=[]
for orientation,v in d['orientations'].items():
 mu=v['young_MPa']/3
 for strain,stress in v['nominal_stress_at_strain_MPa'].items():
  stretch=1+float(strain);prediction=mu*(stretch-stretch**-2);rows.append({'orientation':orientation,'engineering_strain':float(strain),'reported_MPa':stress,'neo_hookean_prediction_MPa':prediction,'relative_error':prediction/stress-1})
r={'comparison':rows,'model_qualified':False,'insertion_geometry':{'head_diameter_mm':8,'hole_diameter_mm':6,'uniform_radial_stretch_hypothesis':.75,'incompressible_axial_stretch_under_uniform_biaxial_squeeze':1/.75**2,'note':'Hypothetical uniform squeeze only; actual folding/contact strain is unknown, no insertion force inferred.'},'conclusion':'Single-parameter model based on initial modulus cannot reproduce listed large-strain points; do not qualify snap insertion with this law.'};(a.source/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
