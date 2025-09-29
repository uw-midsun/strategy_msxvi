#!/usr/bin/env python3
import os, csv, requests
from datetime import datetime, timezone, date, timedelta
from tqdm import tqdm
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from db import connect_to_db

load_dotenv()

API_KEY = os.getenv("SOLCAST_API_KEY")
LOCATIONS_CSV = os.getenv(
    "LOCATIONS_CSV",
    "/root/Desktop/strategy_msxvi/data/asc24latlong.csv"
)

PARAMS = [
    "air_temp", "albedo", "azimuth", "clearsky_dhi", "clearsky_dni",
    "clearsky_ghi", "cloud_opacity", "dhi", "dni", "ghi",
    "max_air_temp", "min_air_temp", "precipitable_water", "precipitation_rate",
    "relative_humidity", "weather_type", "wind_direction_10m", "wind_gust",
    "wind_speed_10m", "zenith"
]
COLS = ["latitude", "longitude", "timestamp"] + PARAMS

def _read_latlon(csv_path):
    with open(csv_path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        fm = {k.lower(): k for k in (r.fieldnames or [])}
        lat_key, lon_key = fm.get("latitude"), fm.get("longitude")
        if not lat_key or not lon_key:
            raise ValueError("CSV must have 'latitude' and 'longitude' headers.")
        return [(float(row[lat_key]), float(row[lon_key])) for row in r]

def _iso_to_epoch(iso_str):
    iso_str = iso_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(iso_str)
    if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()

def _solcast_url(lat, lon, start_iso, duration):
    return (
        "https://api.solcast.com.au/data/historic/radiation_and_weather"
        f"?latitude={lat}&longitude={lon}"
        f"&start={start_iso}&duration={duration}"
        "&format=json&time_zone=utc"
        f"&output_parameters={','.join(sorted(PARAMS))}"  # alphabetized
        f"&api_key={API_KEY}"
    )

def init_table():
    numeric = [p for p in PARAMS if p != "weather_type"]
    ddl = (
        "CREATE TABLE IF NOT EXISTS irradiance ("
        "latitude DOUBLE PRECISION, "
        "longitude DOUBLE PRECISION, "
        "timestamp DOUBLE PRECISION, "
        + ", ".join([f"{c} DOUBLE PRECISION" for c in numeric] + ["weather_type TEXT"])
        + ");"
    )
    conn = connect_to_db()
    if not conn: raise RuntimeError("DB connection failed.")
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.close()
    print("Table 'irradiance' ready.")

def insert_data(day_queries):
    if not API_KEY: raise RuntimeError("Set SOLCAST_API_KEY.")
    if not isinstance(day_queries, (list, tuple)) or not day_queries:
        raise ValueError("day_queries must be a non-empty list of {'start','duration'} dicts.")
    coords = _read_latlon(LOCATIONS_CSV)

    rows = []
    total_requests = len(coords) * len(day_queries)

    # One global progress bar
    with tqdm(total=total_requests, desc="Fetching Solcast", unit="req") as pbar:
        for (lat, lon) in coords:
            for q in day_queries:
                url = _solcast_url(lat, lon, q["start"], q["duration"])
                resp = requests.get(url, timeout=60)
                if resp.status_code != 200:
                    raise RuntimeError(f"Solcast {resp.status_code}: {resp.text[:200]}")
                data = resp.json().get("estimated_actuals") or resp.json().get("data") or []
                for it in data:
                    t_iso = it.get("period_end") or it.get("time") or it.get("timestamp")
                    if not t_iso: 
                        continue
                    ts = _iso_to_epoch(t_iso)
                    row = [lat, lon, ts]
                    for p in PARAMS:
                        v = it.get(p)
                        row.append(None if v is None else (str(v) if p == "weather_type" else float(v)))
                    rows.append(tuple(row))
                pbar.update(1)

    if not rows:
        print("No rows to insert."); return

    sql = f"INSERT INTO irradiance ({', '.join(COLS)}) VALUES %s"
    conn = connect_to_db()
    if not conn: raise RuntimeError("DB connection failed.")
    with conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM irradiance;")
            execute_values(cur, sql, rows, page_size=10000)
    conn.close()
    print(f"Inserted {len(rows)} rows.")

if __name__ == "__main__":
    init_table()

    start_d = date(2024, 7, 1)
    end_d   = date(2024, 7, 31)
    days = (end_d - start_d).days + 1

    day_windows = [
        {"start": f"{start_d.isoformat()}T00:00:00Z", "duration": f"P{days}D"}
    ]

    insert_data(day_windows)
