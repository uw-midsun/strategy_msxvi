import numpy as np
import pandas as pd

csv_read = pd.read_csv("ASC.2016.csv")

G_sc = 1353
tilt = float(input("Enter surface tilt angle: "))
azimuth = float(input("Enter surface azimuth angle: "))
lat = float(csv_read["latitude"].iloc[0])
lon = float(csv_read["longitude"].iloc[0])
day_no = int(input("Enter day number: "))

max_iterations = 24 * 60 * 60

# Solar altitude angle for each time step with solar declination angle, latitude, hour angle, and surface tilt angle
altitude_s = np.zeros(max_iterations)

# Solar azimuth angle for each time step
azimuth_s = np.zeros(max_iterations)
# Solar incidence angle: solar array direction relative to a surface's normal
inc = np.zeros(max_iterations)
# Time of day in hours, from sunrise to sunset, incremented by minutes
time = np.zeros(max_iterations)

# Global Horizontal Solar Irradiance, based on the solar zenith angle and the solar constant
G_oh = np.zeros(max_iterations)
# Set the day number directly
n = day_no
# Solar declination angle for a specific day n, represents position of the sun relative to the Earth's equatorial plane.
dec = 23.45 * np.sin(np.radians(360 * (n / 365)))

# Sunrise/sunset hour: angular distance of the sun from the local meridian at a given time, measured in degrees.
ang = (1 / 15) * np.degrees(
    np.arccos(-np.tan(np.radians(dec)) * np.tan(np.radians(lat)))
)
# Solar hour angle at solar noon, highest altitude in the sky, which is peak solar radiation
ss = 12 + ang
# Sunrise time, measured since midnight, based on the solar hour angle at sunrise
sr = 12 - ang

# Initialize index variable
m = 0

# Loop for each minute of the day
for t in np.arange(sr * 60, ss * 60 + 1, 1):
    # Convert minutes to hours
    t_hour = t / 60
    # Hour angle
    w = 15 * (t_hour - 12)

    altitude_s[m] = np.degrees(
        np.arcsin(
            np.sin(np.radians(dec)) * np.sin(np.radians(lat))
            + np.cos(np.radians(dec)) * np.cos(np.radians(lat)) * np.cos(np.radians(w))
        )
    )
    azimuth_s[m] = np.degrees(
        np.arcsin(
            np.cos(np.radians(dec))
            * np.sin(np.radians(w))
            / np.cos(np.radians(altitude_s[m]))
        )
    )
    # Difference between the calculated solar azimuth angle and the user-provided surface azimuth angle
    azimuth_sy = abs(azimuth_s[m] - azimuth)
    # Solar incidence angle at the m-th minute of the day.
    inc[m] = np.degrees(
        np.arccos(
            np.sin(np.radians(dec)) * np.sin(np.radians(lat)) * np.cos(np.radians(tilt))
            - np.sin(np.radians(dec))
            * np.cos(np.radians(lat))
            * np.sin(np.radians(tilt))
            * np.cos(np.radians(azimuth))
            + np.cos(np.radians(dec))
            * np.cos(np.radians(lat))
            * np.cos(np.radians(tilt))
            * np.cos(np.radians(w))
            + np.cos(np.radians(dec))
            * np.sin(np.radians(lat))
            * np.sin(np.radians(tilt))
            * np.cos(np.radians(azimuth))
            * np.cos(np.radians(w))
            + np.cos(np.radians(dec))
            * np.sin(np.radians(tilt))
            * np.sin(np.radians(azimuth))
            * np.sin(np.radians(w))
        )
    )
    # Zenith angle: between the vertical direction and a given direction relative to the position of the sun
    zenith = 90 - altitude_s[m]
    G_oh[m] = (
        G_sc
        * (1 + 0.033 * np.cos(np.radians(360 * (n + 81) / 365)))
        * np.cos(np.radians(zenith))
    )
    # Horizontal Solar Radiation: total solar radiation received on a horizontal surface
    H_oh = (
        (24 * 3600 / np.pi)
        * G_sc
        * (1 + 0.033 * np.cos(np.radians(360 * (n + 81) / 365)))
        * (
            np.cos(np.radians(dec)) * np.cos(np.radians(lat)) * np.sin(np.radians(ang))
            + (2 * np.pi * ang / 365)
            * np.sin(np.radians(dec))
            * np.sin(np.radians(lat))
        )
    )
    time[m] = t_hour
    m += 1

# Trim excess zeros from arrays
altitude_s = altitude_s[:m]
azimuth_s = azimuth_s[:m]
inc = inc[:m]
time = time[:m]
G_oh = G_oh[:m]

# Display results
df = pd.DataFrame(
    {
        "Time": time,
        "Irradiance (W/m2)": G_oh,
        "Solar Altitude Angle": altitude_s,
        "Solar Azimuth Angle": azimuth_s,
        "Solar Zenith Angle": 90 - altitude_s,
        "Incidence Angle": inc,
    }
)
print(df)

de = dec
day_le = 2 * ang
sunrise = sr
sunset = ss
max_ir = np.max(G_oh)
max_in = np.max(inc)
max_al = np.max(altitude_s)

Results = [de, day_le, sunrise, sunset, max_ir, max_in, max_al]
C1 = [
    "Declination Angle",
    "Day Length",
    "Sunrise",
    "Sunset",
    "Maximum Irradiance",
    "Maximum Incidence Angle",
    "Maximum Solar Altitude Angle",
]
C2 = pd.DataFrame({"Results": Results}, index=C1)
print(C2)
