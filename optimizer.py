import numpy as np
from scipy.optimize import minimize
from simulation import sim

def optimize_velocity(DISC=3600):
    """
    Optimize the velocity profile to maximize the final battery capacity. THIS DOESNT WORK, IT'S JUST A TEMPLATE
    """
    initial_velocities = np.full(DISC, 15) # Initial guess for velocities
    bounds = [(10, 20)] # Bounds for velocity
    result = minimize(sim, initial_velocities, bounds=bounds, method='L-BFGS-B', options={'disp': True, 'maxiter': 100, 'ftol': 1000000})   
    return result.x, result.fun

