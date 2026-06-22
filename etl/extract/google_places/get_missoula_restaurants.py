
import requests
import json
import time
from math import radians, cos, sin, asin, sqrt, atan2, pi

# Configuration
API_KEY = "API KEY"  # Replace with your actual API key
LATITUDE = 46.86926986283907    # Example: New York
LONGITUDE = -113.996473196707
RADIUS = 50000  # meters
MAX_RESULTS = 60  # Max 60 total (API limit)
import requests
import json
import time

46.8013275418686, -114.02724312981393

# Missoula bounding box (approximate)
# Southwest corner to Northeast corner of Missoula
MISSOULA_BOUNDS = {
    "min_lat": 46.80,   # South Missoula
    "max_lat": 46.94,   # North Missoula  
    "min_lng": -114.12, # West Missoula
    "max_lng": -113.91  # East Missoula
}

SEARCH_RADIUS_METERS = 500  # 1km radius per search
STEP_SIZE_METERS = 500  # 1.5km step (overlap ensures coverage)

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in meters"""
    R = 6371000  # Earth's radius in meters
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c

def meters_to_degrees_lat(meters):
    """Convert meters to approximate degrees latitude"""
    return meters / 111320

def meters_to_degrees_lng(meters, latitude):
    """Convert meters to approximate degrees longitude at given latitude"""
    return meters / (111320 * cos(radians(latitude)))

def generate_grid_points(bounds, step_meters):
    """Generate grid points covering the bounding box"""
    points = []
    
    # Convert step to degrees
    step_lat = meters_to_degrees_lat(step_meters)
    step_lng = meters_to_degrees_lng(step_meters, (bounds["min_lat"] + bounds["max_lat"]) / 2)
    
    # Generate grid
    lat = bounds["min_lat"]
    while lat <= bounds["max_lat"]:
        lng = bounds["min_lng"]
        while lng <= bounds["max_lng"]:
            points.append((lat, lng))
            lng += step_lng
        lat += step_lat
    
    print(f"Generated {len(points)} grid points to search")
    return points

def search_restaurants_at_point(api_key, lat, lng, radius_meters):
    """Search for restaurants at a single point using Places API"""
    url = "https://places.googleapis.com/v1/places:searchNearby"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.location,places.formattedAddress,places.id"
    }
    
    all_places = []
    next_page_token = None
    
    while True:  # Get up to 3 pages (60 results) per point
        body = {
            "includedTypes": ["restaurant"],
            "maxResultCount": 20,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": radius_meters
                }
            }
        }
        
        if next_page_token:
            body["pageToken"] = next_page_token
        
        response = requests.post(url, headers=headers, json=body)
        
        if response.status_code != 200:
            print(f"  Error at ({lat}, {lng}): {response.status_code}")
            break
        
        data = response.json()
        
        if "places" in data:
            for place in data["places"]:
                place_info = {
                    "name": place.get("displayName", {}).get("text", "Unknown"),
                    "latitude": place.get("location", {}).get("latitude"),
                    "longitude": place.get("location", {}).get("longitude"),
                    "address": place.get("formattedAddress", "Unknown"),
                    "place_id": place.get("id", "Unknown")
                }
                all_places.append(place_info)
        
        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break
        
        time.sleep(2)  # Wait before requesting next page
    
    return all_places

def get_all_restaurants_in_missoula():
    """Main function to get all restaurants in Missoula"""
    
    # Generate grid of search points
    grid_points = generate_grid_points(MISSOULA_BOUNDS, STEP_SIZE_METERS)
    
    # Store unique restaurants by place_id
    all_restaurants = {}
    
    # Search each grid point
    for i, (lat, lng) in enumerate(grid_points):
        print(f"\nSearching {i+1}/{len(grid_points)} at ({lat:.4f}, {lng:.4f})...")
        
        restaurants = search_restaurants_at_point(API_KEY, lat, lng, SEARCH_RADIUS_METERS)
        
        # Add to dictionary (deduplicate by place_id)
        new_count = 0
        for restaurant in restaurants:
            place_id = restaurant["place_id"]
            if place_id not in all_restaurants:
                all_restaurants[place_id] = restaurant
                new_count += 1
        
        print(f"  Found {len(restaurants)} restaurants this search ({new_count} new)")
        print(f"  Total unique so far: {len(all_restaurants)}")
        
        # Rate limiting to avoid quota issues
        time.sleep(0.5)
    
    return list(all_restaurants.values())

# Run the search
print("=" * 60)
print("Searching for ALL restaurants in Missoula using grid pattern")
print("=" * 60)

restaurants = get_all_restaurants_in_missoula()

# Save to JSON file
output_file = "missoula_restaurants_complete.json"
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(restaurants, f, indent=2, ensure_ascii=False)

print("\n" + "=" * 60)
print(f"✅ COMPLETE! Found {len(restaurants)} unique restaurants in Missoula")
print(f"✅ Data saved to {output_file}")
print("=" * 60)

# Print statistics
if restaurants:
    print(f"\nSample of first 10 restaurants:")
    for i, r in enumerate(restaurants[:10]):
        print(f"{i+1}. {r['name']} - {r['address']}")