# MSXVI Strategy System

Race strategy optimization for Midnight Sun solar racing team competing in Formula Sun Grand Prix (FSGP) and American Solar Challenge (ASC).

**FSGP (Qualifier):** Maximize distance over fixed time period. Scoring based on total distance with elapsed time as tiebreaker.

**ASC (Main Event):**
1. Complete base route without trailering
2. Maximize official miles (1st tiebreaker)
3. Minimize elapsed time (2nd tiebreaker)

Successfully achieving these objectives hinges on two factors:
- Designing an efficient solar car (less power out)
- Following an optimal race strategy

Optimal race strategy boils down to a single question:

*What speed should we drive at to maximize distance within race constraints?*

We address this question by leveraging the route, weather, and solar irradiance data.

## Architecture

![Architecture Diagram](docs/architecture.PNG)

### Database (`db/`)
**PostgreSQL** database with dual-deployment support:
- **Local instance:** Offline operation during race
- **Cloud instance:** Remote data storage and team access
- **Synchronization:** Bidirectional sync via `db/sync.py`

**Tables:**
- `route_model`: Waypoints, elevation, gradients, and road characteristics from GPX files
- `irradiance_archive` / `irradiance`: Historical/live solar irradiance (GHI), latitude/longitude coordinates, timestamps, etc.

**Key Files:**
- `db/connect.py` - Database connection and initialization
- `db/load.py` - Query execution and data loading to memory
- `db/sync.py` - Cloud-to-local synchronization
- `db/setup/route_model/` - GPX parsing and route table generation
- `db/setup/irradiance/irradiance.py` - Live solar irradiance data processing from Solcast (not tested)
- `db/setup/irradiance/irradiance_archive.py` - Historical solar irradiance data processing

### Simulator (`src/simulation.py`)
Physics-based energy model computing instantaneous power flows:

**Power Consumption:**
- Rolling resistance: `P_rr = (M·g·C_r1 + 4·C_r2·v)·v`
- Aerodynamic drag: `P_drag = 0.5·ρ·C_d·A·v³`
- Gradient resistance: `P_grad = M·g·sin(θ)·v`

**Power Generation:**
- Solar array: `P_solar = A_solar·GHI·η_solar`

**Vehicle Parameters:**
- Mass: 300 kg
- Drag coefficient: 0.13
- Frontal area: 1.357 m²
- Solar array: 4.0 m² @ 16% efficiency
- Battery capacity: 5.23 kWh (40s, 3.63V, 36Ah cells)

Integrates power flows over time to track battery State of Charge (SOC) for any velocity profile.

### Optimization (`src/optimize.py`)
**SLSQP (Sequential Least Squares Programming)** to find optimal velocity profile.

**Note:** SLSQP finds the gradients numerically (requires tuning).

**Objective:** Maximize distance traveled within race constraints.

**Constraints:**
- Velocity bounds: 10-20 m/s
- Battery SOC ≥ 20% at all timesteps

**Algorithm:** Iteratively adjusts velocity profile until convergence on maximum-distance solution.

### Visualization (`src/overview.py`)
- **Elevation profiles:** Distance vs. elevation for individual stages or full route
- **Irradiance profiles:** GHI over time for specific locations

## Installation

```bash
# Clone repository
git clone <repository-url>
cd strategy_msxvi

# Install dependencies
uv sync

# Configure environment variables
cp .env.example .env
# Edit .env with:
#   - Local PostgreSQL database credentials
#   - Cloud database credentials (optional)
#   - Solcast API key (optional, needed for live irradiance data)
```

## Usage

### Run Simulation (with or without Optimization)
Edit `src/main.py` to configure:
- `OPTIMIZE`: Enable/disable optimization (default: False)
- `SIMULATION_DURATION_SEC`: Race duration
- `TIMESTEP_SEC`: Simulation timestep
- `MIN_SPEED_MS`, `MAX_SPEED_MS`: Velocity bounds

```bash
uv run -m src.main
```

### Generate Route Overview
```python
from src.overview import plot_elevation, plot_irradiance
from datetime import datetime

# Plot elevation profile for stage 3H
plot_elevation("3H")

# Plot irradiance for specific location and time
plot_irradiance(
    d=10000,  # Distance along route (meters)
    t_start=int(datetime(2024, 7, 1, 8, 0).timestamp()),
    t_end=int(datetime(2024, 7, 1, 20, 0).timestamp())
)
```

### Database Setup

**Option 1: Import Database Dump (Recommended)**

If a database dump is available, this is the fastest way to get started:

```bash
# Import the database dump (creates database if needed)
python -m db.import data/database_dump.sql

# Or manually with psql
psql -U postgres -d strategy_msxvi -f data/database_dump.sql
```

**Option 2: Build Database from Scratch**

Build the database from GPX files and irradiance data:

```bash
# 1. Create route_model table from GPX files
python -m db.setup.route_model.route_model

# 2a. Create irradiance_archive table with historical data (requires SOLCAST_API_KEY)
python -m db.setup.irradiance.irradiance_archive

# 2b. Or create irradiance table with live/forecast data
# MODE 1: Live forecast (requires API key)
# MODE 2: Historical API (requires API key)
# MODE 3: Synthetic data (no API key needed)
python -m db.setup.irradiance.irradiance

# 3. Sync cloud database to local (optional, not tested)
python db/sync.py
```

**Export Database (for maintainers):**

```bash
# Export local database to share with others
python -m db.export

# Or export cloud database
python -m db.export --cloud

# Manually with pg_dump
pg_dump -U postgres -d strategy_msxvi -f data/database_dump.sql
```

**Note:** Database dumps are excluded from git due to size. Share the dump file via Google Drive, Dropbox, or team file server.

## Data

**Route Files:** ASC 2024 GPX files in `data/asc_24/`
- Full base route and individual stage files
- Format: `<stage>_<StartCity>To<EndCity>.gpx` and `<stage>L_<City>Loop.gpx`

**Irradiance Data:** Historical GHI data from Solcast in `data/asc_24/historical_irradiance.csv`

## Project Structure

```
strategy_msxvi/
├── src/
│   ├── main.py           # Main simulation runner
│   ├── simulation.py     # Physics-based energy model
│   ├── optimize.py       # SLSQP velocity optimization
│   ├── overview.py       # Route and irradiance visualization
│   ├── plot.py           # Energy flow plotting utilities
│   └── utils.py          # Data loading and mapping functions
├── db/
│   ├── connect.py        # PostgreSQL connection management
│   ├── load.py           # Database query and data loading
│   ├── sync.py           # Cloud-local database synchronization
│   ├── export.py         # Export database to SQL dump
│   ├── import.py         # Import database from SQL dump
│   └── setup/
│       ├── route_model/  # GPX parsing scripts
│       └── irradiance/   # Solar irradiance processing scripts
├── data/
│   └── asc_24/           # Route GPX files and irradiance data
└── docs/
    └── architecture.PNG  # System architecture diagram
```

## Dependencies

- **Core:** Python 3.12+, NumPy, SciPy, Pandas
- **Database:** psycopg2-binary, python-dotenv
- **Visualization:** Matplotlib
- **Route parsing:** gpxpy
- **Progress:** tqdm

## Technical Notes

- **Database:** PostgreSQL with environment-based configuration (local/cloud)
- **Optimization:** SciPy SLSQP with nonlinear constraints
- **Data caching:** Lazy loading of route and irradiance data to memory (pandas)
- **Coordinate mapping:** Distance-based route lookups, spatial discretization for irradiance

## Future Development

- Model Predictive Control (MPC) implementation for real-time receding horizon optimization
- Telemetry integration for actual vs. predicted comparison
- Multi-day race strategy planning

---

*Midnight Sun Solar Racing Team - University of Waterloo*

Email: k22agarw@uwaterloo.ca if you have questions.
