"""Generate a reviewable PTH inhibit interface; DC allocations are not qualification."""
import csv
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'schematics/power/pth_inhibit_candidate_v1'
OUT.mkdir(parents=True, exist_ok=True)
# Total resistor variation is an engineering allocation, not a selected-part guarantee.
tol = .01
corners = []
for vin, rup, rdown, leakage in itertools.product(
    (9., 12.6), (100e3*(1-tol), 100e3*(1+tol)),
    (1e6*(1-tol), 1e6*(1+tol)), (-5.1e-6, 5.1e-6)
):
    gate = (vin/rup-leakage)/(1/rup+1/rdown)
    corners.append(dict(vin_V=vin, rup_ohm=rup, rdown_ohm=rdown,
                        allocated_gate_sink_A=leakage, gate_V=gate))
# 5.1 uA is a sensitivity allocation: 5 uA BJT ICBO at 150 C + 0.1 uA MOS IGSS.
# ICBO (emitter open) is NOT an ICEO/ICER bound for this connected circuit.
report = {
    'decision': 'Candidate topology for PTH comparison only; not integrated or released',
    'user_requirements': ['Supply and protection suitable for Tab5 and 12 axes, including applicable faults'],
    'design_policy': ['Controlled converter startup', 'No automatic servo rearm after a fault'],
    'manufacturer_conditions': {
        'inhibit_pin': 11, 'external_pullup_on_inhibit_permitted': False,
        'inhibit_low_range_V': [-.2, .8], 'enable_condition': 'open circuit',
        'inhibit_sink_typ_A': 235e-6, 'inhibit_sink_max_A': None,
        'recommended_off_leakage_less_than_A': 100e-9,
        'onsemi_BSS138_IDSS_max_at30V_25C_A': 100e-9,
        'onsemi_BSS138_IDSS_max_at50V_125C_A': 5e-6,
        'BSS138P_substitution_accepted': False,
        'BSS138P_IDSS_max_at60V_25C_A': 1e-6,
    },
    'engineering_allocations': {
        'vin_V': [9,12.6], 'resistor_total_variation': tol,
        'gate_leakage_sensitivity_A': [-5.1e-6,5.1e-6],
        'release_VCE_comparison_V': .2, 'release_VBE_comparison_V': .9,
        'allow_high_comparison_V': 2.4,
        'allow_poweroff_leakage_allocation_A': 10e-6,
    },
    'dc_comparison': {
        'gate_min_V': min(c['gate_V'] for c in corners),
        'gate_max_V': max(c['gate_V'] for c in corners),
        'inhibit_voltage_at_typ_sink_and_6ohm_V': 235e-6*6,
        'release_collector_load_upper_comparison_A': 12.6/(100e3*.99),
        'release_base_current_comparison_A': (2.4-.9)/(4.7e3*1.01)-.9/(4.7e3*.99),
        'base_voltage_at_allocated_10uA_Ioff_V': 10e-6*4.7e3*1.01,
        'rejected_100k_base_pulldown_at_10uA_V': 10e-6*100e3,
        'gate_pullup_power_upper_comparison_W': 12.6**2/(100e3*.99),
        'corners': corners,
    },
    'truth_table_expected_after_settling': [
        {'allow':'low','Q_RELEASE':'off','Q_STOP':'on','module':'inhibited'},
        {'allow':'high','Q_RELEASE':'on','Q_STOP':'off','module':'enabled'},
        {'allow':'high_impedance','Q_RELEASE':'off via base pulldown',
         'Q_STOP':'on from module input','module':'inhibited'},
    ],
    'unproven': [
        'Off-state drain leakage recommendation is not strictly met across temperature by the selected candidate data',
        'Nonzero release VCE means STOP MOS VGS is not exactly zero; IDSS test alone is insufficient',
        'BJT ICBO is not a bound for connected base-emitter resistor leakage',
        'Low-current BJT saturation uses an engineering comparison, not the 10mA data-sheet test point',
        'Inhibit internal voltage and maximum sink current, startup race and supply-collapse timing',
        'PCB leakage, hot/cold resistor variation and exact resistor procurement parts',
        'ALLOW at intermediate supply voltage is not covered by Ioff at VCC=0',
        'Converter output discharge, regeneration and full-system fault behavior',
    ],
    'manufacturing_release': False,
    'sources': [
        {'url':'https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf','section':'Ioff at VCC=0; existing regulator_request_connection_v1 source'},
        {'url':'https://www.ti.com/lit/gpn/pth08t240w','revision':'SLTS264J','pages':[4,6,24]},
        {'url':'https://www.onsemi.com/download/data-sheet/pdf/bss138-d.pdf','revision':'7 April2024','pages':[1,2]},
        {'url':'https://assets.nexperia.com/documents/data-sheet/BC847X_SER.pdf','revision':'13 July2022','pages':[2,4]},
        {'url':'https://assets.nexperia.com/documents/data-sheet/BSS138P.pdf','revision':'1 November2010','pages':[6]},
    ],
}
# Values use actual interface ports; passive parts intentionally have no fabricated MPN.
parts=[]
connections=[]
for side in ('LEFT','RIGHT'):
    pre=side+'__'
    g=pre+'STOP_GATE'; b=pre+'RELEASE_BASE'
    elements=[
        ('Q_STOP','onsemi','BSS138','SOT23',None,{'1':g,'2':'PACK_RETURN','3':pre+'PTH_INHIBIT'}),
        ('Q_RELEASE','Nexperia','BC847B','SOT23',None,{'1':b,'2':'PACK_RETURN','3':g}),
        ('R_GATE_UP','','','0603',100e3,{'1':'MODULE_INPUT_PROTECTED','2':g}),
        ('R_GATE_DOWN','','','0603',1e6,{'1':g,'2':'PACK_RETURN'}),
        ('R_BASE','','','0603',4.7e3,{'1':'SYS__'+side+'_REGULATOR_ALLOW','2':b}),
        ('R_BASE_DOWN','','','0603',4.7e3,{'1':b,'2':'PACK_RETURN'}),
    ]
    for ref,maker,mpn,pkg,value,pins in elements:
        parts.append(dict(ref=pre+ref,manufacturer=maker,mpn=mpn,package=pkg,
                          value_ohm=value,status='candidate, not released'))
        connections.extend(dict(ref=pre+ref,pin=p,net=n) for p,n in pins.items())
    connections.append(dict(ref=pre+'PTH_MODULE',pin='11',net=pre+'PTH_INHIBIT'))
for name,rows in [('bom.csv',parts),('connections.csv',connections)]:
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
(OUT/'review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report['dc_comparison'].items() if k!='corners'},indent=2))
