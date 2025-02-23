import numpy as np
import matplotlib.pyplot as plt
from simulation import sim

def main():
    # Simulation parameters
    DISC = 3600*8  # Time intervals (seconds)
    STAGE_SYMBOL = "1B" # Stage
    CURRENT_D = 0e3 # Starting distance (m)

    # Simulation input
    velocities = np.random.uniform(10, 20, DISC) # Sample velocity profile (m/s)

    # Run simulation
    final_capacity, sim_data = sim(velocities, DISC, STAGE_SYMBOL, CURRENT_D)
    plt.plot(sim_data[:, 4]) # capacity graph (Wh), can power profiles (W) too
    print(final_capacity)

if __name__ == "__main__":
    main()

    