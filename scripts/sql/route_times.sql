-- Update Stage 1: Nashville to Edwardsville (Central Time UTC-5)
UPDATE base_route SET route_start_time = '2024-07-20 14:00:00', route_end_time = '2024-07-20 17:15:00' WHERE symbol = '1A';  -- Adjusted +5 hours
UPDATE base_route SET route_start_time = '2024-07-20 17:15:00', route_end_time = '2024-07-21 16:00:00' WHERE symbol = '2B';  -- Adjusted +5 hours

-- Update Stage 2: Edwardsville to St. Joseph (Central Time UTC-5)
UPDATE base_route SET route_start_time = '2024-07-22 14:00:00', route_end_time = '2024-07-22 17:15:00' WHERE symbol = '2C';  -- Adjusted +5 hours
UPDATE base_route SET route_start_time = '2024-07-22 17:15:00', route_end_time = '2024-07-23 14:30:00' WHERE symbol = '2D';  -- Adjusted +5 hours
UPDATE base_route SET route_start_time = '2024-07-23 14:30:00', route_end_time = '2024-07-23 16:45:00' WHERE symbol = '2E';  -- Adjusted +5 hours

-- Update Stage 3: St. Joseph to Kearney (Central Time UTC-5)
UPDATE base_route SET route_start_time = '2024-07-24 14:00:00', route_end_time = '2024-07-24 16:15:00' WHERE symbol = '3F';  -- Adjusted +5 hours
UPDATE base_route SET route_start_time = '2024-07-24 16:15:00', route_end_time = '2024-07-25 14:15:00' WHERE symbol = '3G';  -- Adjusted +5 hours
UPDATE base_route SET route_start_time = '2024-07-25 14:15:00', route_end_time = '2024-07-26 13:30:00' WHERE symbol = '3H';  -- Adjusted +5 hours

-- Update Stage 4: Gering to Casper (Mountain Time UTC-6)
UPDATE base_route SET route_start_time = '2024-07-27 14:00:00', route_end_time = '2024-07-27 17:15:00' WHERE symbol = '4J';  -- Adjusted +6 hours
