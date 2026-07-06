"""
Google Places API fetch for all restaurants in Missoula.

Uses a grid search to cover the Missoula bounding box, deduplicates by place_id.
Gated to run at most once every 30 days.
"""

import os
import time
from datetime import datetime, timezone
from math import cos, radians

import requests

from storage import Storage

MISSOULA_BOUNDS = {
    "min_lat": 46.80,
    "max_lat": 46.94,
    "min_lng": -114.12,
    "max_lng": -113.91,
}
SEARCH_RADIUS_METERS = 500
STEP_SIZE_METERS = 500
PLACES_REFRESH_DAYS = 30

PLACES_PATH = "restaurants/latest.json"
METADATA_PATH = "metadata/last_places_fetch.json"


def should_fetch(storage: Storage) -> bool:
    meta = storage.read_json(METADATA_PATH)
    if not meta:
        return True
    last = datetime.fromisoformat(meta["last_fetch"]).replace(tzinfo=timezone.utc)
    age_days = (datetime.now(timezone.utc) - last).days
    return age_days >= PLACES_REFRESH_DAYS


def fetch_and_store(storage: Storage) -> list[dict]:
    restaurants = _get_all_restaurants()
    storage.write_json(PLACES_PATH, restaurants)
    storage.write_json(METADATA_PATH, {"last_fetch": datetime.now(timezone.utc).isoformat()})
    print(f"Places: fetched {len(restaurants)} restaurants → {PLACES_PATH}")
    return restaurants


# ---------------------------------------------------------------------------
# Grid search helpers (adapted from etl/extract/google_places/)
# ---------------------------------------------------------------------------

def _meters_to_degrees_lat(meters):
    return meters / 111320


def _meters_to_degrees_lng(meters, latitude):
    return meters / (111320 * cos(radians(latitude)))


def _generate_grid_points(bounds, step_meters):
    mid_lat = (bounds["min_lat"] + bounds["max_lat"]) / 2
    step_lat = _meters_to_degrees_lat(step_meters)
    step_lng = _meters_to_degrees_lng(step_meters, mid_lat)

    points = []
    lat = bounds["min_lat"]
    while lat <= bounds["max_lat"]:
        lng = bounds["min_lng"]
        while lng <= bounds["max_lng"]:
            points.append((lat, lng))
            lng += step_lng
        lat += step_lat
    return points


def _search_at_point(api_key, lat, lng, radius_meters) -> list[dict]:
    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.location,places.formattedAddress,places.id",
    }
    places = []
    next_page_token = None

    while True:
        body = {
            "includedTypes": ["restaurant"],
            "maxResultCount": 20,
            "locationRestriction": {
                "circle": {
                    "center": {"latitude": lat, "longitude": lng},
                    "radius": radius_meters,
                }
            },
        }
        if next_page_token:
            body["pageToken"] = next_page_token

        resp = requests.post(url, headers=headers, json=body, timeout=15)
        if resp.status_code != 200:
            print(f"  Places API error at ({lat:.4f}, {lng:.4f}): {resp.status_code}")
            break

        data = resp.json()
        for place in data.get("places", []):
            places.append({
                "name": place.get("displayName", {}).get("text", "Unknown"),
                "latitude": place.get("location", {}).get("latitude"),
                "longitude": place.get("location", {}).get("longitude"),
                "address": place.get("formattedAddress", "Unknown"),
                "place_id": place.get("id", "Unknown"),
            })

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break
        time.sleep(2)

    return places


def _get_all_restaurants() -> list[dict]:
    api_key = os.environ["GOOGLE_PLACES_API_KEY"]
    grid = _generate_grid_points(MISSOULA_BOUNDS, STEP_SIZE_METERS)
    print(f"Places: searching {len(grid)} grid points...")

    seen: dict[str, dict] = {}
    for i, (lat, lng) in enumerate(grid):
        results = _search_at_point(api_key, lat, lng, SEARCH_RADIUS_METERS)
        for r in results:
            seen.setdefault(r["place_id"], r)
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(grid)} points searched, {len(seen)} unique restaurants")
        time.sleep(0.5)

    return list(seen.values())
