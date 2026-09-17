"""Small, independently testable frame/metric helpers (MuJoCo uses wxyz)."""
from __future__ import annotations
import numpy as np


def euler_quat(roll: float, pitch: float, yaw: float) -> np.ndarray:
    cr, sr = np.cos(roll / 2), np.sin(roll / 2)
    cp, sp = np.cos(pitch / 2), np.sin(pitch / 2)
    cy, sy = np.cos(yaw / 2), np.sin(yaw / 2)
    return np.array([cr*cp*cy + sr*sp*sy, sr*cp*cy - cr*sp*sy,
                     cr*sp*cy + sr*cp*sy, cr*cp*sy - sr*sp*cy])


def quat_mul(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    w, x, y, z = a
    v, i, j, k = b
    q = np.array([w*v-x*i-y*j-z*k, w*i+x*v+y*k-z*j,
                  w*j-x*k+y*v+z*i, w*k+x*j-y*i+z*v])
    return q / np.linalg.norm(q)


def quat_matrix(q: np.ndarray) -> np.ndarray:
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def yaw_matrix(angle: float) -> np.ndarray:
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def wrap_angle(angle: float) -> float:
    return float(np.arctan2(np.sin(angle), np.cos(angle)))


def command_at(t: float, requested: float, start: float, ramp: float) -> np.ndarray:
    # Smoothstep prevents an instantaneous requested-speed discontinuity.
    a = float(np.clip((t - start) / ramp, 0.0, 1.0))
    return np.array([requested * a * a * (3.0 - 2.0 * a), 0.0, 0.0])


def swing_mask(phase: float) -> np.ndarray:
    """Each leg swings for 35% of one left+right cycle; there is double support."""
    phase %= 1.0
    return np.array([0.075 < phase < 0.425, 0.575 < phase < 0.925])
