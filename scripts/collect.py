"""Conditional public-source collection with gzip snapshots and R2 persistence.

Content changes are review candidates, never verified institutional events.
Run only one writer per storage prefix (the Actions concurrency group enforces it).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from freshness import source_health, required_source_coverage

ROOT = Path(__file__).resolve().parents[1]
AGENT = 'InstitutionalSignals/0.2 (+https://github.com/MiyazakiTheFalse/institutional-signals)'
MAX_BYTES = 8 * 1024 * 1024


def packed(value):
    return gzip.compress(json.dumps(value, sort_keys=True, separators=(',', ':')).encode(), mtime=0)


class LocalStore:
    def __init__(self, root):
        self.root = Path(root)

    def get(self, key):
        path = self.root / key
        return path.read_bytes() if path.exists() else None

    def put(self, key, body, immutable=False):
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        if immutable:
            try:
                with path.open('xb') as stream:
                    stream.write(body)
            except FileExistsError:
                if path.read_bytes() != body:
                    raise ValueError('Immutable object collision')
        else:
            temp = path.with_name(path.name + '.tmp')
            temp.write_bytes(body)
            temp.replace(path)


class R2Store:
    def __init__(self):
        import boto3
        from botocore.config import Config
        account = os.environ['R2_ACCOUNT_ID']
        if not re.fullmatch(r'[a-fA-F0-9]{32}', account):
            raise ValueError('Invalid Cloudflare account ID')
        self.bucket = os.environ['R2_BUCKET']
        self.client = boto3.client(
            's3', endpoint_url=f'https://{account}.r2.cloudflarestorage.com',
            aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
            aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'], region_name='auto',
            config=Config(retries={'max_attempts': 3, 'mode': 'standard'},
                          connect_timeout=10, read_timeout=30,
                          request_checksum_calculation='when_required',
                          response_checksum_validation='when_required'))

    def get(self, key):
        from botocore.exceptions import ClientError
        try:
            response = self.client.get_object(Bucket=self.bucket, Key=key)
            with response['Body'] as stream:
                return stream.read()
        except ClientError as exc:
            if exc.response['Error']['Code'] in ('NoSuchKey', '404'):
                return None
            raise

    def put(self, key, body, immutable=False):
        from botocore.exceptions import ClientError
        options = {'IfNoneMatch': '*'} if immutable else {}
        try:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=body,
                                   ContentType='application/gzip', **options)
        except ClientError as exc:
            if not (immutable and exc.response['ResponseMetadata']['HTTPStatusCode'] == 412):
                raise
            if self.get(key) != body:
                raise ValueError('Immutable object collision') from exc


def fetch(url, headers):
    if urlsplit(url).scheme != 'https':
        raise ValueError('HTTPS required')
    try:
        with urlopen(Request(url, headers={'User-Agent': AGENT, 'Accept-Encoding': 'identity', **headers}), timeout=25) as response:
            if urlsplit(response.url).scheme != 'https':
                raise ValueError('Non-HTTPS redirect')
            body = response.read(MAX_BYTES + 1)
            if len(body) > MAX_BYTES:
                raise ValueError('Source exceeds 8 MiB collection limit')
            if response.headers.get('Content-Encoding', 'identity') != 'identity':
                raise ValueError('Unexpected transfer encoding; cannot archive canonical bytes')
            return response.status, dict(response.headers), body
    except HTTPError as exc:
        if exc.code == 304:
            return 304, dict(exc.headers), b''
        raise


class PoliteFetch:
    """RFC 9309 robots handling; rate limits and server outages fail closed.

    A 4xx on robots.txt means no policy is available, not a denied document.
    Any denial on the actual document is still propagated unchanged.
    """
    def __init__(self):
        self.robots = {}

    def __call__(self, url, headers):
        parts = urlsplit(url)
        origin = f'{parts.scheme}://{parts.netloc}'
        if origin not in self.robots:
            parser = RobotFileParser(origin + '/robots.txt')
            try:
                _, _, raw = fetch(origin + '/robots.txt', {})
                parser.parse(raw.decode('utf-8', errors='replace').splitlines())
            except HTTPError as exc:
                if not 400 <= exc.code < 500 or exc.code == 429:
                    raise
                exc.close()
                parser.parse([])
            self.robots[origin] = parser
        if not self.robots[origin].can_fetch(AGENT, url):
            raise ValueError('Source robots policy disallows collection')
        return fetch(url, headers)


class SourceTransport:
    """Use explicitly documented machine APIs, or robots-aware public document access."""
    def __init__(self, sources):
        self.sources = {s['url']: s for s in sources}
        self.polite = PoliteFetch()

    def __call__(self, url, headers):
        source = self.sources[url]
        if source.get('adapter') != 'parliament_api':
            return self.polite(url, headers)
        parsed = urlsplit(url)
        if parsed.netloc != 'committees-api.parliament.uk' or not re.fullmatch(
                r'/api/Publications(?:/[0-9]+(?:/Standard/OriginalFormat)?)?', parsed.path):
            raise ValueError('Not an allowlisted Parliament API operation')
        result = fetch(url, {'Accept': 'application/json', **headers})
        if result[0] == 200:
            payload = json.loads(result[2])
            if not isinstance(payload, dict):
                raise ValueError('Parliament API response must be an object')
            if source.get('expected_publication_id') is not None:
                if payload.get('id') != source['expected_publication_id']:
                    raise ValueError('Wrong publication returned by Parliament API')
            if source.get('response_kind') == 'publication_list':
                if not isinstance(payload.get('items'), list):
                    raise ValueError('Parliament publication list lacks items')
        return result


def collect(sources, store, transport, now=None):
    now = now or datetime.now(timezone.utc)
    if now.utcoffset() != timedelta(0):
        raise ValueError('UTC clock required')
    stamp = now.isoformat().replace('+00:00', 'Z')
    previous = store.get('state/latest.json.gz')
    state = json.loads(gzip.decompress(previous)) if previous else {}
    events = []
    for source in sources:
        sid = source['source_id']
        old = state.get(sid, {})
        if old.get('url') != source['url']:
            old = {}
        if old.get('next_attempt_at') and datetime.fromisoformat(old['next_attempt_at']) > now:
            continue
        entry = {**old, 'url': source['url'], 'last_attempt_at': stamp,
                 'coverage_scope': source.get('coverage_scope', 'original_document'),
                 'supports_sources': source.get('supports_sources', [])}
        try:
            conditional = {}
            if old.get('etag'):
                conditional['If-None-Match'] = old['etag']
            if old.get('last_modified'):
                conditional['If-Modified-Since'] = old['last_modified']
            status, headers, body = transport(source['url'], conditional)
            headers = {k.lower(): v for k, v in headers.items()}
            if status == 304:
                if not old.get('raw_key') or store.get(old['raw_key']) is None:
                    raise ValueError('304 without a durable previous snapshot')
            elif status == 200:
                digest = hashlib.sha256(body).hexdigest()
                raw_key = f'raw/sha256/{digest[:2]}/{digest}.gz'
                compressed = gzip.compress(body, compresslevel=6, mtime=0)
                if digest != old.get('sha256'):
                    store.put(raw_key, compressed, immutable=True)
                    events.append({'source_id': sid, 'observed_at': stamp, 'url': source['url'],
                                   'sha256': digest, 'raw_key': raw_key,
                                   'previous_sha256': old.get('sha256'),
                                   'original_bytes': len(body), 'compressed_bytes': len(compressed),
                                   'content_type': headers.get('content-type'),
                                   'coverage_scope': entry['coverage_scope'],
                                   'supports_sources': entry['supports_sources'],
                                   'review_state': 'unreviewed_content_change'})
                entry.update(sha256=digest, raw_key=raw_key,
                             etag=headers.get('etag'), last_modified=headers.get('last-modified'))
            else:
                raise ValueError(f'Unexpected HTTP status {status}')
            entry.update(last_success_at=stamp, consecutive_failures=0, last_error=None,
                         next_attempt_at=(now + timedelta(minutes=source['poll_target_minutes'])).isoformat())
        except (OSError, ValueError) as exc:
            failures = old.get('consecutive_failures', 0) + 1
            delay = min(1440, source['poll_target_minutes'] * 2 ** min(failures - 1, 5))
            if isinstance(exc, HTTPError) and exc.code == 429:
                from email.utils import parsedate_to_datetime
                retry = exc.headers.get('Retry-After', '')
                try:
                    delay = max(delay, int(retry) / 60)
                except ValueError:
                    try:
                        delay = max(delay, (parsedate_to_datetime(retry) - now).total_seconds() / 60)
                    except (ValueError, TypeError):
                        pass
            entry.update(consecutive_failures=failures,
                         last_error=f'{type(exc).__name__}: {exc}',
                         next_attempt_at=(now + timedelta(minutes=delay)).isoformat())
        state[sid] = entry
    health = {}
    for source in sources:
        entry = state.get(source['source_id'], {})
        health[source['source_id']] = source_health(
            checked_at=datetime.fromisoformat(entry['last_success_at']) if entry.get('last_success_at') else None,
            now=now, target_minutes=source['poll_target_minutes'],
            consecutive_failures=entry.get('consecutive_failures', 0))
    report = {'checked_at': stamp, 'events': events, 'sources': state, 'health': health,
              'coverage': required_source_coverage(h['status'] for h in health.values()),
              'notice': 'HTTP checks and unreviewed content changes; not verified events or forecasts.'}
    # Commit durable run before checkpoint. A failed upload leaves retryable content-addressed blobs.
    run_key = f'runs/{now:%Y/%m/%d}/{now:%H%M%S}-{uuid.uuid4().hex}.json.gz'
    store.put(run_key, packed(report), immutable=True)
    store.put('state/latest.json.gz', packed(state))
    store.put('status/latest.json.gz', packed(report))
    return report


def load_sources(path):
    sources = json.loads(Path(path).read_text(encoding='utf-8'))
    seen = set()
    for row in sources:
        sid = row['source_id']
        if sid in seen or not re.fullmatch(r'[A-Za-z0-9_-]+', sid):
            raise ValueError('Duplicate/invalid source ID')
        if not isinstance(row['poll_target_minutes'], int) or row['poll_target_minutes'] < 30:
            raise ValueError('Polling target must be at least 30 minutes')
        if urlsplit(row['url']).scheme != 'https' or not urlsplit(row['url']).hostname:
            raise ValueError('Invalid source URL')
        if row.get('adapter', 'public_document') not in ('public_document', 'parliament_api'):
            raise ValueError('Unknown source adapter')
        seen.add(sid)
    if not sources:
        raise ValueError('No sources configured')
    return sources


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--store', choices=['local', 'r2'], default='local')
    parser.add_argument('--config', default=str(ROOT / 'config/collection.json'))
    parser.add_argument('--local-dir', default=str(ROOT / '.collection'))
    args = parser.parse_args()
    store = R2Store() if args.store == 'r2' else LocalStore(args.local_dir)
    sources = load_sources(args.config)
    report = collect(sources, store, SourceTransport(sources))
    print(json.dumps({'checked_at': report['checked_at'], 'changed': len(report['events']),
                      'health': report['health'], 'coverage': report['coverage'],
                      'source_errors': {sid: row['last_error'] for sid, row in report['sources'].items()
                                        if row.get('last_error')}}, indent=2))
    return 0 if report['coverage']['safe_to_claim_current'] else 1


if __name__ == '__main__':
    sys.exit(main())
