"""Operator-only quarantine intake; no public upload endpoint is exposed."""
import argparse
import gzip
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from collect import LocalStore, R2Store, packed
from input_security import validate_upload, source_url, clean_text, MAX_UPLOAD


def intake(path, request_id, url, published_at, store, cases):
    from coverage import utc
    from upload_requests import requests_for
    # Resolve the request against server-owned case configuration, never client-supplied capabilities.
    requirements = {c['case_id'] + ':' + r['id']: r for c in cases for r in c['requirements']}
    requirement = requirements.get(request_id)
    if requirement is None:
        raise ValueError('Unknown upload request')
    published = utc(published_at)
    now = datetime.now(timezone.utc)
    if published > now:
        raise ValueError('Publication date cannot be in the future')
    path = Path(path)
    with path.open('rb') as stream:
        body = stream.read(MAX_UPLOAD + 1)
    record = validate_upload(path.name, body)
    if 'dataset' not in requirement['capability'] and record['extension'] != 'pdf':
        raise ValueError('This request requires a PDF')
    record.update(upload_id=uuid.uuid4().hex, request_id=request_id,
                  original_filename=clean_text(path.name, 150), source_url=source_url(url),
                  published_at=published.isoformat(), received_at=now.isoformat(),
                  requested_capability=requirement['capability'])
    key = f"quarantine/{record['upload_id']}/{record['sha256']}.{record['extension']}.gz"
    record['raw_key'] = key
    store.put(key, gzip.compress(body, mtime=0), immutable=True)
    store.put(f"quarantine/{record['upload_id']}/manifest.json.gz", packed(record), immutable=True)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('--request-id', required=True)
    parser.add_argument('--source-url', required=True)
    parser.add_argument('--published-at', required=True, help='Timezone-aware ISO timestamp')
    parser.add_argument('--store', choices=['local', 'r2'], default='local')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    cases = json.loads((root / 'config/case_dependencies.json').read_text())
    store = R2Store() if args.store == 'r2' else LocalStore(root / '.collection')
    result = intake(args.path, args.request_id, args.source_url, args.published_at, store, cases)
    print(json.dumps({'upload_id': result['upload_id'], 'review_state': result['review_state'], 'scan_state': result['scan_state']}))
