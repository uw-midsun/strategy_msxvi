from scipy.optimize import minimize
from simulation import sim

def optimize_velocity(initial_velocities, DISC, INTER, STAGE_SYMBOL, CURRENT_D):
    """
    Optimize the velocity profile to maximize the final battery capacity. THIS DOESNT WORK, IT'S JUST A TEMPLATE
    """
    bounds = [(10, 20)]
    args = (DISC, INTER, STAGE_SYMBOL, CURRENT_D)
    result = minimize(sim, initial_velocities, bounds=bounds, method='L-BFGS-B', args=args, options={'disp': True, 'maxiter': 100, 'ftol': 1e-6})   
    return result.x, result.fun # velocities, final battery capacity

