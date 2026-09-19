#!/usr/bin/env python3
"""Add convex pieces for actual hollow ankle gimbals to a copied MJCF model.

CAD/mass/joints are unchanged. Ring approximation over-covers by <0.1 mm.
B-rep subtraction verifies coverage before exporting. Parent filtering is disabled.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET


def triangulate(points):
    def cross(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    ids = list(range(len(points)))
    area = sum(points[i][0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*points[i][1] for i in ids)
    if area < 0:
        ids.reverse()
    triangles = []
    while len(ids) > 3:
        for i in range(len(ids)):
            a,b,c = [ids[j%len(ids)] for j in (i-1,i,i+1)]
            if cross(points[a],points[b],points[c]) <= 1e-10:
                continue
            if any(all(cross(points[u],points[v],points[k]) >= -1e-10
                       for u,v in ((a,b),(b,c),(c,a))) for k in ids if k not in (a,b,c)):
                continue
            triangles.append([points[a],points[b],points[c]])
            ids.pop(i)
            break
        else:
            raise ValueError('Cannot triangulate CAD outline')
    triangles.append([points[i] for i in ids])
    return triangles


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    design = args.design.resolve()
    if args.out.exists():
        p.error('output already exists')
    source = (design/'cad/r4_geometry.py').read_text()
    markers = ["profile_y(outline,2.0,yy)", "cyl(10.5,2.0,(0,yy-1.0,0),(0,1,0))",
               "ss=ss.cut(cyl(3.1,3,(0,yy-1.5,0),(0,1,0)))",
               "box((8,34.9,2.4),(-42,sgn*1.95,15.2))",
               "box((2.4,34.9,2.4),(-55,sgn*1.95,-18.8))"]
    if any(source.count(marker) != 1 for marker in markers):
        p.error('CAD implementation changed; review gimbal decomposition')
    assignments = [n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Assign)
                   and any(isinstance(t,ast.Name) and t.id == 'outline' for t in n.targets)]
    if len(assignments) != 1:
        p.error('ambiguous gimbal outline')
    outline = ast.literal_eval(assignments[0].value)
    triangles = triangulate(outline)
    import numpy as np
    import cadquery as cq
    sys.path[:0] = [str(design/'cad'),str(design/'src')]
    from build import build
    from tab5_biped.core import KIN
    from r4_geometry import profile_y, box, union
    parts = {v.name:v for v in build()}
    root = ET.parse(design/'models/scene.xml').getroot()
    asset = root.find('asset')
    records = []
    for side, sign in [('left',1),('right',-1)]:
        part = parts[side+'_ankle_gimbal']
        body = root.find(f".//body[@name='{part.link}']")
        prefix = 'col_'+part.name+'_'
        if any(g.get('name','').startswith(prefix) for g in body.findall('geom')):
            p.error('gimbal already has collision proxies')
        solids = []
        vertices = []
        for y in (sign*(-14.5),sign*18.4):
            polygons = list(triangles)
            for i in range(24):
                a,b = np.array([i,i+1])*2*np.pi/24
                outer = 10.5/np.cos(np.pi/24)
                polygons.append([(outer*np.cos(a),outer*np.sin(a)),
                                 (outer*np.cos(b),outer*np.sin(b)),
                                 (3.1*np.cos(b),3.1*np.sin(b)),
                                 (3.1*np.cos(a),3.1*np.sin(a))])
            for poly in polygons:
                solids.append(profile_y(poly,2.,y))
                vertices.append([[x,yy,z] for yy in (y-1,y+1) for x,z in poly])
        for size,center in [((8,34.9,2.4),(-42,sign*1.95,15.2)),
                            ((2.4,34.9,2.4),(-55,sign*1.95,-18.8))]:
            solids.append(box(size,center))
            vertices.append([[center[0]+sx*size[0]/2,center[1]+sy*size[1]/2,center[2]+sz*size[2]/2]
                             for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)])
        combined = union(*solids)
        missing = part.shape.cut(combined).Volume()
        extra = combined.cut(part.shape).Volume()
        if missing > .001 or not combined.isValid():
            raise ValueError(f'{part.name}: uncovered CAD volume {missing}')
        for i,verts in enumerate(vertices):
            name = prefix+str(i)
            ET.SubElement(asset,'mesh',name=name+'_mesh',vertex=' '.join(f'{v/1000:.12g}' for xyz in verts for v in xyz))
            ET.SubElement(body,'geom',name=name,type='mesh',mesh=name+'_mesh',**{'class':'collision'})
        records.append({'part':part.name,'convex_pieces':len(solids),'cad_volume_mm3':part.shape.Volume(),
                        'uncovered_volume_mm3':missing,'extra_volume_mm3':extra,
                        'ring_radial_overcoverage_bound_mm':10.5*(1/np.cos(np.pi/24)-1)})
        print(records[-1],flush=True)
    # Existing yoke proxies omit the end bearing collars. Retain central bores;
    # small fastener holes are conservatively filled in these contact pieces.
    bearing_records = []
    for side,sign in [('left',1),('right',-1)]:
        configurations = {
            side+'_thigh_yoke': [(y,z,2.4) for y in (-16.8,16.8) for z in (0,-KIN['thigh_mm'])],
            side+'_shin_yoke': [(y,z,2.) for y,z in (
                (sign*(-14.5),0),(sign*19.6,0),
                (sign*(KIN['shin_outset_y_mm']-18.5),-KIN['shin_mm']),
                (sign*(KIN['shin_outset_y_mm']+15.6),-KIN['shin_mm']))],
        }
        for name, collars in configurations.items():
            part = parts[name]
            body = root.find(f".//body[@name='{part.link}']")
            for ring,(y,z,thickness) in enumerate(collars):
                for i in range(24):
                    a,b = np.array([i,i+1])*2*np.pi/24
                    outer = 10.5/np.cos(np.pi/24)
                    poly = [(outer*np.cos(a),z+outer*np.sin(a)),
                            (outer*np.cos(b),z+outer*np.sin(b)),
                            (3.1*np.cos(b),z+3.1*np.sin(b)),
                            (3.1*np.cos(a),z+3.1*np.sin(a))]
                    verts = [[x,yy,zz] for yy in (y-thickness/2,y+thickness/2) for x,zz in poly]
                    mesh_name = f'col_{name}_ring_{ring}_{i}'
                    ET.SubElement(asset,'mesh',name=mesh_name+'_mesh',vertex=' '.join(f'{v/1000:.12g}' for xyz in verts for v in xyz))
                    ET.SubElement(body,'geom',name=mesh_name,type='mesh',mesh=mesh_name+'_mesh',**{'class':'collision'})
            bearing_records.append({'part':name,'collars':len(collars),'convex_pieces':24*len(collars),
                                    'small_fastener_holes_filled':True,'full_part_coverage_verified':False})
    root.find('option/flag').set('filterparent','disable')
    root.set('model',root.get('model')+'-gimbal-collision')
    shutil.copytree(design,args.out,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    ET.indent(root,space='  ')
    ET.ElementTree(root).write(args.out/'models/scene.xml',encoding='utf-8',xml_declaration=True)
    paths = [design/name for name in ('robot.json','models/scene.xml','cad/build.py','cad/r4_geometry.py')]+[Path(__file__)]
    report = {'scope':'Gimbal and yoke bearing collision augmentation; other regions remain approximate',
              'parent_filter':'disabled','CAD_and_inertials_unchanged':True,
              'URDF_not_updated':True,'gimbals':records,'bearing_collars':bearing_records,
              'source_sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths}}
    (args.out/'GIMBAL_COLLISION_PATCH.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__':
    main()
