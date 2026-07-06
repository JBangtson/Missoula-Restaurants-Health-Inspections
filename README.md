# Missoula Food Safety — Project Architecture

## Overview

A weekly automated pipeline that scrapes restaurant and health inspection data for Missoula, MT, classifies violation severity using Claude AI, and serves the results to a public-facing map and search interface.

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     GOOGLE CLOUD SCHEDULER                      │
│                        (weekly cron)                            │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CLOUD RUN JOB (main pipeline)                 │
│                        pipeline/main.py                         │
│                                                                 │
│  Step 1 — Places (monthly gate)                                 │
│    if days_since(last_places_fetch) >= 30:                      │
│      fetch_google_places()  →  GCS /restaurants/latest.json    │
│      update GCS /metadata/last_places_fetch.json               │
│                                                                 │
│  Step 2 — Inspections (every run)                               │
│    scrape_missoula_county()  →  raw inspection records          │
│    diff_against_snapshot()   →  new inspections only            │
│    update GCS /inspections/snapshots/latest.json               │
│                                                                 │
│  Step 3 — Classify (new inspections only)                       │
│    for each new inspection:                                     │
│      classify_violations()  →  Claude API                       │
│      attach severity + reasoning to violation records           │
│      derive worst_recent_severity for restaurant pin color      │
│                                                                 │
│  Step 4 — Notify                                                │
│    if any Critical or High violations found:                    │
│      send_alert()  →  Gmail (you, for now)                      │
│      log to GCS /alerts/log/YYYY-MM-DD.json                    │
│                                                                 │
│  Step 5 — Write                                                 │
│    merge restaurants + classified inspections                   │
│    write GCS /output/restaurants.json  (frontend reads this)   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        GCS BUCKETS                              │
├─────────────────────────────────────────────────────────────────┤
│  /restaurants/                                                  │
│    latest.json              ← Google Places data                │
│                                                                 │
│  /inspections/                                                  │
│    raw/YYYY-MM-DD.json      ← full scraped records per run      │
│    snapshots/latest.json    ← inspection_unids from last run    │
│                             (used for diffing)                  │
│                                                                 │
│  /output/                                                       │
│    restaurants.json         ← merged + classified, frontend     │
│                               reads this directly               │
│                                                                 │
│  /alerts/                                                       │
│    log/YYYY-MM-DD.json      ← alert history                     │
│                                                                 │
│  /metadata/                                                     │
│    last_places_fetch.json   ← timestamp gate for monthly fetch  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (static, GCS hosted)                │
│                        frontend/                                │
│                                                                 │
│  map.html                   ← Leaflet map                       │
│    pins color coded by worst_recent_severity:                   │
│      Critical → red                                             │
│      High     → orange                                          │
│      Medium   → yellow                                          │
│      Low      → green                                           │
│      None     → gray                                            │
│                                                                 │
│  index.html                 ← Search + index page               │
│    all restaurants listed                                       │
│    dropdowns per restaurant → inspection history                │
│    filters: severity, date, violation type                      │
│                                                                 │
│  Both pages read:  /output/restaurants.json                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Repo Structure

```
missoula-food-safety/
│
├── pipeline/
│   ├── main.py                  # entry point, orchestrates all steps
│   ├── places.py                # Google Places API fetch
│   ├── scraper.py               # Missoula County health dept scraper
│   ├── diff.py                  # snapshot comparison, detect new inspections
│   ├── classify.py              # Claude API classification logic
│   ├── notify.py                # Gmail alert
│   ├── storage.py               # GCS read/write helpers
│   └── requirements.txt
│
├── frontend/
│   ├── map.html                 # Leaflet map
│   ├── index.html               # Search + index page
│   ├── style.css
│   └── app.js
│
├── data/                        # local dev copies of GCS data
│   └── .gitignore               # don't commit real inspection data
│
├── ARCHITECTURE.md              # this file
├── .env.example                 # env vars needed (no secrets committed)
└── README.md
```

---

## Data Flow — Single Restaurant Record

After the pipeline runs, each restaurant in `/output/restaurants.json` looks like:

```json
{
  "place_id": "ChIJO_X9AyrMXVMRokpqlcZah1Q",
  "google_name": "The Old Post",
  "address": "103 W Spruce St, Missoula, MT 59802",
  "latitude": 46.8740596,
  "longitude": -113.9935149,
  "worst_recent_severity": "High",
  "last_inspection_date": "2025-04-22",
  "inspections": [
    {
      "date": "2025-04-22",
      "type": "Routine",
      "rfi_count": 2,
      "violations": [
        {
          "code": "3-501.17",
          "description": "Ready-to-eat TCS food improperly date marked.",
          "is_rfi": true,
          "observations": "Fresh squeezed lemon juice not labeled...",
          "classification": {
            "severity": "Medium",
            "reasoning": "Missing date labels risk serving expired TCS food but no immediate contamination observed."
          }
        }
      ]
    }
  ]
}
```

---

## Classification Severity Scale

| Severity | Meaning | Example violations |
|---|---|---|
| **Critical** | Immediate risk of foodborne illness | Undercooking raw animal foods, fecal coliform in water |
| **High** | Likely risk if not corrected quickly | Improper cold holding temps, ROP without HACCP plan |
| **Medium** | Risk if pattern continues | Missing date labels, inadequate time control documentation |
| **Low** | Minor / procedural | Missing test strips, signage issues, minor facility cleanliness |

`worst_recent_severity` on each restaurant reflects the most severe violation found in the **most recent routine inspection only** — not all-time worst.

---

## Environment Variables

```bash
GOOGLE_PLACES_API_KEY=
ANTHROPIC_API_KEY=
GCS_BUCKET_NAME=
GMAIL_SENDER=
ALERT_RECIPIENT=          # your email, for now
GOOGLE_CLOUD_PROJECT=
```

---

## Future Extensions

- **Subscriptions** — users subscribe to specific restaurants, get alerted on new Critical/High violations
- **FastAPI layer** — add endpoints if public API becomes useful, with Cloud Run auth to prevent abuse
- **Multi-county** — same pipeline pointed at other MT county health dept sites
- **Trend scoring** — flag restaurants with repeated violations across inspections, not just latest