"""Angular inertial couple exerted by a rigid payload on its support.
Inputs use base-to-world quaternions (w,x,y,z) and COM inertia in base axes.
"""
import numpy as np
from scipy.spatial.transform import Rotation


def angular_motion(time, quaternion_wxyz):
    t = np.asarray(time)
    q = np.asarray(quaternion_wxyz)
    assert len(t) >= 7 and np.all(np.diff(t) > 0)
    assert np.isfinite(q).all() and np.allclose(np.linalg.norm(q, axis=1), 1, atol=1e-6)
    rotation = Rotation.from_quat(q[:, [1, 2, 3, 0]])
    # World-axis relative rotation, symmetric interval; endpoints excluded downstream.
    omega = np.empty((len(t), 3))
    omega[1:-1] = (rotation[2:] * rotation[:-2].inv()).as_rotvec() / (t[2:] - t[:-2])[:, None]
    omega[0] = (rotation[1] * rotation[0].inv()).as_rotvec() / (t[1] - t[0])
    omega[-1] = (rotation[-1] * rotation[-2].inv()).as_rotvec() / (t[-1] - t[-2])
    alpha = np.gradient(omega, t, axis=0, edge_order=2)
    return rotation.inv().apply(omega), rotation.inv().apply(alpha)


def couple_on_support(omega_body, alpha_body, inertia_com):
    inertia = np.asarray(inertia_com)
    return -(alpha_body @ inertia.T + np.cross(omega_body, omega_body @ inertia.T))


def verify_analytic_cases():
    t = np.linspace(0, 1, 1001)
    axis = np.array([1., 2., 3.]); axis /= np.linalg.norm(axis)
    inertia = np.diag([.001, .002, .004])
    errors = {}
    for name, angle, omega_exact, alpha_exact in [
        ('constant_rotation', 2*t, np.tile(2*axis,(len(t),1)), np.zeros((len(t),3))),
        ('accelerating_rotation', 1.5*t*t, 3*t[:,None]*axis, np.tile(3*axis,(len(t),1)))]:
        q = Rotation.from_rotvec(angle[:,None]*axis).as_quat()[:,[3,0,1,2]]
        w, a = angular_motion(t,q)
        got = couple_on_support(w,a,inertia)
        expected = couple_on_support(omega_exact,alpha_exact,inertia)
        errors[name] = float(np.max(np.abs(got[3:-3]-expected[3:-3])))
        assert errors[name] < 1e-9
    # Zero angular acceleration does not imply zero couple for anisotropic inertia.
    assert np.linalg.norm(couple_on_support(omega_exact[-1:],np.zeros((1,3)),inertia)) > .001
    principal = couple_on_support(np.array([[2.,0,0]]),np.array([[3.,0,0]]),inertia)
    assert np.allclose(principal, [[-.003,0,0]], atol=1e-14)
    gyro = couple_on_support(np.array([[1.,2.,3.]]),np.zeros((1,3)),inertia)
    assert np.allclose(gyro, [[-.012,.009,-.002]], atol=1e-14)
    errors['principal_axis_sign'] = float(np.max(np.abs(principal-[[ -.003,0,0]])))
    errors['explicit_gyroscopic_couple'] = float(np.max(np.abs(gyro-[[-.012,.009,-.002]])))
    return errors
