# tracker/utils.py
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def is_inside_geofence(lat, lon, geofence):
    dist = haversine_distance(lat, lon, geofence.center_lat, geofence.center_lon)
    return dist <= geofence.radius_m, dist
