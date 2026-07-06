"""
Google Cloud Storage client for fetching regulation PDFs.
Reads REGULATIONS_BUCKET env var for the bucket name.
Auth: set GOOGLE_APPLICATION_CREDENTIALS to a service account JSON path,
      or run 'gcloud auth application-default login' for local dev.
"""

import os


def _get_storage_client():
    try:
        from google.cloud import storage
        return storage.Client()
    except ImportError:
        raise RuntimeError(
            "google-cloud-storage is not installed. "
            "Run: pip install -r mcp/requirements.txt"
        )


def get_bucket_name() -> str | None:
    return os.environ.get("REGULATIONS_BUCKET")


def list_pdfs() -> list[str]:
    """Return blob names of all PDFs in the configured bucket."""
    bucket_name = get_bucket_name()
    if not bucket_name:
        return []
    client = _get_storage_client()
    bucket = client.bucket(bucket_name)
    blobs = bucket.list_blobs()
    return [b.name for b in blobs if b.name.lower().endswith(".pdf")]


def download_pdf(blob_name: str) -> bytes:
    """Download a single PDF blob and return its raw bytes."""
    bucket_name = get_bucket_name()
    if not bucket_name:
        raise ValueError("REGULATIONS_BUCKET environment variable is not set.")
    client = _get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    return blob.download_as_bytes()
