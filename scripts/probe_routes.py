"""Single-attempt, allowlisted route diagnostics. No proxying, evasion or credential spoofing.

Each probe uses the same format and access-policy validation as the production
collector. Results are observations of HTTP retrieval, NEVER evidence approval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError

from collect import ROOT, SourceTransport, failure_code, load_sources

TARGETS = (
    'PARL-2026-09', 'PARL-2026-10', 'PARL-2026-11',
    'OFWAT-2026', 'PARL-REPORT-API', 'PARL-REPORT-PDF-API',
    'PARL-REPORT-PDF-FORMAT',
    'PARL-PUBLICATIONS-API', 'PARL-EFRA-PUBLICATIONS',
    'OFWAT-REPORT-PUBLICATION', 'OFWAT-DATA-PUBLICATION',
    'OFWAT-DATA-DICTIONARY', 'GOV-JOINT-PDF',
)


def document_descriptor_hints(payload):
    """Return only public structural fields needed to construct an official document route."""
    hints = []
    allow = {'id', 'documentid', 'documentpurpose', 'filedataformat', 'format',
             'filename', 'name', 'url', 'downloadurl', 'purpose', 'type'}
    def visit(value, path='', depth=0):
        if depth > 7 or len(hints) >= 30:
            return
        if isinstance(value, dict):
            for key, item in value.items():
                if key.lower() in allow and isinstance(item, (str, int)):
                    hints.append({'path': path + '/' + key, 'value': str(item)[:180]})
                if isinstance(item, (dict, list)):
                    visit(item, path + '/' + key, depth + 1)
        elif isinstance(value, list):
            for index, item in enumerate(value[:4]):
                visit(item, path + '/' + str(index), depth + 1)
    visit(payload)
    return hints[:30]


def probe(sources, transport):
    """One GET per route, with no repeated attempts after 403 or 429."""
    indexed = {s['source_id']: s for s in sources}
    for sid in TARGETS:
        if sid not in indexed:
            raise ValueError('Missing required probe route: ' + sid)
    results = []
    for sid in TARGETS:
        source = indexed[sid]
        row = {
            'source_id': sid,
            'url': source['url'],
            'coverage_scope': source.get('coverage_scope', 'original_document'),
            'is_supplemental': not source.get('required_for_health', True),
            'verified_evidence': False,
        }
        try:
            status, _, body = transport(source['url'], {})
            row.update(result='retrieved_unreviewed' if status == 200 else 'not_modified',
                       http_status=status, response_bytes=len(body))
            if status == 200:
                row['sha256'] = hashlib.sha256(body).hexdigest()
            if sid == 'PARL-REPORT-API' and status == 200:
                row['document_descriptors'] = document_descriptor_hints(json.loads(body))
        except (OSError, ValueError) as exc:
            row.update(result='unavailable', failure_code=failure_code(exc))
            if sid in ('PARL-REPORT-PDF-API', 'PARL-REPORT-PDF-FORMAT') and isinstance(exc, ValueError):
                detail = str(exc)
                if detail.startswith('Parliament document response is not a PDF (mime='):
                    row['format_diagnostic'] = detail[:160]
            if isinstance(exc, HTTPError):
                row['http_status'] = exc.code
                exc.close()
        results.append(row)
    return results


def main():
    sources = load_sources(ROOT / 'config/collection.json')
    for entry in probe(sources, SourceTransport(sources)):
        print(json.dumps(entry, sort_keys=True), flush=True)


if __name__ == '__main__':
    main()
