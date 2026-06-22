"""
Fetch and incrementally update health inspection data for all restaurants
in the Google Places JSON.

Run 1: Searches the health dept for each restaurant by name, fetches all
       inspection history, and saves to health_inspections.json.
Run N: For each restaurant with existing health dept matches, checks the
       inspection list for new UNIDs and fetches only those details.
"""

import json
import time
from datetime import datetime
from pathlib import Path

from get_restaurant_health_dept_data import (
    get_establishment_info,
    get_inspection_detail,
    get_inspection_list,
    search,
)

PLACES_JSON = (
    Path(__file__).parent.parent / "google_places" / "missoula_restaurants_complete.json"
)
OUTPUT_JSON = Path(__file__).parent / "health_inspections.json"
DELAY = 0.5


def load_output() -> dict:
    if OUTPUT_JSON.exists():
        with open(OUTPUT_JSON, encoding="utf-8-sig") as f:
            return json.load(f)
    return {}


def save_output(data: dict):
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _fetch_all_for_match(unid: str, name: str, address: str, delay: float) -> dict:
    info = get_establishment_info(unid)
    time.sleep(delay)
    inspection_list = get_inspection_list(unid)
    time.sleep(delay)

    detailed = []
    for insp in inspection_list:
        detail = get_inspection_detail(insp["inspection_unid"])
        detailed.append({**insp, "detail": detail})
        time.sleep(delay)

    return {
        "estab_unid": unid,
        "name": name,
        "address": address,
        "info": info,
        "inspections": detailed,
    }


def process_restaurant(restaurant: dict, existing: dict, delay: float = DELAY) -> dict:
    name = restaurant["name"]
    place_id = restaurant["place_id"]

    result = existing if existing else {
        "google_name": name,
        "google_address": restaurant["address"],
        "place_id": place_id,
        "health_dept_matches": [],
        "last_searched": None,
    }

    if not result.get("health_dept_matches"):
        # First time: search and fetch everything
        print(f"  Searching: {name}")
        search_results = search(name)
        time.sleep(delay)

        if not search_results:
            print("  No health dept results found")
        else:
            print(f"  Found {len(search_results)} health dept match(es)")
            for sr in search_results:
                match = _fetch_all_for_match(
                    sr["estab_unid"], sr["name"], sr["address"], delay
                )
                insp_count = len(match["inspections"])
                print(f"    {sr['name']}: {insp_count} inspection(s)")
                result["health_dept_matches"].append(match)
    else:
        # Subsequent runs: check for new inspection UNIDs only
        print(f"  Checking for new inspections: {name}")
        for match in result["health_dept_matches"]:
            unid = match["estab_unid"]
            known_unids = {i["inspection_unid"] for i in match.get("inspections", [])}

            current_list = get_inspection_list(unid)
            time.sleep(delay)

            new = [i for i in current_list if i["inspection_unid"] not in known_unids]
            if new:
                print(f"    {match['name']}: {len(new)} new inspection(s)")
                for insp in new:
                    detail = get_inspection_detail(insp["inspection_unid"])
                    match["inspections"].append({**insp, "detail": detail})
                    time.sleep(delay)
            else:
                print(f"    {match['name']}: up to date")

    result["last_searched"] = datetime.now().isoformat()
    return result


def main():
    with open(PLACES_JSON, encoding="utf-8") as f:
        restaurants = json.load(f)

    data = load_output()
    total = len(restaurants)
    print(f"Processing {total} restaurants...\n")

    for i, restaurant in enumerate(restaurants, 1):
        place_id = restaurant["place_id"]
        print(f"[{i}/{total}] {restaurant['name']}")
        try:
            data[place_id] = process_restaurant(restaurant, data.get(place_id, {}))
        except Exception as e:
            print(f"  ERROR: {e}")
            if place_id not in data:
                data[place_id] = {}

        save_output(data)

    print(f"\nDone. Results saved to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
