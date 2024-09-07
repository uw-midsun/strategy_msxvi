UPDATE base_route
SET stage_elapsed_distance = subquery.cumulative_distance
FROM (
    SELECT
        id,
        SUM(geopy_dist_from_last_m) OVER (PARTITION BY symbol ORDER BY id) AS cumulative_distance
    FROM
        base_route
) AS subquery
WHERE
    base_route.id = subquery.id;
