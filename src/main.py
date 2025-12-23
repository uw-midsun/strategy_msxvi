import numpy as np
from datetime import datetime
from src.simulation import sim
from src.optimize import optimize_velocity
from src.plot import show_plots, COL_BATTERY

TIMESTEP_SEC = 10
SIMULATION_DURATION_SEC = 8 * 60 * 6
OPTIMIZE = False

MIN_SPEED_MS = 10
MAX_SPEED_MS = 20
CONSTANT_SPEED_MS = 15

def create_velocity_profile(duration_sec, timestep_sec, initial_distance, start_timestamp):
    """Generate velocity profile based on optimization flag."""
    num_steps = duration_sec
    if OPTIMIZE:
        initial_velocities = np.full(num_steps, MIN_SPEED_MS)
        velocities, _ = optimize_velocity(initial_velocities, timestep_sec, initial_distance, start_timestamp)
    else:
        velocities = np.full(num_steps, CONSTANT_SPEED_MS)
    return velocities

def main():
    initial_distance = 1
    start_time = datetime(2024, 7, 1, 8, 0)
    start_timestamp = int(start_time.timestamp())

    velocities = create_velocity_profile(SIMULATION_DURATION_SEC, TIMESTEP_SEC, initial_distance, start_timestamp)
    results_joules, final_distance, final_timestamp = sim(velocities, TIMESTEP_SEC, initial_distance, start_timestamp)

    results_wh = results_joules / 3600
    time_hours = np.arange(len(results_wh)) * TIMESTEP_SEC / 3600

    final_time = datetime.fromtimestamp(final_timestamp)
    final_battery = results_wh[-1, COL_BATTERY]
    print(f"Distance: {final_distance:.0f} m | Time: {final_time} | Battery: {final_battery:.1f} Wh")

    show_plots(time_hours, results_wh, velocities)

if __name__ == "__main__":
    main()
