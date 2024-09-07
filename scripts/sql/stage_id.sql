UPDATE base_route
SET stage_id = subquery.stage_id
FROM (
    SELECT
        id,
        symbol,
        symbol || FLOOR((SUM(geopy_dist_from_last_m) OVER (
            PARTITION BY symbol 
            ORDER BY id ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) - 1) / 3000 + 1)::TEXT AS stage_id
    FROM
        base_route
) AS subquery
WHERE
    base_route.id = subquery.id;