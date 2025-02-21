import numpy as np
import matplotlib.pyplot as plt
from simulation import sim

def main():
    # Simulation parameters
    DISC = 3600*8  # Time intervals (seconds)
    STAGE_SYMBOL = "1B" # Stage
    CURRENT_D = 0e3 # Starting distance (m)
    velocities = np.random.uniform(10, 20, DISC) # Sample velocity profile

    # Run simulation
    final_capacity, sim_data = sim(velocities, DISC, STAGE_SYMBOL, CURRENT_D)
    print(final_capacity)
    plt.plot(sim_data[:, 4])

    ## Run optimization (THIS DOESN"T WORK RN)
    # optimized_velocities, final_capacity = optimize_velocity(velocities, DISC, INTER, STAGE_SYMBOL, CURRENT_D)

if __name__ == "__main__":
    main()

    