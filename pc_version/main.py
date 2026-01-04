from geopy.distance import geodesic
import os
      
# region BACKEND

print("""
      SUSTAINABLE-FLIGHT-ROUTER
      by dntoth-dev
      GitHub: /dntoth-dev/sustainable-flight-router
      -------------------------------------------------
      If you are running the program for the first time, make sure to fill the routes.csv file with routes.
      After filling, hit enter key to continue...      
      """)
ready=input()

airports = "airports_short.csv"
fixes = "fixes_short.csv"
routes = "routes.csv"

# region Fetch latitude of airports/navaids
def lat(id):
    if not id: return None
    id = id.upper().strip()
    if len(id) == 4: # Airports have a 4 letter identifier (luckily that's an easy difference to spot lets goo)
        icao = id
        with open(airports, "r") as file:
            next(file)
            for line in file:
                parts = line.strip().split(';')
                if parts[0] == icao:
                    return float(parts[9]) # Return as float for geodesic calculations
    elif len(id) == 5: # Fixes have a 5 letter identifier
        navaid = id
        with open(fixes, "r") as file:
            next(file)
            for line in file:
                parts = line.strip().split(';')
                if parts[0] == navaid:
                    lat = parts[1]
                    # A formula converting DMS (Degrees, Minutes, Seconds) to DD (Decimal Degrees) format, because in the fixes_short.csv, coordinates are provided like that
                    prefix = -1 if lat[0] == 'S' else 1
                    deg = int(lat[1:3])
                    min = int(lat[3:5])
                    sec = int(lat[5:7])
                    dec_deg = deg + min/60 + sec/3600
                    return float(prefix * dec_deg) # Return as float for geodesic calculations)
    return None

# endregion
# region Fetch longitude of airports/navaids
def long(id):
    if not id: return None
    id = id.upper().strip()
    if len(id) == 4: # Airports have a 4 letter identifier (luckily that's an easy difference to spot lets goo)
        icao = id
        with open(airports, "r") as file:
            next(file)
            for line in file:
                parts = line.strip().split(';')
                if parts[0] == icao:
                    return float(parts[10]) # Return as float for geodesic calculations
    elif len(id) == 5: # Fixes have a 5 letter identifier
        navaid = id
        with open(fixes, "r") as file:
            next(file)
            for line in file:
                parts = line.strip().split(';')
                if parts[0] == navaid:
                    long = parts[2]
                    # A formula converting DMS (Degrees, Minutes, Seconds) to DD (Decimal Degrees) format, because in the fixes_short.csv, coordinates are provided like that
                    prefix = -1 if long[0] == 'W' else 1
                    deg = int(long[1:4])
                    min = int(long[4:6])
                    sec = int(long[6:8])
                    dec_deg = deg + min/60 + sec/3600
                    return float(prefix * dec_deg) # Return as float for geodesic calculations
    return None

def get_point(id):
    """Helper to return (lat, lon) tuple for geopy or None"""
    l, n = lat(id), long(id)
    if l is None or n is None: return None
    return (l, n)

# endregion

default_routes = []
if os.path.exists(routes):
    with open(routes, "r") as file:
        next(file)
        for line in file:
            current_route = [p.strip() for p in line.strip().split(';') if p.strip()]
            if current_route:
                default_routes.append(current_route)
print("INFO: Original routes stored successfully.")

deps = [r[0] for r in default_routes] # List of departure airports
arrs = [r[-1] for r in default_routes] # List of arrival airports

optimised_routes = []

for i in range(len(deps)):
    start = deps[i]
    arr = arrs[i]
    
    start_pt = get_point(start)
    arr_pt = get_point(arr)

    if not start_pt or not arr_pt:
        print(f"INFO: Skipping route {start}-{arr}. Coordinates not found.")
        continue
    
    total_distance = geodesic(start_pt, arr_pt).kilometers
    candidates = []
    
    with open(fixes, "r") as file:
        next(file)
        for line in file:
            parts = line.strip().split(';')
            p_id = parts[0]
            if len(p_id) == 5:
                p_pt = get_point(p_id)
                if p_pt:
                    dist_to_b = geodesic(p_pt, arr_pt).kilometers
                    if dist_to_b < total_distance:
                        candidates.append({'id': p_id, 'pt': p_pt, 'dist_b': dist_to_b})
    
    # Building the route
    current_route = [start]
    curr_pt = start_pt
    
    while True:
        best_next = None
        min_score = 999999
        
        curr_dist_to_dest = geodesic(curr_pt, arr_pt).kilometers
        
        for p in candidates:
            if p['id'] in current_route: continue
            
            p_dist_to_dest = p['dist_b']
            if p_dist_to_dest < curr_dist_to_dest:
                step_dist = geodesic(curr_pt, p['pt']).kilometers
                penalty = (step_dist + p_dist_to_dest) - curr_dist_to_dest
                
                # Scoring based on Total Path Efficiency
                # Penalty = (Step Distance + Distance Remaining) - Current Straight Line to Destination
                # This prevents "zig-zagging" to nearby points that don't actually help the route stay straight.

                score = step_dist + (penalty * 3.0)
                    
                if score < min_score:
                    min_score = score
                    best_next = p
        
        if not best_next or min_score > curr_dist_to_dest:
            break
        current_route.append(best_next['id'])
        curr_pt = best_next['pt']

    current_route.append(arr)
    optimised_routes.append(current_route)
    print(f"INFO: Route {i+1} optimised.")
    
# calculating distances with safety for missing waypoints
def calc_route_dist(route):
    dists = []
    for idx in range(len(route) - 1):
        p1 = get_point(route[idx])
        p2 = get_point(route[idx+1])
        if p1 and p2:
            dists.append(geodesic(p1, p2).kilometers)
        else:
            dists.append(0.0) # Segment skipped due to missing data
    return dists

optimised_routes_dists = [calc_route_dist(r) for r in optimised_routes]
default_routes_dists = [calc_route_dist(r) for r in default_routes]

while True:
    print(f"Type a number to show the associated route (1-{len(optimised_routes)}) or 'q' to quit")
    num = input()
    if num.lower() == 'q': break

    try:
        n = int(num) - 1
        d_sum = sum(default_routes_dists[n])
        o_sum = sum(optimised_routes_dists[n])
        
        print(f"""
            SHOWING DETAILS FOR ROUTE {num}:
            Original route:         {' -> '.join(default_routes[n])}
            Number of waypoints:    {len(default_routes[n])-2}
            Total distance:         {d_sum:.2f} km

            Optimised route:        {' -> '.join(optimised_routes[n])}
            Number of waypoints:    {len(optimised_routes[n])-2}
            Total distance:         {o_sum:.2f} km
          
            Improvement: {d_sum - o_sum:.2f} km shorter.
          """)
    except:
        print("Invalid route number.")
# endregion