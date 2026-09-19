#!/usr/bin/env python3
"""Record manufacturer STEP bounds; do not infer motor mass from assembly volume."""
import argparse,hashlib,json
from pathlib import Path
import cadquery as cq


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--step',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():p.error('new output required')
    digest=hashlib.sha256(a.step.read_bytes()).hexdigest()
    expected=json.loads(Path('design/x330_manufacturer_reference.json').read_text())['sources']['cad']['sha256']
    if digest!=expected:raise ValueError('STEP differs from reviewed manufacturer version')
    w=cq.importers.importStep(str(a.step))
    def bounds(shape):
        b=shape.BoundingBox();return {key:getattr(b,key) for key in ('xmin','xmax','ymin','ymax','zmin','zmax')}
    report={'scope':__doc__,'step_sha256':digest,'bounding_box_mm':bounds(w.val()),
            'solids':[{'index':i,'volume_mm3':s.Volume(),'bounding_box_mm':bounds(s)} for i,s in enumerate(w.solids().vals())],
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n');print('Recorded',len(report['solids']),'assembly solids.')


if __name__=='__main__':main()
