"""Reduced primitive collision proxies for R4, SI units.

Motor packages and sole contact use their declared boxes. Thin cosmetic panels
are represented by separated boxes, NOT a single convex hull filling the boot.
Openings/vents, curved toes and small bearing details are simplified. Independent
CAD B-rep tests are authoritative for packaging; these proxies are not an exact
collision tessellation and do not establish physical walking success.
"""
from .core import KIN


def box(size, pos):
    return {'type': 'box', 'size': [v / 2000 for v in size], 'pos': [v / 1000 for v in pos]}


def proxies(part):
    n = part['name']
    sg = 1 if n.startswith('left_') else -1
    if n == 'body_shroud':
        return part['collisions']
    if n.endswith('_boot_shell'):
        cy = sg * KIN['foot_outset_y_mm']
        # Outer wall, inboard lower lip, toe and heel. Hollow ankle passage.
        return [
            box((70, 1.5, 23), (2, cy + sg * 25, .5)),
            box((58, 1.5, 12), (2, cy + sg * 25, 22)),
            box((70, 1.5, 9), (2, cy - sg * 25, -8)),
            box((1.4, 46, 10), (54, cy, -6)),
            box((1.4, 46, 29), (-38, cy, 5)),
        ]
    if n.endswith('_roll_to_pitch_carrier'):
        hp = KIN['hip_pitch_offset_mm']
        return [box((2.0, 29, 37), (8.5, 0, hp[2]+7.5))] + [
            box((25, 1.4, 34), (20, y, hp[2]+7)) for y in (-14.2, 14.2)] + [
            box((19, 29, 2), (20, 0, hp[2]+25.2))]
    if n.endswith('_shin_yoke'):
        dy = sg * KIN['shin_outset_y_mm']; L = KIN['shin_mm']
        pairs = [(sg*(-14.5), dy+sg*(-18.5)), (sg*19.6, dy+sg*15.6)]
        return [box((16, 1.6, 13), (0, a, -7)) for a, b in pairs] + [
            box((16, 1.6, L-21), (0, b, -(21+L)/2)) for a,b in pairs]
    # All remaining declared boxes stay in the component's own link frame.
    return part['collisions']
