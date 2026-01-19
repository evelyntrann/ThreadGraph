# hashing.py
import hashlib
import json

def compute_content_hash(payload: dict) -> bytes:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).digest()
