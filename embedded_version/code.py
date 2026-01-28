import math
import gc
import busio
import time
import board

# region BACKEND

print("""
      SUSTAINABLE-FLIGHT-ROUTER (Pico-Optimized PC Logic)
      by dntoth-dev
      -------------------------------------------------
      """)

airports_file = "airports_short.csv"
fixes_file = "fixes_short.csv"
routes_file = "routes.csv"

# Global lists to store processed route data for UART/External comms
default_routes = []
optimised_routes = []

def vincenty_distance(coord1, coord2):
    """Calculates geodesic distance (Vincenty). Accurate for Pico."""
    if not coord1 or not coord2 or None in coord1 or None in coord2:
        return 0.0
    if (coord1[0] == 0 and coord1[1] == 0) or (coord2[0] == 0 and coord2[1] == 0):
        return 0.0

    lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
    lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])

    a = 6378137.0
    f = 1 / 298.257223563
    b = (1 - f) * a

    L = lon2 - lon1
    U1 = math.atan((1 - f) * math.tan(lat1))
    U2 = math.atan((1 - f) * math.tan(lat2))
    sinU1, cosU1 = math.sin(U1), math.cos(U1)
    sinU2, cosU2 = math.sin(U2), math.cos(U2)

    lambda_lon = L
    for _ in range(8): # Sufficient iterations for local navigation
        sin_lambda, cos_lambda = math.sin(lambda_lon), math.cos(lambda_lon)
        sin_sigma = math.sqrt((cosU2 * sin_lambda)**2 + (cosU1 * sinU2 - sinU1 * cosU2 * cos_lambda)**2)
        if sin_sigma == 0: return 0.0
        cos_sigma = sinU1 * sinU2 + cosU1 * cosU2 * cos_lambda
        sigma = math.atan2(sin_sigma, cos_sigma)
        sin_alpha = cosU1 * cosU2 * sin_lambda / sin_sigma
        cos2_alpha = 1 - sin_alpha**2
        cos2_sigma_m = cos_sigma - 2 * sinU1 * sinU2 / cos2_alpha if cos2_alpha != 0 else 0
        C = f / 16 * cos2_alpha * (4 + f * (4 - 3 * cos2_alpha))
        lambda_prev = lambda_lon
        lambda_lon = L + (1 - C) * f * sin_alpha * (sigma + C * sin_sigma * (cos2_sigma_m + C * cos_sigma * (-1 + 2 * cos2_sigma_m**2)))
        if abs(lambda_lon - lambda_prev) < 1e-9: break

    u2 = cos2_alpha * (a**2 - b**2) / b**2
    A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2)))
    B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    delta_sigma = B * sin_sigma * (cos2_sigma_m + B / 4 * (cos_sigma * (-1 + 2 * cos2_sigma_m**2) - B / 6 * cos2_sigma_m * (-3 + 4 * sin_sigma**2) * (-3 + 4 * cos2_sigma_m**2)))
    
    return (b * A * (sigma - delta_sigma)) / 1000.0

def parse_fix_coords(l_val, n_val):
    """Converts DMS string formats from fixes_short.csv to Decimal Degrees."""
    try:
        l_prefix = -1 if l_val[0] == 'S' else 1
        lat = l_prefix * (int(l_val[1:3]) + int(l_val[3:5])/60 + int(l_val[5:7])/3600)
        n_prefix = -1 if n_val[0] == 'W' else 1
        lon = n_prefix * (int(n_val[1:4]) + int(n_val[4:6])/60 + int(n_val[6:8])/3600)
        return lat, lon
    except:
        return None

def get_point(id_to_find):
    """Locates point in CSVs without loading the whole file into RAM."""
    id_to_find = id_to_find.upper().strip()
    # Check Airports
    try:
        with open(airports_file, "r") as f:
            next(f)
            for line in f:
                if line.startswith(id_to_find + ";"):
                    parts = line.strip().split(';')
                    return (float(parts[9]), float(parts[10]))
        # Check Fixes
        with open(fixes_file, "r") as f:
            next(f)
            for line in f:
                if line.startswith(id_to_find + ";"):
                    parts = line.strip().split(';')
                    return parse_fix_coords(parts[1], parts[2])
    except:
        pass
    return None

def find_optimised_route(start_id, arr_id):
    """
    Finds a route that balances efficiency and waypoint count.
    Dynamically limits waypoints based on distance to prevent unnecessary turns.
    """
    start_pt = get_point(start_id)
    arr_pt = get_point(arr_id)
    if not start_pt or not arr_pt: return [start_id, arr_id]

    route = [start_id]
    curr_pt = start_pt
    direct_dist = vincenty_distance(start_pt, arr_pt)
    
    # Adaptive limit: 1 waypoint per 100km, min 2, max 6 (total 8 points)
    max_waypoints = max(2, min(6, int(direct_dist / 100)))
    
    for _ in range(max_waypoints): 
        curr_to_dest = vincenty_distance(curr_pt, arr_pt)
        
        # Stop adding waypoints if we are close or if direct flight is already short
        if curr_to_dest < 60: break 
        
        best_fix_id = None
        best_fix_pt = None
        best_score = 999999.0
        
        # Determine the "sweet spot" for the next waypoint distance
        min_step = direct_dist * 0.12
        max_step = direct_dist * 0.30

        with open(fixes_file, "r") as f:
            next(f)
            for line in f:
                parts = line.split(';')
                p_id = parts[0]
                if len(p_id) != 5 or p_id in route: continue
                
                p_pt = parse_fix_coords(parts[1], parts[2])
                if not p_pt: continue
                
                dist_from_curr = vincenty_distance(curr_pt, p_pt)
                
                # Governor: Only look at points roughly in the right direction/distance
                if dist_from_curr < min_step or dist_from_curr > max_step: continue
                
                dist_to_arr = vincenty_distance(p_pt, arr_pt)
                
                # Strict check: Does this point actually improve the route or keep it tight?
                if (dist_from_curr + dist_to_arr) > (curr_to_dest * 1.01): continue
                if dist_to_arr >= curr_to_dest: continue 
                
                # Scoring: Penalty for deviating from the straight line
                penalty = (dist_from_curr + dist_to_arr) - curr_to_dest
                score = dist_from_curr + (penalty * 6.0) # Heavier penalty for deviations
                
                if score < best_score:
                    best_score = score
                    best_fix_id = p_id
                    best_fix_pt = p_pt

        if best_fix_id:
            route.append(best_fix_id)
            curr_pt = best_fix_pt
            gc.collect()
        else:
            break
            
    route.append(arr_id)
    return route

def get_route_km(r):
    total = 0.0
    for i in range(len(r)-1):
        p1 = get_point(r[i])
        p2 = get_point(r[i+1])
        total += vincenty_distance(p1, p2)
    return total

# --- Initialization and UI Loop ---

print("Optimizing routes...")
try:
    with open(routes_file, "r") as f:
        next(f)
        for line in f:
            r = [p.strip() for p in line.strip().split(';') if p.strip()]
            if len(r) < 2: continue
            
            # Store default route
            default_routes.append(r)
            
            # Process and store optimized route
            opt = find_optimised_route(r[0], r[-1])
            
            # Final Guard: Ensure optimization isn't actually worse than default
            d_orig = get_route_km(r)
            d_opt = get_route_km(opt)
            if d_opt > d_orig:
                opt = [r[0], r[-1]]
                
            optimised_routes.append(opt)
            print(f"Route {len(optimised_routes)}: {r[0]}->{r[-1]} ({len(opt)} pts)")
            gc.collect()
except Exception as e:
    print(f"Error during initialization: {e}")
    

"""
while True:
    print("\nSelect route (1-" + str(len(default_routes)) + ") or 'q':")
    cmd = input().strip().lower()
    if cmd == 'q': break
    try:
        idx = int(cmd) - 1
        orig, opt = default_routes[idx], optimised_routes[idx]
        d_orig, d_opt = get_route_km(orig), get_route_km(opt)

        print("-" * 20)
        print(f"ORIGINAL ({len(orig)} pts): {d_orig:.2f} km\n{' -> '.join(orig)}")
        print(f"OPTIMISED ({len(opt)} pts): {d_opt:.2f} km\n{' -> '.join(opt)}")
        print(f"SAVED: {d_orig - d_opt:.2f} km")
        print("-" * 20)
        
        # Note: You can now access default_routes[idx] and optimised_routes[idx]
        # here to send data via UART to your Arduino.
    except: pass
    gc.collect()
"""
UART = busio.UART(board.GP16, board.GP17, baudrate=9600, timeout=1)
default_routes = default_routes # just to know the list names, and for everything to be at one place
optimised_routes = optimised_routes

for i, route in enumerate(optimised_routes):
    for index, wp in enumerate(route):
        if index != len(route)-1:
            UART.write(f"{wp},".encode('ASCII'))
        else:
            UART.write(f"{wp};".encode('ASCII'))
        time.sleep(0.1)
    UART.write("\n".encode('ASCII'))
