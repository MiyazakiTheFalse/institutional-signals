"""Append-only verified evidence journal and strict historical as-of replay.

Collector content changes are not verified events. The local filesystem adapter
refuses overwrites; production must use equally durable conditional writes.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from knowledge_graph import utc

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')

def event_from_review(review, *, event_type, institution_ids, structured_claims=None,
                      supersedes=None, parser_version='human-review-v1'):
    required = ('id', 'source_id', 'sha256', 'available_at', 'reviewed_at',
                'primary_document_id', 'review_state')
    if any(not review.get(k) for k in required):
        raise ValueError('Incomplete reviewed evidence')
    if review['review_state'] != 'verified':
        raise ValueError('Unreviewed collector output cannot be promoted')
    if not re.fullmatch(r'[0-9a-f]{64}', review['sha256']):
        raise ValueError('Expected SHA-256 content digest')
    if not institution_ids or not event_type:
        raise ValueError('Institution and event type required')
    available, verified = utc(review['available_at']), utc(review['reviewed_at'])
    published = utc(review['published_at']) if review.get('published_at') else None
    if published and published > available:
        raise ValueError('Publication cannot postdate first availability')
    if verified < available:
        raise ValueError('Cannot verify before first availability')
    event = {
        'source_id': review['source_id'],
        'canonical_document_id': review['primary_document_id'],
        'content_hash_sha256': review['sha256'],
        'published_at': review.get('published_at'),
        'source_updated_at': review.get('source_updated_at'),
        'observed_at': review['available_at'],
        'fetched_at': review.get('fetched_at', review['available_at']),
        'verified_at': review['reviewed_at'],
        'available_at': review['available_at'],
        'event_type': event_type,
        'institution_ids': sorted(set(institution_ids)),
        'structured_claims': structured_claims or {},
        'quality': 'human_verified',
        'duplicate_group': review['primary_document_id'],
        'raw_blob_ref': review.get('raw_blob_ref') or review.get('scan_key') or review['sha256'],
        'parser_version': parser_version,
        'human_review_state': 'verified',
        'source_review_id': review['id'],
        'supersedes': supersedes,
    }
    for field in ('observed_at', 'fetched_at', 'verified_at', 'available_at',
                  'source_updated_at', 'published_at'):
        if event[field] is not None:
            utc(event[field])
    event['event_id'] = hashlib.sha256(canonical(event)).hexdigest()
    return event

def append_event(directory, event):
    content = {k: v for k, v in event.items() if k != 'event_id'}
    if event.get('event_id') != hashlib.sha256(canonical(content)).hexdigest():
        raise ValueError('Tampered event ID')
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    target = root / (event['event_id'] + '.json')
    with target.open('xb') as output:
        output.write(canonical(event))
    return target

def replay(events, as_of):
    """Only evidence available AND verified by as_of; one underlying document."""
    cutoff = utc(as_of)
    known = {}
    for item in events:
        if item.get('human_review_state') != 'verified':
            continue
        if utc(item['available_at']) > cutoff or utc(item['verified_at']) > cutoff:
            continue
        eid = item['event_id']
        if eid in known and known[eid] != item:
            raise ValueError('Conflicting same-ID journal entries')
        known[eid] = item
    effective = {}
    for item in sorted(known.values(), key=lambda e: (utc(e['verified_at']), e['event_id'])):
        predecessor = item.get('supersedes')
        if predecessor:
            if predecessor not in known:
                continue
            if known[predecessor]['canonical_document_id'] != item['canonical_document_id']:
                raise ValueError('Cross-document correction')
        effective[item['duplicate_group']] = item
    return sorted(effective.values(), key=lambda e: e['event_id'])

def read_journal(directory):
    return [json.loads(p.read_text()) for p in sorted(Path(directory).glob('*.json'))]
