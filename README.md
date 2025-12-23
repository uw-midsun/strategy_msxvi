# MSXVI - FSGP & ASC Strategy
## About
This repository contains the work of the Midnight Sun Strategy team, including code for setting up and interacting with a database, a simulator, and MPC.

## FSGP & ASC
FSGP serves as a qualifying event for ASC. 

    Scoring is based on the highest overall official distance driven or laps completed over the duration of the event with ties being broken by the lowest overall official elapsed time or fastest lap" in other words maximising distance for a fixed time. 

If qualified, the objectives of ASC are the following:

    1. To complete the American Solar Challenge base route without trailering.
    2. To complete as many official miles as possible. (1st Tiebreaker)
    3. To complete the distance in the shortest elapsed time. (2nd Tiebreaker)

Successfully achieving these objectives hinges on two factors: 
- designing an efficient solar car (less power out)
- following an optimal race strategy

Optimal race strategy boils down to a single question:

### **What speed should we drive at to maximize distance within race constraints?**

We address this question by leveraging the route, weather, and solar irradiance data. 

## Route Overview

Run *overview.py* to get distance, elevation profile, and irradiance data for a given stage.

## Database

The database is comprised of two tables: the route model and a solar irradiance table.*routemodel.py* parses the route files (.gpx) to generate a table. *irradiance.py* parses live online data (solcast.com), historical data (from solcast.com), or symthetic data to generate a table. 

The database can run offline locally (*loader.py*) and can be synced (*sync.py*) with a cloud instance based on the availability of wifi. 

![Architecture Diagram](docs/architecture.PNG)

## Simulator

energy = f(location, time, velocity)

*simulation.py* consists of a solver which computes the instantaneous power draw and supply from multiple sources over the course of a stage:

- **Drag Resistance**: based on vehicle aerodynamics, wind and velocity.
- **Rolling Resistance**: determined by the surface conditions of the road, mass of the car, and velocity.
- **Gradient Resistance**: determined by slope of the road and velocity.
- **Solar Irradiance**: determined by solar irradiance, vehicle orientation, array efficiency, and velocity.

## Optimization

*optimize.py* uses Sequential Least Squares Programming (SLSQP) to find the optimal velocity profile that maximizes distance traveled over a given time period.

**Constraints:**
- Velocity bounds: 10-20 m/s at each time step
- Battery State of Charge (SOC) must remain >= 20% throughout the journey

The optimizer takes an initial velocity profile and iteratively adjusts it until converging on the solution that maximizes distance while satisfying all constraints. This forms the core optimization step used in the MPC loop.

## MPC (To-do)

State: energy, location, time
Control: velocity

Receding Horizon Loop:
1. At time k, optimize v[k, k+1, ..., k+n] using SLSQP
   - Objective: maximize distance (minimize -distance)
   - Constraints: energy >= 20% SOC, 10 <= v <= 30 m/s
2. Execute only first control: v[k]
3. Update state: (location, time, energy) using actual measurements
4. Repeat at k+1 with new forecast/data

## Todo
- refactor
- mpc
- documentation

