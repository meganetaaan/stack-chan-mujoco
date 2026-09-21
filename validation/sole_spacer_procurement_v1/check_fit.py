"""Dimensional screening only: supplier table versus current nominal sole hole."""
import json
from pathlib import Path

out = Path(__file__).resolve().parent
hole_diameter = 6.4  # Current CAD, no manufacturing tolerance established.
# Accu supplier datasheet, retrieved 2026-09-21. Title contradicts OD table.
od_min, od_max = 7.0 - 0.36, 7.0
result = {
    'scope': 'Supplier table envelope against nominal CAD; not an assembly tolerance qualification',
    'supplier_part': 'HPW-M2-V2-A2-BL',
    'source': 'https://www.accu.co.uk/api/product-datasheet?id=407083',
    'review_date': '2026-09-21',
    'source_conflict': 'Title says 6 mm OD; dimensional table says 7 mm +0/-0.36 mm',
    'sole_hole_nominal_diameter_mm': hole_diameter,
    'supplier_od_interval_mm': [od_min, od_max],
    'diametral_clearance_interval_mm': [hole_diameter - od_max, hole_diameter - od_min],
    'radial_interference_interval_mm': [(od_min - hole_diameter)/2, (od_max - hole_diameter)/2],
    'supplier_id_interval_mm': [2.2, 2.34],
    'supplier_thickness_interval_mm': [0.7, 0.9],
    'decision': 'Not approved: source conflict and table envelope incompatible with current nominal hole',
    'all_table_sizes_fit_nominal_hole': od_max <= hole_diameter,
    'any_table_size_fits_nominal_hole': od_min <= hole_diameter,
}
(out / 'fit_report.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
