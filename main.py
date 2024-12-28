import numpy as np
from simulation import sim
from optimizer import optimize_velocity

def main():

    # Simulation parameters
    DISC = 3600  # Discretization (number of time steps)
    INTER = 8  # Time interval(s)
    STAGE_SYMBOL = "1B"
    CURRENT_D = 0e3 # Starting distance (m)

    # Run simulation
    velocities = np.random.uniform(10, 20, 3600) # sample velocity profile
    final_capacity = sim(velocities, DISC, INTER, STAGE_SYMBOL, CURRENT_D)

    ## Run optimization (THIS DOESN"T WORK RN)
    # optimized_velocities, final_capacity = optimize_velocity(DISC, INTER, STAGE_SYMBOL, CURRENT_D)

if __name__ == "__main__":
    main()
    

    