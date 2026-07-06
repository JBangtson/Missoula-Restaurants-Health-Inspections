"""
Missoula County health department scraper.

Incrementally updates inspection data stored in GCS:
- First run per restaurant: searches health dept, fetches full history
- Subsequent runs: checks for new inspection UNIDs, fetches only new details

GCS path: inspections/data.json
  {place_id: {google_name, place_id, health_dept_matches: [{estab_unid, name,
              address, info, inspections: [{type, date, inspection_unid,
              violations_summary, detail: {rfi_count, violations}}]}]}}
"""

import re
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from storage import Storage

BASE_URL = "https://www.inspectionsonline.us/mt/missoulamissoula/inspect.nsf"
DOC_VALUE_FIELDS = (
    "fld_EstabName~fld_FaciName~fld_FStreetNo~fld_FStreetName~"
    "fld_FCity~fld_FProv~fld_FPCode~fld_EstType~fld_SCPhone~"
    "fld_InspectionDate~fld_AllcvCounter~fld_AllvCounter~"
    "fld_EstTypeAlt~fld_RFvCountsUseVLib~fld_QRFICounts"
)
DELAY = 0.5
DATA_PATH = "inspections/data.json"


def scrape_all(restaurants: list[dict], storage: Storage) -> dict:
    """
    Incrementally update inspection data for all restaurants.
    Returns the full raw data dict (keyed by place_id).
    """
    data = storage.read_json(DATA_PATH) or {}
    total = len(restaurants)
    print(f"Scraper: processing {total} restaurants...")

    for i, restaurant in enumerate(restaurants, 1):
        place_id = restaurant["place_id"]
        if (i % 100) == 0:
            print(f"  [{i}/{total}] {restaurant['name']}")
        try:
            data[place_id] = _process_restaurant(restaurant, data.get(place_id, {}))
        except Exception as e:
            print(f"  ERROR [{restaurant['name']}]: {e}")
            data.setdefault(place_id, {})
        # Save progress every 50 restaurants so a crash doesn't lose everything
        if i % 50 == 0:
            storage.write_json(DATA_PATH, data)

    storage.write_json(DATA_PATH, data)
    print(f"Scraper: done, {len(data)} entries in {DATA_PATH}")
    return data


def _process_restaurant(restaurant: dict, existing: dict) -> dict:
    name = restaurant["name"]
    place_id = restaurant["place_id"]

    result = existing if existing else {
        "google_name": name,
        "google_address": restaurant.get("address", ""),
        "place_id": place_id,
        "health_dept_matches": [],
        "last_searched": None,
    }

    if not result.get("health_dept_matches"):
        search_results = search(name)
        time.sleep(DELAY)
        for sr in search_results:
            match = _fetch_all_for_match(sr["estab_unid"], sr["name"], sr["address"])
            result["health_dept_matches"].append(match)
    else:
        for match in result["health_dept_matches"]:
            known = {i["inspection_unid"] for i in match.get("inspections", [])}
            current_list = get_inspection_list(match["estab_unid"])
            time.sleep(DELAY)
            for insp in current_list:
                if insp["inspection_unid"] not in known:
                    detail = get_inspection_detail(insp["inspection_unid"])
                    match["inspections"].append({**insp, "detail": detail})
                    time.sleep(DELAY)

    result["last_searched"] = datetime.now().isoformat()
    return result


def _fetch_all_for_match(unid: str, name: str, address: str) -> dict:
    info = get_establishment_info(unid)
    time.sleep(DELAY)
    inspection_list = get_inspection_list(unid)
    time.sleep(DELAY)

    detailed = []
    for insp in inspection_list:
        detail = get_inspection_detail(insp["inspection_unid"])
        detailed.append({**insp, "detail": detail})
        time.sleep(DELAY)

    return {"estab_unid": unid, "name": name, "address": address, "info": info, "inspections": detailed}


# ---------------------------------------------------------------------------
# Low-level HTTP
# ---------------------------------------------------------------------------

def _get(url: str) -> requests.Response:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; restaurant-data-scraper/1.0)"}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search(term: str) -> list[dict]:
    clean = re.split(r"[,&]", term)[0].strip()
    query = (
        f"[fld_Program] CONTAINS kw_Food AND "
        f"([fld_EstabName] CONTAINS {clean} OR [fld_FaciName] CONTAINS {clean})"
    )
    url = (
        f"https://www.inspectionsonline.us/MT/missoulamissoula/Inspect.nsf/"
        f"SearchEstabNT?SearchView=&Query={requests.utils.quote(query)}"
        f"&SearchOrder=4&SearchWV=TRUE&SearchFuzzy=TRUE"
    )
    return _parse_search_results(_get(url).text)


def _parse_search_results(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for table in soup.find_all("table", attrs={"width": "100%"}):
        links = table.find_all("a")
        if not links:
            continue
        m = re.search(r"RestrictToCategory=([A-F0-9]{32})", links[0].get("href", ""), re.IGNORECASE)
        if not m:
            continue
        results.append({
            "name": links[0].get_text(strip=True),
            "address": links[1].get_text(strip=True) if len(links) > 1 else "",
            "estab_unid": m.group(1).upper(),
        })
    return results


# ---------------------------------------------------------------------------
# Establishment info
# ---------------------------------------------------------------------------

def get_establishment_info(estab_unid: str) -> dict:
    url = (
        f"{BASE_URL}/(ag_getDocValues)?OpenAgent="
        f"&xx_UNID={estab_unid}&xx_fldList={DOC_VALUE_FIELDS}"
    )
    return _parse_doc_values(_get(url).text)


def _parse_doc_values(text: str) -> dict:
    keys = [
        "estab_name", "facility_name", "street_no", "street_name",
        "city", "state", "postal_code", "estab_type", "phone",
        "last_inspection_date", "critical_violations", "non_critical_violations",
        "estab_type_alt", "rfi_counts", "qrfi_counts",
    ]
    values = [p.strip() for p in text.strip().split("~") if p != ""]
    return dict(zip(keys, values + [""] * max(0, len(keys) - len(values))))


# ---------------------------------------------------------------------------
# Inspection list
# ---------------------------------------------------------------------------

def get_inspection_list(estab_unid: str) -> list[dict]:
    url = f"{BASE_URL}/vw_InspectionsPubSumm-NT?OpenView&RestrictToCategory={estab_unid}"
    return _parse_inspection_list(_get(url).text)


def _parse_inspection_list(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    inspections = []
    for row in soup.find_all("div", class_="row"):
        cols = row.find_all("div", class_=lambda c: c and "column" in c)
        if not cols or any("h2" in (d.get("class") or []) for d in cols):
            continue
        links = cols[0].find_all("a") if cols else []
        if not links:
            continue
        m = re.search(r"pUNID=([A-F0-9]{32})", links[0].get("href", ""), re.IGNORECASE)
        if not m:
            continue
        inspections.append({
            "type": cols[0].get_text(strip=True) if len(cols) > 0 else "",
            "date": cols[1].get_text(strip=True) if len(cols) > 1 else "",
            "violations_summary": cols[2].get_text(strip=True) if len(cols) > 2 else "",
            "inspection_unid": m.group(1).upper(),
        })
    return inspections


# ---------------------------------------------------------------------------
# Inspection detail
# ---------------------------------------------------------------------------

def get_inspection_detail(inspection_unid: str) -> dict:
    url = f"{BASE_URL}/(ag_dspPubDetail)?OpenAgent&pUNID={inspection_unid}"
    return _parse_inspection_detail(_get(url).text)


def _parse_inspection_detail(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    result = {"establishment": "", "address": "", "date": "", "type": "", "rfi_count": 0, "violations": []}

    header_table = soup.find("table", attrs={"border": "0", "width": "100%"})
    if header_table:
        for row in header_table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            label = cells[0].get_text(strip=True).lower()
            value = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            if "inspection report" in cells[0].get_text(strip=True).lower():
                result["establishment"] = cells[0].get_text(strip=True).replace("- Inspection Report", "").strip()
            elif label == "address:":
                result["address"] = value
            elif label == "inspection date":
                result["date"] = value
            elif label == "inspection type":
                result["type"] = value
            elif "risk factor" in label:
                try:
                    result["rfi_count"] = int(re.search(r"\d+", value).group())
                except (AttributeError, ValueError):
                    pass

    for table in soup.find_all("table", class_="gt"):
        for row in table.find_all("tr", recursive=False):
            cells = row.find_all("td", recursive=False)
            if len(cells) < 2:
                continue
            code = cells[0].get_text(strip=True)
            if not re.match(r"^\d", code) and "-" not in code:
                continue
            v = _parse_violation_cell(cells[1], code)
            if v:
                result["violations"].append(v)

    return result


def _parse_violation_cell(cell, code: str) -> dict | None:
    inner = cell.find("table")
    if not inner:
        return None

    description, is_rfi, resolution, observations = "", False, "", ""
    for row in inner.find_all("tr"):
        text = row.get_text(strip=True)
        italic = row.find("i")
        if italic and not description:
            description = italic.get_text(strip=True)
        if "RISK FACTOR/INTERVENTION" in text:
            is_rfi = True
        if "RECOMMENDED RESOLUTION:" in text:
            resolution = text.replace("RECOMMENDED RESOLUTION:", "").strip()
        if "OBSERVATIONS & CORRECTIVE ACTIONS:" in text:
            observations = text.replace("OBSERVATIONS & CORRECTIVE ACTIONS:", "").strip()

    if not description and not observations:
        return None
    return {"code": code, "description": description, "is_rfi": is_rfi, "resolution": resolution, "observations": observations}
