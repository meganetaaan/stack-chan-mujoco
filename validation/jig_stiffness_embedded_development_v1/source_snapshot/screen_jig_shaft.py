"""Necessary shaft-bending screen; excludes offset stem, jaws and handle compliance."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'force_N':1.,'young_MPa':180000.,'displacement_limit_mm':.1,
      'material_basis':'Core304 typical modulus 200 GPa at 20 C, reduced 10% as an engineering assumption, not a guaranteed minimum.',
      'source':'https://www.outokumpu.com/-/media/files/products/core/outokumpu-core-range-datasheet.pdf',
      'load_basis':'1 N transverse assembly-force design screen; actual insertion and withdrawal forces remain unverified',
      'cases':[{'name':'slender_upper','section_mm':2.,'length_mm':133.9},{'name':'slender_lower','section_mm':2.,'length_mm':131.9},{'name':'stiff6_candidate','section_mm':6.,'length_mm':127.9}],
      'limitations':['ideal fixed shaft end','no offset moment, torsion, joints or finger compliance','not total jig deflection']}
(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
rows=[]
for c in plan['cases']:
 I=c['section_mm']**4/12;L=c['length_mm'];E=plan['young_MPa'];F=plan['force_N']
 d=F*L**3/(3*E*I)
 rows.append(dict(c,second_moment_mm4=I,deflection_mm=d,bending_stress_MPa=F*L*c['section_mm']/2/I,
                  force_at_displacement_limit_N=plan['displacement_limit_mm']/d*F,passed=d<=plan['displacement_limit_mm']))
report={'scope':__doc__,'rows':rows,'jig_verified':False}
(a.out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
