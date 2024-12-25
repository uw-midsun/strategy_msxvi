# MSXVI - FSGP & ASC Strategy
## About
This repository contains the work of the Midnight Sun Strategy team, including code for setting up and interacting with a database, a simulator, and optimization algorithms.

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

Race strategy boils down to a single question:

### **What speed should we drive at?**

We address this question by leveraging the route, weather, and solar irradiance data. 

## Simulator

Run *sim.py* to simulate the car.

sim.py consists of a solver which computes the instantaneous power draw and supply from multiple sources over the course of a stage:

- **Drag Resistance**: based on vehicle aerodynamics, wind and velocity.
- **Rolling Resistance**: determined by the surface conditions of the road, mass of the car, and velocity.
- **Gradient Resistance**: determined by slope of the road and velocity.
- **Solar Irradiance**: determined by solar irradiance, vehicle orientation, array efficiency, and velocity.

## Route Overview

Run 'overview.py' to get distance, elevation profile, and irradiance data for a given stage.

## Database

The database is comprised of two tables: the route model and a solar irradiance table. The database is intended to be stored locally and synced with a cloud version based on availability of internet. The cloud database is regularly updated with the latest route model and solar irradiance data. This design enables the local solver to run offline with high performance and reliability. 

![Architecture Diagram](docs/architecture.PNG)

**The cell below syncs the local database with the cloud database if there's wifi.**

Additionally, for increased performance, the local database is then stored in memory as a [pandas DataFrame](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html).
