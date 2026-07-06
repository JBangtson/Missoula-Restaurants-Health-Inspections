import json
import os

from google.cloud import storage as gcs


class Storage:
    def __init__(self):
        self.client = gcs.Client()
        self.bucket = self.client.bucket(os.environ["GCS_BUCKET_NAME"])

    def read_json(self, path: str):
        blob = self.bucket.blob(path)
        if not blob.exists():
            return None
        return json.loads(blob.download_as_text())

    def write_json(self, path: str, data):
        blob = self.bucket.blob(path)
        blob.upload_from_string(
            json.dumps(data, indent=2, ensure_ascii=False),
            content_type="application/json",
        )
