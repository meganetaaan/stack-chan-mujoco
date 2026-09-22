"""Check a proposed static current threshold against explicit worst-sign error sums."""
from pathlib import Path
import json
p=Path('validation/brake_current_sensor_budget_v1');a=json.loads((p/'plan.json').read_text())
o=a['input_offset_V']+a['offset_drift_V_per_K']*a['max_temperature_delta_K']+a['PSRR_V_per_V']*a['supply_deviation_from_5V_max_V']
glo=a['gain']*(1-a['gain_error_fraction']);ghi=a['gain']*(1+a['gain_error_fraction']);rlo=a['shunt_ohm']*(1-a['shunt_total_error_fraction_assumed']);rhi=a['shunt_ohm']*(1+a['shunt_total_error_fraction_assumed']);vlo=a['threshold_V']*(1-a['threshold_total_error_fraction_assumed']);vhi=a['threshold_V']*(1+a['threshold_total_error_fraction_assumed']);imin=(vlo/ghi-o)/rhi;imax=(vhi/glo+o)/rlo
checks={'trip_window':a['criteria']['trip_current_min_A']<=imin<=imax<=a['criteria']['trip_current_max_A'],'threshold_inside_gain_spec':.5<=vlo<=vhi<=a['supply_min_armed_V']-.5}
r={'input_referred_offset_sum_V':o,'trip_current_interval_A':[imin,imax],'threshold_interval_V':[vlo,vhi],'checks':checks,'shunt_loss_at_1A_W':a['shunt_ohm'],'shunt_drop_at_1A_V':a['shunt_ohm'],'sensor_or_protection_verified':False}
(p/'report.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
