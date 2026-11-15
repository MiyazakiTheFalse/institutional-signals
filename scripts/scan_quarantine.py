"""Operator-run ClamAV scanning. A clean scan is not evidence verification."""
import argparse
import gzip
import hashlib
import io
import json
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from collect import R2Store

def unpack_checked(packed, expected_hash, limit=10485760):
    with gzip.GzipFile(fileobj=io.BytesIO(packed)) as stream:
        body = stream.read(limit + 1)
    if not body or len(body) > limit: raise ValueError('Decompressed size limit exceeded')
    if hashlib.sha256(body).hexdigest() != expected_hash: raise ValueError('Evidence integrity mismatch')
    return body

def scan(body, executable='clamscan'):
    version = subprocess.run([executable, '--version'], capture_output=True, text=True, timeout=15, check=True).stdout.strip()
    # Require a dated, recently updated signature database; no silent scanner fallback.
    database_date = datetime.strptime(version.rsplit('/', 1)[1], '%a %b %d %H:%M:%S %Y').replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - database_date).total_seconds()
    if not 0 <= age <= 3 * 86400: raise ValueError('Antivirus signatures are stale or future dated')
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder) / 'untrusted-evidence.bin'
        target.write_bytes(body)
        result = subprocess.run([executable, '--no-summary', '--alert-exceeds-max=yes', str(target)], capture_output=True, timeout=120)
    if result.returncode not in (0, 1): raise RuntimeError('Antivirus scan failed')
    return {'scan_state': 'clean' if result.returncode == 0 else 'infected_or_limit_exceeded', 'scanner': version,
            'scanned_at': datetime.now(timezone.utc).isoformat(), 'sha256': hashlib.sha256(body).hexdigest()}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--owner', required=True); parser.add_argument('--submission', required=True)
    args=parser.parse_args()
    if not re.fullmatch('[a-zA-Z0-9_-]{1,64}', args.owner) or not re.fullmatch('[0-9a-f-]{36}', args.submission): raise ValueError('Invalid submission identity')
    store=R2Store(); prefix=f'{args.owner}/{args.submission}'
    record=json.loads(store.get('submissions/'+prefix+'/manifest.json'))
    if not re.fullmatch('[0-9a-f]{64}', record['sha256']): raise ValueError('Invalid hash')
    key=f"quarantine/{prefix}/{record['sha256']}.gz"
    body=unpack_checked(store.get(key), record['sha256'])
    report={**scan(body), 'owner':args.owner, 'submission_id':args.submission, 'evidence_verified':False}
    # Immutable scan results retain engine/database identity on rescans.
    stamp=hashlib.sha256(json.dumps(report,sort_keys=True).encode()).hexdigest()
    store.put(f'scans/{prefix}/{stamp}.json.gz', gzip.compress(json.dumps(report).encode(),mtime=0), immutable=True)
    print(json.dumps({'submission':args.submission,'scan_state':report['scan_state'],'evidence_verified':False}))

if __name__ == '__main__': main()
