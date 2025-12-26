import os
# import board
# import busio
import time
import math

# Initialise UART
# uart = busio.UART(board.GP16, board.GP17, baudrate=9600, timeout=0)
# counter = 0

airports = "airports_short.csv"
fixes = "fixes_short.csv"
routes = "routes.csv"

# region Fetch latitude of airports/navaids
def lat(id):
    if len(id) == 4: # Airports have a 4 letter identifier (luckily that's an easy difference to spot lets goo)
        icao = id
        with open(airports, "r") as file:
            next(file)
            for line in file:
                parts = line.strip().split(';')
                if parts[0] == icao.upper():
                    lat = parts[9]
                    return lat
    elif len(id) == 5: # Fixes have a 5 letter identifier
        navaid = id
        with open(fixes, "r") as file:
            next(file)
            for line in file:
                parts = line.strip().split(';')
                if parts[0] == navaid.upper():
                    lat = parts[1]
                    # A formula converting DMS (Degrees, Minutes, Seconds) to DD (Decimal Degrees) format, because in the fixes_short.csv, coordinates are provided like that
                    prefix = '-' if lat[0] == 'S' else ''
                    deg = lat[1:3]
                    min = lat[3:5]
                    sec = lat[5:7]
                    dec_deg = int(deg) + int(min)/60 + int(sec)/3600
                    lat_dec_deg = f"{prefix}{dec_deg}"
                    return lat_dec_deg
                else:
                    continue
    else:
        print("Please enter a 4 letter ICAO or a 5 letter NAVAID!\nNOTE: THE PROGRAM WORKS FOR EUROPEAN ROUTES ONLY!")

# endregion
# region Fetch longitude of airports/navaids
def long(id):
    if len(id) == 4: # Airports have a 4 letter identifier (luckily that's an easy difference to spot lets goo)
        icao = id
        with open(airports, "r") as file:
            next(file)
            for line in file:
                parts = line.strip().split(';')
                if parts[0] == icao.upper():
                    long = parts[10]
                    return long
    elif len(id) == 5: # Fixes have a 5 letter identifier
        navaid = id
        with open(fixes, "r") as file:
            next(file)
            for line in file:
                parts = line.strip().split(';')
                if parts[0] == navaid.upper():
                    long = parts[2]
                    # A formula converting DMS (Degrees, Minutes, Seconds) to DD (Decimal Degrees) format, because in the fixes_short.csv, coordinates are provided like that
                    prefix = '-' if long[0] == 'W' else ''
                    deg = long[1:4]
                    min = long[4:6]
                    sec = long[6:8]
                    dec_deg = int(deg) + int(min)/60 + int(sec)/3600
                    long_dec_deg = f"{prefix}{dec_deg}"
                    return long_dec_deg
    else:
        print("CoordinateError: An invalid ICAO/NAVAID was provided, or its coordinates cannot be called.")
# endregion

EARTH_RADIUS_KM = 6371.0088

# Distance calculation with haversine formula (original name: haversine_distance_wgs84)
def haversine(lat1, lon1, lat2, lon2):
    """
    Calculates the great-circle distance between two points 
    (given in decimal degrees) on the surface of the Earth using 
    the Haversine formula with the WGS-84 mean radius.
    
    This is a simplification that is highly accurate for distances 
    up to a few hundred kilometers and provides a good compromise 
    on the Pico W.
    """
    try:
        # 1. Convert latitude and longitude from degrees to radians
        lat1_rad, lon1_rad = math.radians(float(lat1)), math.radians(float(lon1))
        lat2_rad, lon2_rad = math.radians(float(lat2)), math.radians(float(lon2))

        # 2. Calculate the difference in latitudes and longitudes
        dlat, dlon = lat2_rad - lat1_rad, lon2_rad - lon1_rad

        # 3. Apply the Haversine formula components:
        
        # Haversine part (a)
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        
        # Angular distance part (c) = 2 * atan2(math.sqrt(a), math.sqrt(1 - a))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        # 4. Calculate the distance (Distance = Radius * c)
        distance = EARTH_RADIUS_KM * c
        
        return distance   
    except:
        print("DistError: Distance cannot be calculated with the Haversine formula.\nCheck provided latitude and longitude data!")

# One list will store all the routes, each list element is a route
default_routes = []

# region Storing default route elements
with open(routes, "r") as file:
    next(file)
    for line in file:
        current_route = [p for p in line.strip().split(';') if p.isalpha()]
        if current_route:
            default_routes.append(current_route)
print("Default routes stored!")
# endregion

deps = [r[0] for r in default_routes] # List for all departure airports
arrs = [r[-1] for r in default_routes] # List for all arrival airports

# region Creating efficient routes
optimised_routes = []
for i in range(len(deps)):
    # Initially
    A = deps[i] # A point is departure airport
    B = arrs[i] # B point is arrival airport with same index
    print(f"Optimising route {i}/{len(deps)}...")
    a_lat, a_lon = lat(A), long(A)
    b_lat, b_lon = lat(B), long(B)
    
    if a_lat is None or b_lat is None:
        print(f"Skipping route {A}-{B}: Coordinates not found.")
        continue
    
    # Filter candidates into mem to avoid repeated file reading
    # considering points which are closer to the destination than the start
    total_dist = haversine(a_lat, a_lon, b_lat, b_lon)
    candidates = []
    
    with open(fixes, "r") as file:
        next(file)
        for line in file:
            parts = line.strip().split(';')
            p = parts[0]
            if len(p) == 5:
                lat_str, lon_str = parts[1], parts[2]
                
                # lat
                lat_prefix = '-' if lat_str[0] == 'W' else ''
                p_lat = float(lat_prefix + str(int(lat_str[1:3]) + int(lat_str[3:5])/60 + int(lat_str[5:7])/3600))

                # long
                lon_prefix = '-' if lon_str[0] == 'W' else ''
                p_lon = float(lon_prefix + str(int(lon_str[1:4]) + int(lon_str[4:6])/60 + int(lon_str[6:8])/3600))
                
                # check if point is within the bounding sphere of the route
                dist_to_b = haversine(p_lat, p_lon, b_lat, b_lon)
                if dist_to_b < total_dist:
                    candidates.append({'id': p, 'lat': p_lat, 'lon': p_lon, 'dist_b': dist_to_b})
                    
    # Building the route
    current_route = [A]
    curr_lat, curr_lon = float(a_lat), float(a_lon)
    
    while True:
        best_next = None
        min_step_dist = 999999
        
        curr_dist_to_dest = haversine(curr_lat, curr_lon, b_lat, b_lon)
        
        for p in candidates:
            if p['id'] in current_route: continue
            
            if p['dist_b'] < curr_dist_to_dest:
                step_dist = haversine(curr_lat, curr_lon, p['lat'], p['lon'])
                if step_dist < min_step_dist:
                    min_step_dist = step_dist
                    best_next = p
        
        if not best_next or min_step_dist > curr_dist_to_dest:
            break
        current_route.append(best_next['id'])
        curr_lat, curr_lon = best_next['lat'], best_next['lon']
    current_route.append(B)
        
    optimised_routes.append(current_route)
    print(f"Route {i+1} optimised:{' -> '.join(current_route)}")
    
# endregion