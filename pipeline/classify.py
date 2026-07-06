"""
Claude-based violation classification and inspection summarization.

One API call per inspection:
  - assigns severity (Critical/High/Medium/Low) to each violation
  - writes a 2-3 sentence professional summary of the overall inspection

derive_worst_severity() is called in main.py to roll up the worst
severity from the most recent routine inspection into the restaurant record.
"""

import json

import anthropic

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low"]

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def classify_inspection(inspection: dict) -> dict:
    """
    Classifies all violations in one inspection with a single Claude call.
    Attaches classification to each violation and adds a summary field
    to the inspection dict. Modifies in-place and returns the inspection.
    """
    violations = inspection.get("violations", [])

    if not violations:
        inspection["summary"] = "No violations were recorded during this inspection."
        return inspection

    viol_lines = []
    for v in violations:
        line = f"[{v.get('code', '?')}] {v.get('description', '')}"
        if v.get("observations"):
            line += f"\n   Observations: {v['observations']}"
        if v.get("is_rfi"):
            line += "  [Risk Factor/Intervention]"
        viol_lines.append(line)

    example_violations = "\n".join(
        f'    {{"code": "{v.get("code", "?")}", "severity": "Medium", "reasoning": "one sentence explaining the risk"}}{"," if i < len(violations) - 1 else ""}'
        for i, v in enumerate(violations)
    )

    prompt = f"""You are a seasoned public health inspector with 20 years of field experience reviewing restaurant inspections.

Inspection type: {inspection.get('type', 'Routine')}
Date: {inspection.get('date', 'Unknown')}

Violations found ({len(violations)}):
{chr(10).join(viol_lines)}

Tasks:
1. For each violation (by its code), assign a severity and write a one-sentence reasoning:
   - Critical: Immediate risk of foodborne illness (temperature abuse, contamination, vermin, adulterated food)
   - High: Likely risk if not corrected quickly (improper cooling/holding, no HACCP plan for ROP, bare-hand contact)
   - Medium: Risk if pattern continues (missing date labels, inadequate documentation, equipment issues)
   - Low: Minor or procedural (missing test strips, signage gaps, minor cleanliness, non-critical equipment)

2. Write a 2-3 sentence overall summary of this inspection from a health inspector's perspective. Be direct and specific — mention what was done well or poorly, and whether the establishment appears to take food safety seriously.

Respond with JSON only, no text outside the JSON. Include one entry per violation using the exact code shown above:
{{
  "violations": [
{example_violations}  ],
  "summary": "Overall inspection summary here."
}}"""

    response = _get_client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text
    try:
        # Extract JSON even if Claude wraps it in a markdown code block
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError(f"No JSON object found in response: {raw[:200]}")
        result = json.loads(raw[start:end])

        class_by_code = {item["code"]: item for item in result.get("violations", []) if "code" in item}
        for v in violations:
            item = class_by_code.get(v.get("code", ""))
            if item:
                sev = item.get("severity", "Low")
                if sev not in SEVERITY_ORDER:
                    sev = "Low"
                v["classification"] = {
                    "severity": sev,
                    "reasoning": item.get("reasoning", ""),
                }

        inspection["summary"] = result.get("summary", "")

    except Exception as e:
        print(f"  WARNING: classification parse failed — {e}")
        print(f"  Raw response: {raw[:300]}")
        inspection["summary"] = ""

    return inspection


def classify_inspections(new_inspections: list[dict]) -> list[dict]:
    """Classify all new inspections. One Claude call per inspection."""
    total = len(new_inspections)
    print(f"Classify: classifying {total} inspection(s)...")

    for i, inspection in enumerate(new_inspections, 1):
        vcount = len(inspection.get("violations", []))
        print(f"  [{i}/{total}] {inspection.get('type', '?')} {inspection.get('date', '')} — {vcount} violation(s)")
        classify_inspection(inspection)

    return new_inspections


def derive_worst_severity(inspections: list[dict]) -> str:
    """
    Returns worst severity across all violations in the most recent
    routine inspection only. Violations must have a 'classification' dict.
    """
    routine = [i for i in inspections if "routine" in i.get("type", "").lower()]
    if not routine:
        return "None"
    latest = max(routine, key=lambda x: x.get("date", ""))

    worst_idx = len(SEVERITY_ORDER)
    for v in latest.get("violations", []):
        sev = v.get("classification", {}).get("severity", "")
        if sev in SEVERITY_ORDER:
            idx = SEVERITY_ORDER.index(sev)
            if idx < worst_idx:
                worst_idx = idx

    return SEVERITY_ORDER[worst_idx] if worst_idx < len(SEVERITY_ORDER) else "None"
