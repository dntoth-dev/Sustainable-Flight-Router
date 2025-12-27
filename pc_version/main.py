from geopy.distance import geodesic
import os

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

default_routes = []

with open(routes, "r") as file:
    next(file)
    for line in file:
        current_route = [p for p in line.strip().split(';') if p.isalpha()]
        if current_route:
            default_routes.append(current_route)
            print("Original routes stored successfully.")

deps = [r[0] for r in default_routes] # List of departure airports
arrs = [r[-1] for r in default_routes] # List of arrival airports

optimised_routes = []

for i in range(len(deps)):
    start = deps[i]
    arr = arrs[i]
    
    start_lat, start_lon = lat(start), long(start)
    arr_lat, arr_lon = lat(arr), long(arr)
    
    if start_lat is None or arr_lat is None:
        print(f"Skipping route {start}-{arr}. Coordinates not found.")
        continue
    
    total_distance = geodesic((start_lat, start_lon), (arr_lat, arr_lon))
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
                dist_to_b = geodesic((p_lat, p_lon), (arr_lat, arr_lon))
                if dist_to_b < total_distance:
                    candidates.append({'id': p, 'lat': p_lat, 'lon': p_lon, 'dist_b': dist_to_b})
    
    # Building the route
    current_route = [start]
    curr_lat, curr_lon = float(start_lat), float(start_lon)
    
    while True:
        best_next = None
        min_step_dist = 999999
        
        curr_dist_to_dest = geodesic((curr_lat, curr_lon), (arr_lat, arr_lon))
        
        for p in candidates:
            if p['id'] in current_route: continue
            
            if p['dist_b'] < curr_dist_to_dest:
                step_dist = geodesic((curr_lat, curr_lon), (p['lat'], p['lon']))
                if step_dist < min_step_dist:
                    min_step_dist = step_dist
                    best_next = p
        
        if not best_next or min_step_dist > curr_dist_to_dest:
            break
        current_route.append(best_next['id'])
        curr_lat, curr_lon = best_next['lat'], best_next['lon']
    current_route.append(arr)
        
    optimised_routes.append(current_route)
    print(f"Route {i+1} optimised:{' -> '.join(current_route)}\n{'*'*20}")