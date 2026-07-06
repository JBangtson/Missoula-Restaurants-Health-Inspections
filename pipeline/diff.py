"""
Snapshot diffing — identifies new inspections since the last pipeline run.

GCS path: inspections/snapshots/latest.json  →  list of seen inspection_unids
"""

from dateutil import parser as dp
from storage import Storage


def _normalize_date(date_str: str) -> str:
    if not date_str:
        return ""
    if len(date_str) == 10 and date_str[4] == "-":
        return date_str
    try:
        return dp.parse(date_str).strftime("%Y-%m-%d")
    except Exception:
        return date_str

SNAPSHOT_PATH = "inspections/snapshots/latest.json"


def load_snapshot(storage: Storage) -> set[str]:
    data = storage.read_json(SNAPSHOT_PATH)
    return set(data) if data else set()


def save_snapshot(storage: Storage, raw_data: dict):
    all_unids = [
        insp["inspection_unid"]
        for r in raw_data.values()
        for match in r.get("health_dept_matches", [])
        for insp in match.get("inspections", [])
        if insp.get("inspection_unid")
    ]
    storage.write_json(SNAPSHOT_PATH, all_unids)
    print(f"Diff: snapshot saved with {len(all_unids)} inspection UNIDs")


def find_new_inspections(raw_data: dict, snapshot: set[str]) -> list[dict]:
    """
    Returns flattened inspection records whose UNIDs are not in the snapshot.
    Each record: {place_id, inspection_unid, type, date, rfi_count, violations}
    """
    new = []
    for place_id, restaurant in raw_data.items():
        for match in restaurant.get("health_dept_matches", []):
            for insp in match.get("inspections", []):
                unid = insp.get("inspection_unid")
                if not unid or unid in snapshot:
                    continue
                detail = insp.get("detail", {})
                new.append({
                    "place_id": place_id,
                    "inspection_unid": unid,
                    "type": insp.get("type") or detail.get("type", ""),
                    "date": _normalize_date(detail.get("date") or insp.get("date", "")),
                    "rfi_count": detail.get("rfi_count", 0),
                    "violations": detail.get("violations", []),
                })

    print(f"Diff: {len(new)} new inspection(s) since last run")
    return new
