# Pick nearest real DB point to each 5000 m target (no interpolation), output data/route_resampled_nearest.csv with latitude, longitude only

import csv
import math
import bisect
import os
from connect import connect_to_db

TABLE   = "route_model"      
STEP_M  = 5000.0
OUTDIR  = "data"
OUTFILE = os.path.join(OUTDIR, "asc24latlong.csv")

def fetch_points():
    """Fetch (distance, lat, lon) ordered by distance. Deduplicate exact duplicates."""
    q = f"""
        SELECT distance::float8 AS d,
               lat::float8      AS lat,
               "long"::float8   AS lon
        FROM {TABLE}
        WHERE distance IS NOT NULL AND lat IS NOT NULL AND "long" IS NOT NULL
        ORDER BY distance ASC;
    """
    with connect_to_db() as con, con.cursor() as cur:
        cur.execute(q)
        rows = cur.fetchall()

    cleaned = []
    last_d = None
    for d, lat, lon in rows:
        if last_d is None or d != last_d:
            cleaned.append((d, lat, lon))
            last_d = d
    return cleaned

def targets_from_range(dmin, dmax, step):
    start = math.ceil(dmin / step) * step
    if start > dmax:
        return []
    kmax = int(math.floor((dmax - start) / step))
    return [start + k * step for k in range(kmax + 1)]

def pick_nearest(points, targets):
    """For each target distance, pick the DB row closest in distance."""
    dists = [p[0] for p in points]
    out = []
    for td in targets:
        j = bisect.bisect_left(dists, td)
        cand = []
        if j > 0:
            cand.append(points[j-1])
        if j < len(points):
            cand.append(points[j])
        best = min(cand, key=lambda r: abs(r[0] - td))
        _, lat, lon = best
        out.append((lat, lon))
    return out

def main():
    pts = fetch_points()
    if not pts:
        print("No points found in DB.")
        return

    dmin, dmax = pts[0][0], pts[-1][0]
    targets = targets_from_range(dmin, dmax, STEP_M)
    if not targets:
        print("No targets in range. Check data vs step.")
        return

    samples = pick_nearest(pts, targets)

    os.makedirs(OUTDIR, exist_ok=True)
    with open(OUTFILE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["latitude", "longitude"])
        for lat, lon in samples:
            w.writerow([f"{lat:.8f}", f"{lon:.8f}"])

    print(f"Wrote {len(samples)} rows to {OUTFILE} (nearest real DB points).")

if __name__ == "__main__":
    main()
