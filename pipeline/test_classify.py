"""Quick test: classify one inspection and print the result."""
from dotenv import load_dotenv
load_dotenv()

import json
import classify

# The Masala inspection from output/restaurants.json
test_inspection = {
    "place_id": "ChIJI8DN6SrMXVMRAlYA9CtSAhw",
    "inspection_unid": "F2CB612D46C1CB0187258DF400627AF3",
    "type": "Routine",
    "date": "2026-05-11",
    "rfi_count": 1,
    "violations": [
        {
            "code": "6-202.15",
            "description": "Outer openings not protected against the entry of insects and/or rodents.",
            "is_rfi": False,
            "observations": "Today all the doors in the establishment are open, no screens are in place.",
        },
        {
            "code": "7-202.12",
            "description": "Sanitizer concentration exceeds maximum allowed strength.",
            "is_rfi": True,
            "observations": "Today the chlorine (bleach) sanitizer was above 100 ppm. Ensure chlorine sanitizer is maintained between 50-100 ppm.",
        },
    ],
}

print("Calling Claude...")
result = classify.classify_inspection(test_inspection)
print("\n--- Result ---")
print(f"Summary: {result.get('summary')}")
for v in result.get("violations", []):
    cl = v.get("classification", {})
    print(f"\n  [{v['code']}] {cl.get('severity', 'UNCLASSIFIED')}")
    print(f"  {cl.get('reasoning', '')}")
