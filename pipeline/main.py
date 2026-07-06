"""
Missoula Food Safety pipeline — Cloud Run Job entry point.

Steps:
  1. Places (monthly gate)  → GCS restaurants/latest.json
  2. Scrape + diff          → GCS inspections/data.json + snapshots/latest.json
  3. Classify               → Claude API, new violations only
  4. Notify                 → Gmail if Critical/High found
  5. Write output           → GCS output/restaurants.json (frontend reads this)
"""

# Load .env for local development (no-op on Cloud Run where env vars are injected)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import sys
from datetime import date

import classify
import diff
import notify
import places
import scraper
from storage import Storage


OUTPUT_PATH = "output/restaurants.json"


def main():
    storage = Storage()

    # Step 1 — Places (monthly gate)
    if places.should_fetch(storage):
        print("Step 1: fetching Google Places data...")
        restaurants = places.fetch_and_store(storage)
    else:
        print("Step 1: using cached Places data (fetched <30 days ago)")
        restaurants = storage.read_json(places.PLACES_PATH)
        if not restaurants:
            print("ERROR: no restaurants found in GCS and Places fetch is gated. Exiting.")
            sys.exit(1)

    # Step 2 — Scrape + diff
    print(f"\nStep 2: scraping health dept for {len(restaurants)} restaurants...")
    snapshot = diff.load_snapshot(storage)
    raw_data = scraper.scrape_all(restaurants, storage)
    new_inspections = diff.find_new_inspections(raw_data, snapshot)
    # Save snapshot AFTER classification so a crash doesn't permanently skip inspections
    # (moved below Step 3)

    # Step 3 — Classify only the most recent new inspection per restaurant
    if new_inspections:
        to_classify = _most_recent_per_restaurant(new_inspections)
        print(f"\nStep 3: classifying {len(to_classify)} inspection(s) (most recent per restaurant, {len(new_inspections)} new total)...")
        classified_new = classify.classify_inspections(to_classify)
    else:
        print("\nStep 3: no new inspections, skipping classification")
        classified_new = []

    diff.save_snapshot(storage, raw_data)

    # Step 4 — Notify on Critical/High violations
    if classified_new and notify.should_notify(classified_new):
        date_str = str(date.today())
        print(f"\nStep 4: sending alert for Critical/High violations...")
        notify.send_alert(classified_new, date_str)
        notify.log_alert(storage, classified_new, date_str)
    else:
        print("\nStep 4: no Critical/High violations, skipping alert")

    # Step 5 — Build and write merged output
    print("\nStep 5: building output/restaurants.json...")
    old_output = storage.read_json(OUTPUT_PATH) or []
    output = build_output(restaurants, raw_data, classified_new, old_output)
    storage.write_json(OUTPUT_PATH, output)
    print(f"Done: wrote {len(output)} restaurant records to {OUTPUT_PATH}")


def _most_recent_per_restaurant(inspections: list[dict]) -> list[dict]:
    """Return only the most recent inspection per place_id."""
    best: dict[str, dict] = {}
    for insp in inspections:
        place_id = insp.get("place_id", "")
        if not place_id:
            continue
        existing = best.get(place_id)
        if not existing or insp.get("date", "") > existing.get("date", ""):
            best[place_id] = insp
    return list(best.values())


def build_output(
    restaurants: list[dict],
    raw_data: dict,
    classified_new: list[dict],
    old_output: list[dict],
) -> list[dict]:
    """
    Merge Places metadata + raw inspection data + new/old classifications into
    the flat array format the frontend reads.
    """
    # Build lookup: inspection_unid → {violations: {code→classification}, summary: str}
    # New classifications take precedence over old ones.
    class_lookup: dict[str, dict] = {}

    for r in old_output:
        for insp in r.get("inspections", []):
            unid = insp.get("inspection_unid")
            if unid:
                class_lookup[unid] = {
                    "violations": {
                        v["code"]: v["classification"]
                        for v in insp.get("violations", [])
                        if v.get("classification")
                    },
                    "summary": insp.get("summary", ""),
                }

    for insp in classified_new:
        unid = insp.get("inspection_unid")
        if unid:
            class_lookup[unid] = {
                "violations": {
                    v["code"]: v["classification"]
                    for v in insp.get("violations", [])
                    if v.get("classification")
                },
                "summary": insp.get("summary", ""),
            }

    output = []
    for restaurant in restaurants:
        place_id = restaurant["place_id"]
        raw = raw_data.get(place_id, {})

        # Flatten health_dept_matches → single inspection list
        all_inspections = []
        for match in raw.get("health_dept_matches", []):
            for insp in match.get("inspections", []):
                unid = insp.get("inspection_unid")
                detail = insp.get("detail", {})

                violations = []
                for v in detail.get("violations", []):
                    violation = {
                        "code": v.get("code", ""),
                        "description": v.get("description", ""),
                        "is_rfi": v.get("is_rfi", False),
                        "observations": v.get("observations", ""),
                    }
                    insp_class = class_lookup.get(unid, {})
                    cl = insp_class.get("violations", {}).get(v.get("code", ""))
                    if cl:
                        violation["classification"] = cl
                    violations.append(violation)

                date_str = _normalize_date(detail.get("date") or insp.get("date", ""))
                insp_type = insp.get("type") or detail.get("type", "")

                # Deduplicate: skip if we already have this unid (multiple matches may share)
                if unid and any(i.get("inspection_unid") == unid for i in all_inspections):
                    continue

                insp_class = class_lookup.get(unid, {})
                all_inspections.append({
                    "inspection_unid": unid,
                    "type": insp_type,
                    "date": date_str,
                    "rfi_count": detail.get("rfi_count", 0),
                    "summary": insp_class.get("summary", ""),
                    "violations": violations,
                })

        all_inspections.sort(key=lambda x: x.get("date", ""), reverse=True)

        worst = classify.derive_worst_severity(all_inspections)
        last_date = all_inspections[0]["date"] if all_inspections else None

        output.append({
            "place_id": place_id,
            "google_name": restaurant.get("name", ""),
            "address": restaurant.get("address", ""),
            "latitude": restaurant.get("latitude"),
            "longitude": restaurant.get("longitude"),
            "worst_recent_severity": worst,
            "last_inspection_date": last_date,
            "inspections": all_inspections,
        })

    return output


def _normalize_date(date_str: str) -> str:
    """Normalize MM/DD/YYYY or other formats to YYYY-MM-DD."""
    if not date_str:
        return ""
    # Already ISO
    if len(date_str) == 10 and date_str[4] == "-":
        return date_str
    # MM/DD/YYYY
    parts = date_str.split("/")
    if len(parts) == 3:
        m, d, y = parts
        return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
    # Try dateutil as fallback
    try:
        from dateutil import parser as dp
        return dp.parse(date_str).strftime("%Y-%m-%d")
    except Exception:
        return date_str


if __name__ == "__main__":
    main()
