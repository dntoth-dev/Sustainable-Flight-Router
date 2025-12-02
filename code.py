import os
import board
import busio
import time
import math

# Initialise UART
uart = busio.UART(board.GP16, board.GP17, baudrate=9600, timeout=0)
counter = 0


airports = "airports_short.csv"
fixes = "fixes_short.csv"
routes = "routes.csv"

# region Fetching airport coordinates from the .csv file by entering the airport ICAO identifier
def fetch_airport_lat(icao):
    with open(airports, "r") as file:
        next(file)
        for line in file:
            parts = line.strip().split(';')
            if parts[0] == icao.upper():
                lat = parts[9]
                return lat
            else:
                continue
            
def fetch_airport_long(icao):
    with open(airports, "r") as file:
        next(file)
        for line in file:
            parts = line.strip().split(';')
            if parts[0] == icao.upper():
                long = parts[10]
                return long
            else:
                continue
# endregion

# region Fetching the coordinates of fixes from the .csv file by entering their unique, 5 letter identifier
def fetch_fix_lat(id):
    with open(fixes, "r") as file:
        next(file)
        for line in file:
            parts = line.strip().split(';')
            if parts[0] == id.upper():
                lat = parts[1]
                return lat
            else:
                continue
            
def fetch_fix_long(id):
    with open(fixes, "r") as file:
        next(file)
        for line in file:
            parts = line.strip().split(';')
            if parts[0] == id.upper():
                long = parts[2]
                return long
            else:
                continue
# endregion

# One list will store all the routes, each list element is a route
default_routes = []

# Opening routes.csv, going through elements of routes. Includes element logic, which filters against empty cells
with open(routes, "r") as file:
    next(file)
    for line in file:
        current_route = []
        parts = line.strip().split(';')
        for piece in parts:
            if piece.isalpha(): # Exclude empty cells
                current_route.append(piece)
        default_routes.append(current_route)

deps = [] # List for all departure airports
arrs = [] # List for all arrival airports

for route in default_routes:
    deps.append(route[0])
    arrs.append(route[len(route)-1])
    
EARTH_RADIUS_KM = 6371.0088
    
def haversine_distance_wgs84(lat1, lon1, lat2, lon2):
    """
    Calculates the great-circle distance between two points 
    (given in decimal degrees) on the surface of the Earth using 
    the Haversine formula with the WGS-84 mean radius.
    
    This is a simplification that is highly accurate for distances 
    up to a few hundred kilometers and provides a good compromise 
    on the Pico W.
    """
    
    # 1. Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))

    # 2. Calculate the difference in latitudes and longitudes
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # 3. Apply the Haversine formula components:
    
    # Haversine part (a)
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    
    # Angular distance part (c) = 2 * atan2(math.sqrt(a), math.sqrt(1 - a))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    # 4. Calculate the distance (Distance = Radius * c)
    distance = EARTH_RADIUS_KM * c
    
    return distance    
    
def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlon = lon2_rad - lon1_rad
    
    y = math.sin(dlon) * math.cos(lat2_rad)
    x = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)
    
    # Bearing in radians, then convert to degrees and normalize (0 to 360)
    bearing_rad = math.atan2(y, x)
    bearing_deg = math.degrees(bearing_rad)
    
    return (bearing_deg + 360) % 360
