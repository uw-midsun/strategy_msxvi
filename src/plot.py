import matplotlib.pyplot as plt

# Results array column indices
COL_SOLAR = 0
COL_ROLLING = 1
COL_DRAG = 2
COL_GRADIENT = 3
COL_BATTERY = 4

def plot_energy_component(ax, time_hours, energy_wh, title, color, xlabel=None):
    """Plot a single energy component with consistent styling."""
    ax.plot(time_hours, energy_wh, color=color, linewidth=1.5)
    ax.set_title(title)
    ax.set_ylabel('Energy (Wh)')
    if xlabel:
        ax.set_xlabel(xlabel)
    ax.grid(True, alpha=0.3)

def plot_combined_balance(ax, time_hours, results_wh):
    """Plot all energy components on a single axis."""
    components = [
        (COL_SOLAR, 'Solar Power', 'orange'),
        (COL_ROLLING, 'Rolling Resistance', 'blue'),
        (COL_DRAG, 'Drag Resistance', 'red'),
        (COL_GRADIENT, 'Gradient Resistance', 'green'),
    ]

    for col_idx, label, color in components:
        ax.plot(time_hours, results_wh[:, col_idx], label=label, color=color,
                linewidth=1.5, alpha=0.7)

    ax.set_title('Energy Balance (All Components)')
    ax.set_xlabel('Time (hours)')
    ax.set_ylabel('Energy (Wh)')
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)

def plot_velocity_profile(ax, time_hours, velocities):
    """Plot velocity profile over time."""
    ax.plot(time_hours, velocities, color='darkblue', linewidth=1.5)
    ax.set_title('Velocity Profile')
    ax.set_xlabel('Time (hours)')
    ax.set_ylabel('Velocity (m/s)')
    ax.grid(True, alpha=0.3)

def create_plots(time_hours, results_wh, velocities=None):
    """Generate all simulation plots."""
    fig, axs = plt.subplots(3, 3, figsize=(18, 10))
    fig.suptitle('Simulation Results', fontsize=16, fontweight='bold')

    plot_energy_component(axs[0, 0], time_hours, results_wh[:, COL_SOLAR],
                         'Solar Power Generation', 'orange')
    plot_energy_component(axs[0, 1], time_hours, results_wh[:, COL_ROLLING],
                         'Rolling Resistance', 'blue')
    plot_energy_component(axs[0, 2], time_hours, results_wh[:, COL_DRAG],
                         'Drag Resistance', 'red')
    plot_energy_component(axs[1, 0], time_hours, results_wh[:, COL_GRADIENT],
                         'Gradient Resistance', 'green')
    plot_energy_component(axs[1, 1], time_hours, results_wh[:, COL_BATTERY],
                         'Battery Capacity', 'purple')

    plot_combined_balance(axs[1, 2], time_hours, results_wh)

    if velocities is not None:
        plot_velocity_profile(axs[2, 0], time_hours, velocities)

    # Hide unused subplots
    axs[2, 1].axis('off')
    axs[2, 2].axis('off')

    plt.tight_layout()
    return fig

def show_plots(time_hours, results_wh, velocities=None, save_path=None):
    """Create and display simulation plots, optionally saving to file."""
    create_plots(time_hours, results_wh, velocities)
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.show()
