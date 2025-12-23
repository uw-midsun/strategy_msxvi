from scipy.optimize import minimize
from .simulation import sim, BAT_CAPACITY
import numpy as np

def optimize_velocity(initial_velocities, dt, d0, t0):
    """
    Returns velocity profile to maximize distance traveled in given time.
    Uses SLSQP with battery SOC constraint (min 20%).

    Args:
        initial_velocities: Initial velocity profile (m/s)
        dt: Time step (seconds)
        d0: Starting distance (meters)
        t0: Starting time (unix timestamp)
    """
    bounds = [(10, 20)] * len(initial_velocities)
    constraints = [{
        'type': 'ineq',
        'fun': battery_constraint,
        'args': (dt, d0, t0)
    }]

    print("Beginning minimization (SLSQP)...")
    result = minimize(
        sim_wrapper,
        initial_velocities,
        bounds=bounds,
        method='SLSQP',
        args=(dt, d0, t0),
        constraints=constraints,
        options={'disp': True, 'maxiter': 50, 'ftol': 1e-6}
    )
    print("Done minimization.")
    return result.x, result.fun

def battery_constraint(velocities, dt, d0, t0):
    """Battery SOC must stay >= 20%. Returns: min(SOC) - 0.20"""
    sim_data, _, _ = sim(velocities, dt, d0, t0)
    capacities = sim_data[:, 4] * dt
    socs = capacities / BAT_CAPACITY
    return np.min(socs) - 0.20

def sim_wrapper(x, dt, d0, t0):
    """Objective function: maximize distance (minimize negative distance)"""
    _, final_d, _ = sim(x, dt, d0, t0)
    return -final_d