import numpy as np
from simulation import sim
from optimizer import optimize_velocity

def main():
    # Run simulation
    velocities = np.random.uniform(10, 20, 3600) # sample velocity profile
    final_capacity = sim(velocities)

    ## Run optimization (THIS DOESN"T WORK RN)
    # optimized_velocities, final_capacity = optimize_velocity()

if __name__ == "__main__":
    main()
    

    