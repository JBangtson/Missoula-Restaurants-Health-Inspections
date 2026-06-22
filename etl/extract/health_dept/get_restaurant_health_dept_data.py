"""
Missoula Health Department inspection data scraper.

Flow:
  1. search(term) -> list of establishments with their UNIDs
  2. get_inspection_list(estab_unid) -> list of past inspection UNIDs + dates
  3. get_inspection_detail(inspection_unid) -> full violation data per visit
  4. get_restaurant_data(name) -> full tree for a restaurant (convenience wrapper)

All UNIDs are 32-char hex strings from the Lotus Domino backend.
"""

import re
import time
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.inspectionsonline.us/mt/missoulamissoula/inspect.nsf"

DOC_VALUE_FIELDS = (
    "fld_EstabName~fld_FaciName~fld_FStreetNo~fld_FStreetName~"
    "fld_FCity~fld_FProv~fld_FPCode~fld_EstType~fld_SCPhone~"
    "fld_InspectionDate~fld_AllcvCounter~fld_AllvCounter~"
    "fld_EstTypeAlt~fld_RFvCountsUseVLib~fld_QRFICounts"
)


# ---------------------------------------------------------------------------
# Low-level HTTP
# ---------------------------------------------------------------------------

def _get(url: str, timeout: int = 15) -> requests.Response:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; restaurant-data-scraper/1.0)"}
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp


# ---------------------------------------------------------------------------
# 1. Search
# ---------------------------------------------------------------------------

def search(term: str) -> list[dict]:
    """
    Search for food-service establishments by name.
    Returns a list of dicts: {name, address, estab_unid}
    """
    # Commas and ampersands are query-syntax characters in Lotus Notes FT search;
    # strip at the first one so "Bayern Brewing, Inc." searches as "Bayern Brewing".
    clean_term = re.split(r'[,&]', term)[0].strip()
    query = (
        f"[fld_Program] CONTAINS kw_Food AND "
        f"([fld_EstabName] CONTAINS {clean_term} OR [fld_FaciName] CONTAINS {clean_term})"
    )
    url = (
        f"https://www.inspectionsonline.us/MT/missoulamissoula/Inspect.nsf/"
        f"SearchEstabNT?SearchView=&Query={requests.utils.quote(query)}"
        f"&SearchOrder=4&SearchWV=TRUE&SearchFuzzy=TRUE"
    )
    resp = _get(url)
    return _parse_search_results(resp.text)


def _parse_search_results(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    # Each result is a <TABLE WIDTH=100%> with two <A> tags: name and address
    # The HREF contains RestrictToCategory={ESTAB_UNID}
    for table in soup.find_all("table", attrs={"width": "100%"}):
        links = table.find_all("a")
        if not links:
            continue
        href = links[0].get("href", "")
        m = re.search(r"RestrictToCategory=([A-F0-9]{32})", href, re.IGNORECASE)
        if not m:
            continue
        name = links[0].get_text(strip=True)
        address = links[1].get_text(strip=True) if len(links) > 1 else ""
        results.append({
            "name": name,
            "address": address,
            "estab_unid": m.group(1).upper(),
        })
    return results


# ---------------------------------------------------------------------------
# 2. Establishment info from ag_getDocValues
# ---------------------------------------------------------------------------

def get_establishment_info(estab_unid: str) -> dict:
    """
    Fetch basic establishment metadata via the ag_getDocValues agent.
    Returns a dict with address, type, phone, last inspection summary counts.
    """
    url = (
        f"{BASE_URL}/(ag_getDocValues)?OpenAgent="
        f"&xx_UNID={estab_unid}&xx_fldList={DOC_VALUE_FIELDS}"
    )
    resp = _get(url)
    return _parse_doc_values(resp.text)


def _parse_doc_values(text: str) -> dict:
    # Response is tilde-delimited; first char is also a tilde, so split and drop empty first
    parts = text.strip().split("~")
    keys = [
        "estab_name", "facility_name", "street_no", "street_name",
        "city", "state", "postal_code", "estab_type", "phone",
        "last_inspection_date", "critical_violations", "non_critical_violations",
        "estab_type_alt", "rfi_counts", "qrfi_counts",
    ]
    values = [p.strip() for p in parts if p != ""]
    return dict(zip(keys, values + [""] * max(0, len(keys) - len(values))))


# ---------------------------------------------------------------------------
# 3. Inspection list from the summary view
# ---------------------------------------------------------------------------

def get_inspection_list(estab_unid: str) -> list[dict]:
    """
    Fetch the list of all past inspections for an establishment.
    Returns a list of dicts: {type, date, violations_summary, inspection_unid}
    """
    url = (
        f"{BASE_URL}/vw_InspectionsPubSumm-NT"
        f"?OpenView&RestrictToCategory={estab_unid}"
    )
    resp = _get(url)
    return _parse_inspection_list(resp.text)


def _parse_inspection_list(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    inspections = []
    # Each inspection is a <DIV class='gt row'> (skip the header row which has class 'h2')
    for row in soup.find_all("div", class_="row"):
        cols = row.find_all("div", class_=lambda c: c and "column" in c)
        if not cols:
            continue
        # Skip header rows (contain h2 class divs)
        if any("h2" in (div.get("class") or []) for div in cols):
            continue
        links = cols[0].find_all("a") if cols else []
        if not links:
            continue
        href = links[0].get("href", "")
        m = re.search(r"pUNID=([A-F0-9]{32})", href, re.IGNORECASE)
        if not m:
            continue
        insp_type = cols[0].get_text(strip=True) if len(cols) > 0 else ""
        date = cols[1].get_text(strip=True) if len(cols) > 1 else ""
        violations_summary = cols[2].get_text(strip=True) if len(cols) > 2 else ""
        inspections.append({
            "type": insp_type,
            "date": date,
            "violations_summary": violations_summary,
            "inspection_unid": m.group(1).upper(),
        })
    return inspections


# ---------------------------------------------------------------------------
# 4. Full inspection detail
# ---------------------------------------------------------------------------

def get_inspection_detail(inspection_unid: str) -> dict:
    """
    Fetch the full violation detail for a single inspection visit.
    Returns {establishment, address, date, type, rfi_count, violations: [...]}
    Each violation: {code, description, is_rfi, resolution, observations}
    """
    url = f"{BASE_URL}/(ag_dspPubDetail)?OpenAgent&pUNID={inspection_unid}"
    resp = _get(url)
    return _parse_inspection_detail(resp.text)


def _parse_inspection_detail(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    result = {
        "establishment": "",
        "address": "",
        "estab_type": "",
        "phone": "",
        "date": "",
        "type": "",
        "rfi_count": 0,
        "violations": [],
    }

    # --- Header table (establishment info + inspection metadata) ---
    header_table = soup.find("table", attrs={"border": "0", "width": "100%"})
    if header_table:
        rows = header_table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if not cells:
                continue
            label = cells[0].get_text(strip=True).lower()
            value = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            if "inspection report" in cells[0].get_text(strip=True).lower():
                # Title cell: "ESTABLISHMENT NAME - Inspection Report"
                title = cells[0].get_text(strip=True)
                result["establishment"] = title.replace("- Inspection Report", "").strip()
            elif label == "address:":
                result["address"] = value
            elif label == "establishment type:":
                result["estab_type"] = value
            elif label == "phone no.:":
                result["phone"] = value
            elif label == "inspection date":
                result["date"] = value
            elif label == "inspection type":
                result["type"] = value
            elif "risk factor" in label:
                try:
                    result["rfi_count"] = int(re.search(r"\d+", value).group())
                except (AttributeError, ValueError):
                    pass

    # --- Violation detail table ---
    tables = soup.find_all("table", class_="gt")
    for table in tables:
        rows = table.find_all("tr", recursive=False)
        for row in rows:
            cells = row.find_all("td", recursive=False)
            if len(cells) < 2:
                continue
            code_cell = cells[0]
            detail_cell = cells[1]
            code = code_cell.get_text(strip=True)
            # Skip header rows and non-violation rows
            if not re.match(r"^\d", code) and "-" not in code:
                continue
            violation = _parse_violation_cell(detail_cell, code)
            if violation:
                result["violations"].append(violation)

    return result


def _parse_violation_cell(cell, code: str) -> dict | None:
    inner_tables = cell.find_all("table")
    if not inner_tables:
        return None
    inner = inner_tables[0]
    rows = inner.find_all("tr")

    description = ""
    is_rfi = False
    resolution = ""
    observations = ""

    for row in rows:
        text = row.get_text(strip=True)
        cells = row.find_all("td")
        if not cells:
            continue
        cell_text = cells[0].get_text(strip=True) if cells else ""

        # Description is in an <i> tag
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

    return {
        "code": code,
        "description": description,
        "is_rfi": is_rfi,
        "resolution": resolution,
        "observations": observations,
    }


# ---------------------------------------------------------------------------
# 5. High-level convenience wrapper
# ---------------------------------------------------------------------------

def get_restaurant_data(name: str, delay: float = 0.5) -> list[dict]:
    """
    Search for a restaurant by name and return all inspection data.
    Returns a list of matches, each with full inspection history.
    delay: seconds to sleep between requests (be polite to the server)
    """
    establishments = search(name)
    results = []
    for estab in establishments:
        unid = estab["estab_unid"]
        info = get_establishment_info(unid)
        time.sleep(delay)
        inspections = get_inspection_list(unid)
        time.sleep(delay)
        detailed_inspections = []
        for insp in inspections:
            detail = get_inspection_detail(insp["inspection_unid"])
            detailed_inspections.append(detail)
            time.sleep(delay)
        results.append({
            "search_result": estab,
            "info": info,
            "inspections": detailed_inspections,
        })
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    term = sys.argv[1] if len(sys.argv) > 1 else "PAULS"
    print(f"Searching for: {term}\n")

    matches = search(term)
    print(f"Found {len(matches)} establishment(s):")
    for m in matches:
        print(f"  {m['name']}  ({m['estab_unid']})")
        print(f"    {m['address']}")

    if "--full" in sys.argv:
        print("\nFetching full inspection history...\n")
        data = get_restaurant_data(term)
        output_file = f"health_dept_{term.lower()}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"Saved to {output_file}")
    elif matches:
        print("\nFetching inspections for first result...")
        unid = matches[0]["estab_unid"]
        inspections = get_inspection_list(unid)
        print(f"\n{len(inspections)} inspection(s) found:")
        for i in inspections:
            print(f"  [{i['date']}] {i['type']} — {i['violations_summary']}")

        if inspections:
            print(f"\nFetching detail for most recent inspection...")
            detail = get_inspection_detail(inspections[0]["inspection_unid"])
            print(f"  Date:  {detail['date']}")
            print(f"  Type:  {detail['type']}")
            print(f"  RFI:   {detail['rfi_count']}")
            print(f"  Violations ({len(detail['violations'])}):")
            for v in detail["violations"]:
                rfi = " [RFI]" if v["is_rfi"] else ""
                print(f"    {v['code']}{rfi}: {v['description'][:80]}")
