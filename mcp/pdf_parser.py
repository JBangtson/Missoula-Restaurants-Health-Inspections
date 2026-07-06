"""
PDF text extraction and in-memory search index.
Uses pdfplumber for better text extraction from regulatory PDFs.
"""

import io
import re


def parse_pdf(pdf_bytes: bytes) -> list[dict]:
    """Extract text from a PDF. Returns a list of {page, text} dicts."""
    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError(
            "pdfplumber is not installed. Run: pip install -r mcp/requirements.txt"
        )

    pages = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({"page": i, "text": text})
    return pages


def build_index(parsed_pages: list[dict]) -> dict:
    """Build a simple page-number → text index."""
    return {p["page"]: p["text"] for p in parsed_pages}


def search_text(index: dict, query: str, max_results: int = 5) -> list[dict]:
    """
    Search all pages for query (case-insensitive substring).
    Returns up to max_results matches as {page, excerpt} dicts.
    """
    query_lower = query.lower()
    results = []
    for page_num, text in index.items():
        if query_lower in text.lower():
            # Extract a ~400-char window around the first match
            pos = text.lower().find(query_lower)
            start = max(0, pos - 150)
            end = min(len(text), pos + 250)
            excerpt = text[start:end].strip()
            # Clean up excessive whitespace
            excerpt = re.sub(r"\s+", " ", excerpt)
            results.append({"page": page_num, "excerpt": excerpt})
            if len(results) >= max_results:
                break
    return results


def find_section(index: dict, code: str) -> list[dict]:
    """
    Search for a specific violation code string (e.g. '3-501.16') in page text.
    Returns matching page excerpts.
    """
    # Try exact code first, then the section prefix without the item number
    targets = [code]
    if "." in code:
        targets.append(code.split(".")[0])  # e.g. "3-501" from "3-501.16"

    for target in targets:
        results = search_text(index, target, max_results=3)
        if results:
            return results
    return []
