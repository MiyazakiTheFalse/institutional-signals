"""Bounded probe contract: no retries, no source substitution, no fake verification."""
import sys
import unittest
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from collect import load_sources
from probe_routes import probe, TARGETS


class RouteProbeTests(unittest.TestCase):
    def test_reports_origins_and_supplements_separately(self):
        sources = load_sources(ROOT / 'config/collection.json')
        urls = {s['url']: s['source_id'] for s in sources}
        calls = {}
        def fake(url, headers):
            sid = urls[url]
            calls[sid] = calls.get(sid, 0) + 1
            if sid == 'OFWAT-2026':
                raise HTTPError(url, 403, 'not allowed', {}, None)
            return 200, {'Content-Type': 'application/pdf'}, b'%PDF-1.7'
        result = probe(sources, fake)
        self.assertEqual({r['source_id'] for r in result}, set(TARGETS))
        self.assertTrue(all(count == 1 for count in calls.values()))
        original = next(x for x in result if x['source_id'] == 'OFWAT-2026')
        alternative = next(x for x in result if x['source_id'] == 'OFWAT-DATA-PUBLICATION')
        self.assertEqual(original['failure_code'], 'http_403')
        self.assertEqual(original['http_status'], 403)
        self.assertEqual(alternative['result'], 'retrieved_unreviewed')
        self.assertTrue(alternative['is_supplemental'])
        self.assertFalse(alternative['verified_evidence'])
        self.assertFalse(original['verified_evidence'])
        self.assertNotIn('failure_code', alternative)

    def test_missing_required_route_fails_loudly(self):
        with self.assertRaisesRegex(ValueError, 'Missing required probe'):
            probe([], lambda u, h: (200, {}, b''))


if __name__ == '__main__':
    unittest.main()
