from scipy.optimize import minimize, OptimizeResult
from .simulation import sim, BAT_CAPACITY
import numpy as np

def optimize_velocity(initial_velocities, STEP, CURRENT_D):
    """
    Returns velocity profile to maximize the final battery capacity.
    Uses SLSQP with battery SOC constraint.
    """
    bounds = [(10, 20)] * len(initial_velocities)  # m/s for each velocity
    args = (STEP, CURRENT_D)

    # Battery constraint: minimum SOC >= 20%
    constraints = [
        {
            'type': 'ineq',
            'fun': battery_constraint,
            'args': args
        }
    ]

    print("Beginning minimization (SLSQP)...")
    result = minimize(
        sim_wrapper,
        initial_velocities,
        bounds=bounds,
        method='SLSQP',
        args=args,
        constraints=constraints,
        options={'disp': True, 'maxiter': 500, 'ftol': 1e-6}
    )
    print("Done minimization.")
    return result.x, result.fun

def battery_constraint(velocities, STEP, CURRENT_D):
    """
    Constraint: battery SOC must stay >= 20% at all times
    Returns: min(SOC) - 0.20 (must be >= 0 for constraint satisfaction)
    """
    _, sim_data, _ = sim(velocities, STEP, CURRENT_D)
    capacities = sim_data[:, 4] * STEP  # Convert Wh back to J
    socs = capacities / BAT_CAPACITY
    return np.min(socs) - 0.20

def sim_wrapper(x, STEP, CURRENT_D):
    _, _, final_d = sim(x, STEP, CURRENT_D)
    return -final_d  # maximize final distance travelled

def callback(intermediate_result: OptimizeResult):
    print("Pass this function as a parameter to minimize! Any code run here will be run between every iteration of the minimization.")