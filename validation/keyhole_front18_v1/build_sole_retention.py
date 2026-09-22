"""Internal TPU mushroom retention concept, with unchanged external foot envelope."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--front-x-mm',type=float,default=24);a=p.parse_args();root=Path(__file__).resolve().parents[3];a.out.mkdir(parents=True,exist_ok=False)
plan={'scope':__doc__,'stem_radius_mm':2.8,'hole_radius_mm':3,'head_radius_mm':4,'head_z_mm':[-15.8,-14.3],'positions_relative_center_mm':[[-16,-16],[-16,16],[a.front_x_mm,-16],[a.front_x_mm,16]],'criteria':{'valid_single_solids':True,'unintended_overlap_max_mm3':.01},'limitations':['Concept only; large-strain TPU insertion, creep and pullout not verified.','Nominal 0.2 mm radial and axial gaps, no tolerance qualification.','Material grade and retention forces not selected.']};(a.out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];sources={}
def cyl(r,z0,z1,x,y):return cq.Solid.makeCylinder(r,z1-z0,cq.Vector(x,y,z0))
for side,cy in [('left',6),('right',-6)]:
 paths={n:root/f'validation/{folder}/{side}_{n}.step' for n,folder in [('sole_TPU','boot_low_head_candidate_v1/cad'),('boot_shell','boot_low_head_candidate_v1/cad'),('foot_yoke','native_horn_yoke_development_v1/v4')]};parts={n:cq.importers.importStep(str(f)).val() for n,f in paths.items()};sources.update({str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths.values()});sole=parts['sole_TPU'];yoke=parts['foot_yoke'];oldvol=sole.Volume();oldyv=yoke.Volume()
 for x,dy in plan['positions_relative_center_mm']:
  y=cy+dy;yoke=yoke.cut(cyl(3,-19.01,-15.99,x,y));sole=sole.fuse(cyl(2.8,-19.01,-15.79,x,y)).fuse(cyl(4,-15.8,-14.3,x,y))
 sole=sole.clean();yoke=yoke.clean();valid=all(s.isValid() and len(s.Solids())==1 for s in [sole,yoke]);overlap=sole.intersect(yoke).Volume();boot_overlap=sole.intersect(parts['boot_shell']).Volume();bb=sole.BoundingBox()
 for n,s in [('sole_TPU',sole),('foot_yoke',yoke)]:cq.exporters.export(s,str(a.out/f'{side}_{n}.step'))
 rows.append({'side':side,'valid_single_solids':valid,'sole_added_mm3':sole.Volume()-oldvol,'yoke_removed_mm3':oldyv-yoke.Volume(),'sole_yoke_overlap_mm3':overlap,'sole_boot_overlap_mm3':boot_overlap,'sole_bounds_mm':[bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax],'nominal_geometry_pass':valid and overlap<=.01 and boot_overlap<=.01})
r={'rows':rows,'source_sha256':sources,'retention_strength_verified':False,'assembly_verified':False};(a.out/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
