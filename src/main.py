import numpy as np
import matplotlib.pyplot as plt
from .optimize import optimize_velocity
from .simulation import sim
from .overview import show_overview, get_stage_bounds
from db.load import load_data_to_memory

def main():
    route_model_df, irradiance_df = load_data_to_memory()
    route_model_df = route_model_df.sort_values(by="distance")

    # Overview of a stage
    STAGE_SYMBOL = "3H" # Play around with this!
    show_overview(STAGE_SYMBOL, route_model_df)

    # Simulation parameters
    MIN_SPEED = 10
    MAX_SPEED = 20
    STEP = 3600  # Time intervals (seconds); 3600 seconds in an hour
    HOURS_SPENT_DRIVING = 8
    CURRENT_D, _ = get_stage_bounds(route_model_df, STAGE_SYMBOL) # Starting distance (m)

    # Optimized Velocities (Feel free to make your own custom velocity profile!)
    velocities, _ = optimize_velocity(np.full(HOURS_SPENT_DRIVING, MIN_SPEED), STEP, CURRENT_D)
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

if __name__ == "__main__":
    main()

    