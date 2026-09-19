#!/usr/bin/env python3
"""Inventory missing mechanical collision proxies and parent filtering.

Presence does not prove conservative coverage of a CAD part.
"""
import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--design', required=True, type=Path)
    p.add_argument('--out', required=True, type=Path)
    args = p.parse_args()
    xml = args.design/'models/scene.xml'
    components = args.design/'models/components.json'
    root = ET.parse(xml).getroot()
    geoms = root.findall('.//body/geom')
    rows = []
    for part in json.loads(components.read_text())['parts']:
        if part['role'] == 'visual':
            continue
        proxies = [g.attrib for g in geoms if g.get('name','').startswith('col_'+part['name']+'_')]
        rows.append({'part':part['name'],'link':part['link'],'proxy_count':len(proxies),
                     'proxy_types':sorted(set(g['type'] for g in proxies))})
    flag = root.find('option/flag')
    parent_filter = flag.get('filterparent','enable') if flag is not None else 'enable'
    report = {'scope':'Presence inventory only; no shape-coverage or collision-safety proof',
              'xml_filterparent':parent_filter,
              'same_link_contacts_filtered_by_engine':True,
              'parts_without_collision_proxy':[row['part'] for row in rows if not row['proxy_count']],
              'parts':rows,'sha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (xml,components)}}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['parts_without_collision_proxy']))


if __name__ == '__main__':
    main()
