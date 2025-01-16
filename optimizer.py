from scipy.optimize import minimize
from simulation import sim

def optimize_velocity(initial_velocities, DISC, INTER, STAGE_SYMBOL, CURRENT_D):
    """
    Returns velocity profile to maximize the final battery capacity and battery capacity itself. THIS DOESNT WORK, IT'S JUST A TEMPLATE FOR SCIPY MINIMIZE.
    """
    bounds = [(10, 20)]
    args = (DISC, INTER, STAGE_SYMBOL, CURRENT_D)
    result, _ = minimize(sim, initial_velocities, bounds=bounds, method='L-BFGS-B', args=args, options={'disp': True, 'maxiter': 100, 'ftol': 1e-6})   
    return result.x, result.fun 

