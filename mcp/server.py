"""
Montana Food Code MCP Server
Exposes tools for classifying health inspection violations against the FDA Food Code
and searching regulation PDFs stored in a Google Cloud Storage bucket.

Run:
    python mcp/server.py

Or register in .claude/settings.json under mcpServers (see project README).
"""

from mcp.server.fastmcp import FastMCP
import gcs_client
import pdf_parser
from food_code_data import lookup_section, RISK_LEVEL_DESCRIPTIONS

mcp = FastMCP("Montana Food Code Regulations")

# In-memory cache: bucket_name → {pdf_name → page_index}
_pdf_cache: dict[str, dict] = {}
_loaded = False


def _load_pdfs() -> dict:
    """Fetch and parse all PDFs from GCS (once per session)."""
    global _pdf_cache, _loaded
    if _loaded:
        return _pdf_cache

    _loaded = True
    bucket = gcs_client.get_bucket_name()
    if not bucket:
        return {}

    try:
        pdf_names = gcs_client.list_pdfs()
    except Exception as e:
        return {}

    for name in pdf_names:
        try:
            raw = gcs_client.download_pdf(name)
            pages = pdf_parser.parse_pdf(raw)
            _pdf_cache[name] = pdf_parser.build_index(pages)
        except Exception:
            pass

    return _pdf_cache


# ── Tools ──────────────────────────────────────────────────────────────────

@mcp.tool()
def list_available_regulations() -> str:
    """List regulation PDFs currently stored in the GCS bucket."""
    bucket = gcs_client.get_bucket_name()
    if not bucket:
        return (
            "REGULATIONS_BUCKET environment variable is not set.\n"
            "Set it to your GCS bucket name to enable PDF lookups.\n"
            "Example: REGULATIONS_BUCKET=my-mt-regulations-bucket"
        )

    try:
        pdfs = gcs_client.list_pdfs()
    except Exception as e:
        return f"Could not connect to GCS bucket '{bucket}': {e}"

    if not pdfs:
        return (
            f"Bucket '{bucket}' is reachable but contains no PDF files yet.\n"
            "Upload Montana DPHHS / FDA Food Code regulation PDFs to that bucket.\n"
            "The classify_violation tool still works without PDFs using the built-in classification table."
        )

    lines = [f"Bucket: {bucket}", f"PDFs available ({len(pdfs)}):"]
    lines.extend(f"  • {p}" for p in pdfs)
    return "\n".join(lines)


@mcp.tool()
def classify_violation(code: str, description: str = "") -> str:
    """
    Classify a health inspection violation by risk level and category.

    Uses the built-in FDA Food Code table — works even without PDFs loaded.

    Args:
        code: Violation code, e.g. "3-501.16" or "3-501"
        description: Optional violation description for additional context
    """
    result = lookup_section(code)
    if not result:
        return (
            f"Could not classify code '{code}'. "
            "The code may not follow FDA Food Code numbering (X-XXX.XX format).\n"
            "If this is a Montana-specific code, upload the relevant regulation PDF and use search_regulations."
        )

    risk = result["risk_level"]
    risk_desc = RISK_LEVEL_DESCRIPTIONS.get(risk, risk)

    lines = [
        f"Code: {code}",
        f"Section: {result.get('matched_prefix', code)}",
        f"Category: {result['category']}",
        f"Chapter: {result['chapter']}",
        f"",
        f"Risk Level: {risk}",
        f"{risk_desc}",
        f"",
        f"Rule Summary: {result['description']}",
    ]

    if description:
        lines.append(f"\nViolation Description Provided: {description}")

    return "\n".join(lines)


@mcp.tool()
def lookup_violation_code(code: str) -> str:
    """
    Look up a specific violation code in the regulation PDFs, with built-in table fallback.

    Searches GCS-hosted PDFs for the exact code text, then falls back to
    the built-in FDA Food Code classification table if no PDF match is found.

    Args:
        code: Violation code, e.g. "3-501.16"
    """
    cache = _load_pdfs()

    pdf_results = []
    for pdf_name, index in cache.items():
        matches = pdf_parser.find_section(index, code)
        for m in matches:
            pdf_results.append((pdf_name, m["page"], m["excerpt"]))

    if pdf_results:
        lines = [f"Found '{code}' in regulation PDFs:\n"]
        for pdf_name, page, excerpt in pdf_results[:3]:
            lines.append(f"📄 {pdf_name} (page {page}):")
            lines.append(f"  …{excerpt}…")
            lines.append("")
        return "\n".join(lines)

    # Fall back to built-in table
    builtin = classify_violation(code)
    if not cache:
        note = "\n[No regulation PDFs loaded yet — result is from built-in FDA Food Code table.]"
    else:
        note = f"\n[Code not found in {len(cache)} loaded PDF(s) — result is from built-in FDA Food Code table.]"

    return builtin + note


@mcp.tool()
def search_regulations(query: str) -> str:
    """
    Full-text search across all regulation PDFs in the GCS bucket.

    Returns up to 5 matching page excerpts. Requires PDFs to be present in the bucket.

    Args:
        query: Search term, e.g. "temperature control" or "handwashing"
    """
    cache = _load_pdfs()

    if not cache:
        bucket = gcs_client.get_bucket_name()
        if not bucket:
            return (
                "REGULATIONS_BUCKET is not configured. "
                "Set the environment variable and add PDFs to the bucket to enable full-text search."
            )
        return (
            f"No PDFs are loaded from bucket '{bucket}'.\n"
            "Upload regulation PDFs to the bucket, then restart the server to index them.\n"
            "Use classify_violation for code-based lookups in the meantime."
        )

    all_results = []
    for pdf_name, index in cache.items():
        matches = pdf_parser.search_text(index, query, max_results=5)
        for m in matches:
            all_results.append((pdf_name, m["page"], m["excerpt"]))

    if not all_results:
        return f"No matches found for '{query}' across {len(cache)} loaded PDF(s)."

    lines = [f"Search results for '{query}' ({len(all_results)} match(es)):\n"]
    for pdf_name, page, excerpt in all_results[:5]:
        lines.append(f"📄 {pdf_name} — page {page}:")
        lines.append(f"  …{excerpt}…")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
