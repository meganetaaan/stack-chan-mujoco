#!/usr/bin/env python3
"""CAD feet with an 8 mm shorter toe and a 4 mm narrower inner edge."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import itertools


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists(): parser.error('new output required')
    source = Path('outputs/design_r6_base_collisions').resolve()
    sys.path[:0] = [str(source/'cad'), str(source/'src')]
    import cadquery as cq
    from build import build
    from r4_geometry import Part, box, cyl, union, profile_y, mass_properties
    original = {part.name: part for part in build()}
    args.out.mkdir(parents=True)
    records, overlaps = {}, []
    for side, sign in [('left',1),('right',-1)]:
        cy = sign*6
        old = original[side+'_foot_yoke'].shape
        upper = old.cut(box((200,200,40),(0,0,-36)))
        foot = union(upper, box((86,48,3),(4,cy,-17.5),r=3))
        points=[(-39,-15.8),(47,-15.8),(47,0),(43,12),(38,22),(30,37),(-29,37),(-39,24)]
        inner=[(-37,-18),(45,-18),(45,-1),(41,10.7),(36.5,20.8),(28.5,35),(-27.5,35),(-37,23.2)]
        boot = profile_y(points,48,cy)
        boot = cq.Workplane(obj=boot).edges('|Y').fillet(1.2).val()
        boot = boot.cut(profile_y(inner,44,cy))
        boot = boot.cut(box((74,50,45),(7,0,48),r=4,edge='|Z'))
        boot = boot.cut(box((42,56,8),(1,0,38),r=2,edge='|Z'))
        boot = boot.cut(box((77,8,32),(5.5,-sign*18,14),r=3,edge='|Y'))
        for xx in [-34,36]:
            for sy in [-1,1]:
                y = cy + sy*20.5
                boot = boot.fuse(box((7,7,3.2),(xx,y,-14.2),r=1))
                boot = boot.cut(cyl(1.15,6,(xx,y,-17)))
                foot = foot.cut(cyl(1.15,4,(xx,y,-19.5)))
        for sy in [-1,1]:
            for xx in [-19,-10,-1]:
                boot = boot.cut(box((3,6,8),(xx,cy+sy*24,17),r=.7,edge='|Y'))
        parts = {'foot_yoke': foot.clean(), 'boot_shell': boot.clean(),
                 'sole_TPU': box((86,48,3),(4,cy,-20.5),r=3)}
        for (n1,s1),(n2,s2) in itertools.combinations(parts.items(),2):
            v = float(s1.intersect(s2).Volume())
            if v > .01: overlaps.append({'side':side,'parts':[n1,n2],'volume_mm3':v})
        for suffix, shape in parts.items():
            name = side+'_'+suffix
            if not shape.isValid() or len(shape.Solids()) != 1:
                raise ValueError(name+': invalid or disconnected solid')
            m,com,I = mass_properties(Part(name,side+'_ankle_roll',shape,'custom',(.25,.3,.35),None))
            records[name] = {'mass_kg':float(m),'com_link_m':com.tolist(),
                             'inertia_com_kg_m2':I.tolist()}
            cq.exporters.export(shape,str(args.out/(name+'.step')))
            cq.exporters.export(shape,str(args.out/(name+'.stl')),tolerance=.09,angularTolerance=.15)
    report = {'scope':__doc__,'properties':records,'same_foot_intersections':overlaps,
              'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in [Path(__file__),source/'cad/r4_geometry.py',source/'cad/build.py']},
              'not_verified':['full ankle swept CAD clearance','ground support stability','strength']}
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'parts':len(records),'same_foot_intersections':overlaps}))


if __name__ == '__main__': main()
