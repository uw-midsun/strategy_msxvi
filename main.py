import numpy as np
import matplotlib.pyplot as plt
from simulation import sim
from overview import show_overview, get_stage_dist, get_stage_start_dist
from optimizer import optimize_velocity
from db import load_data_to_memory

# The code in this file, optimize, overview, and simulate is kind of a mess! Play around with it!
def main():
    STAGE_SYMBOL = "3H" # Play around with this!

    route_model_df, _ = load_data_to_memory()
    route_model_df = route_model_df.sort_values(by="distance")

    stage_dist = get_stage_dist(route_model_df, STAGE_SYMBOL)
    show_overview(STAGE_SYMBOL)

    # Speed bounds in m/s for the car
    MIN_SPEED = 10
    MAX_SPEED = 20
    AVG_SPEED = (MIN_SPEED + MAX_SPEED) / 2

    # Simulation parameters
    STEP = 3600  # Time intervals (seconds); 3600 seconds in an hour
    HOURS_SPENT_DRIVING = 8
    CURRENT_D = get_stage_start_dist(route_model_df, STAGE_SYMBOL) # Starting distance (m)

    # Simulation input
    velocities, _ = optimize_velocity(np.full(HOURS_SPENT_DRIVING, AVG_SPEED), STEP, CURRENT_D)
    print(velocities)

    # Run simulation
    final_capacity, sim_data, final_d = sim(velocities, STEP, CURRENT_D)
    plt.plot(sim_data[:, 4]) # 4th column: capacity graph (Wh), can get power profiles (W) too
    plt.show()
    plt.plot(velocities)
    plt.ylim(MIN_SPEED, MAX_SPEED)
    plt.xlabel('Time (hours)')
    plt.ylabel('Speed (m/s)')
    plt.show()
    
    print(final_capacity)
    print(f"{final_d / 1000} km driven of {stage_dist / 1000}") # TODO: something seems wrong with the distance travelled...

if __name__ == "__main__":
    main()

    