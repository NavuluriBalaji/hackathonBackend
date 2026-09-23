import math
import json
import urllib.request
import urllib.error

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates spatial Haversine distance in kilometers between two coordinates."""
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_realtime_route(lat1: float, lon1: float, lat2: float, lon2: float):
    """
    Fetches real-time driving route distance (km) and travel duration (minutes)
    from OpenStreetMap's free OSRM Public Routing API.
    Falls back smoothly to Haversine spatial distance if offline.
    """
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=false"

    try:
        req = urllib.request.Request(osrm_url, headers={'User-Agent': 'ProjectResilience/1.0'})
        with urllib.request.urlopen(req, timeout=2.0) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data.get("code") == "Ok" and data.get("routes"):
                    route = data["routes"][0]
                    dist_meters = route.get("distance", 0.0)
                    duration_secs = route.get("duration", 0.0)

                    dist_km = round(dist_meters / 1000.0, 2)
                    duration_mins = max(5.0, round(duration_secs / 60.0, 1))

                    return {
                        "distance_km": dist_km,
                        "duration_minutes": duration_mins,
                        "routing_engine": "OpenStreetMap (OSRM Live)",
                        "success": True
                    }
    except Exception as e:
        # Fallback to Haversine calculation if OSRM is unreachable
        pass

    # Haversine fallback with 1.25 road curvature factor & 45 km/h avg rural transport speed
    direct_km = haversine_distance(lat1, lon1, lat2, lon2)
    road_km = round(direct_km * 1.25, 2)
    est_mins = max(5.0, round((road_km / 45.0) * 60.0, 1))

    return {
        "distance_km": max(1.0, road_km),
        "duration_minutes": est_mins,
        "routing_engine": "Haversine Spatial Fallback",
        "success": True
    }
