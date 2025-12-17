from scipy.optimize import minimize, OptimizeResult
from simulation import sim

def optimize_velocity(initial_velocities, STEP, CURRENT_D):
    """
    Returns velocity profile to maximize the final battery capacity.
    """
    bounds = [(10, 20)] # m/s
    args = (STEP, CURRENT_D)
    print("Beginning minimization...")
    result = minimize(sim_wrapper, initial_velocities, bounds=bounds, method='Nelder-Mead', args=args, options={'disp': True, 'maxiter': 10000}) 
    print("Done minimization.")  
    return result.x, result.fun 

def callback(intermediate_result: OptimizeResult):
    print("Pass this function as a parameter to minimize! Any code run here will be run between every iteration of the minimization.")

def sim_wrapper(x, STEP, CURRENT_D):
    _, _, final_d = sim(x, STEP, CURRENT_D)
    return -final_d # maximize final distance travelled

# Other potential ideas to try:
#  - other modes of scipy.mimize, ex. BFGS?
#  - apparently genetic algorithms are quite good at this kind of task!
#  - potentially neural networks, but that might be breaking a nut with a sledgehammer