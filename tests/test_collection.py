import gzip
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from collect import collect, LocalStore, packed, PoliteFetch, SourceTransport


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = LocalStore(self.temp.name)
        self.now = datetime(2026, 11, 15, 12, tzinfo=timezone.utc)
        self.sources = [{'source_id': 'official', 'url': 'https://example.org/news', 'poll_target_minutes': 30}]

    def run_collect(self, transport, minutes=0):
        return collect(self.sources, self.store, transport, self.now + timedelta(minutes=minutes))

    def initial(self):
        return self.run_collect(lambda u, h: (200, {'ETag': 'v1'}, b'evidence' * 100))

    def test_compressed_snapshot_roundtrip_and_content_address(self):
        result = self.initial()
        event = result['events'][0]
        self.assertEqual(gzip.decompress(self.store.get(event['raw_key'])), b'evidence' * 100)
        self.assertLess(event['compressed_bytes'], event['original_bytes'])
        self.assertTrue(result['coverage']['safe_to_claim_current'])
        self.assertEqual(event['review_state'], 'unreviewed_content_change')

    def test_no_change_304_records_success_without_new_event(self):
        self.initial()
        def not_modified(url, headers):
            self.assertEqual(headers['If-None-Match'], 'v1')
            return 304, {}, b''
        result = self.run_collect(not_modified, 30)
        self.assertEqual(result['events'], [])
        self.assertEqual(result['health']['official']['status'], 'current')

    def test_identical_200_deduplicates(self):
        self.initial()
        result = self.run_collect(lambda u, h: (200, {}, b'evidence' * 100), 30)
        self.assertEqual(result['events'], [])

    def test_correction_keeps_original(self):
        first = self.initial()['events'][0]
        second = self.run_collect(lambda u, h: (200, {}, b'correction'), 30)['events'][0]
        self.assertEqual(second['previous_sha256'], first['sha256'])
        self.assertIsNotNone(self.store.get(first['raw_key']))
        self.assertNotEqual(first['raw_key'], second['raw_key'])

    def test_outage_is_not_no_event(self):
        self.initial()
        def offline(u, h):
            raise OSError('offline')
        report = self.run_collect(offline, 30)
        self.assertFalse(report['coverage']['safe_to_claim_current'])
        self.assertEqual(report['sources']['official']['consecutive_failures'], 1)
        self.assertEqual(report['sources']['official']['last_success_at'], '2026-11-15T12:00:00Z')

    def test_304_without_previous_snapshot_rejected(self):
        report = self.run_collect(lambda u, h: (304, {}, b''))
        self.assertFalse(report['coverage']['safe_to_claim_current'])

    def test_poll_target_skips_network(self):
        self.initial()
        def unexpected(u, h):
            self.fail('Polled before target')
        self.assertEqual(self.run_collect(unexpected, 10)['events'], [])

    def test_storage_failure_prevents_checkpoint_advance(self):
        original = self.store.put
        def broken(key, body, immutable=False):
            if key.startswith('runs/'):
                raise OSError('upload failed')
            original(key, body, immutable)
        self.store.put = broken
        with self.assertRaises(OSError):
            self.initial()
        self.assertIsNone(self.store.get('state/latest.json.gz'))

    def test_retry_after_respected(self):
        def limited(u, h):
            raise HTTPError(u, 429, 'limited', {'Retry-After': '7200'}, None)
        result = self.run_collect(limited)
        next_check = datetime.fromisoformat(result['sources']['official']['next_attempt_at'])
        self.assertEqual(next_check, self.now + timedelta(hours=2))

    def test_compression_is_deterministic(self):
        self.assertEqual(packed({'a': 1}), packed({'a': 1}))

    def test_robots_unavailable_does_not_mean_document_denied(self):
        with patch('collect.fetch', side_effect=[HTTPError('https://example.org/robots.txt', 403, 'unavailable', {}, None),
                                                 (200, {}, b'document')]) as get:
            self.assertEqual(PoliteFetch()('https://example.org/news', {})[0], 200)
            self.assertEqual(get.call_count, 2)

    def test_actual_document_403_is_preserved(self):
        with patch('collect.fetch', side_effect=[(200, {}, b'User-agent: *\nAllow: /'),
                                                 HTTPError('https://example.org/news', 403, 'denied', {}, None)]):
            with self.assertRaises(HTTPError):
                PoliteFetch()('https://example.org/news', {})

    def test_robots_server_failure_or_rate_limit_stops_fetch(self):
        for status in (429, 500, 503):
            with self.subTest(status=status), patch('collect.fetch', side_effect=HTTPError('https://example.org/robots.txt', status, 'retry later', {}, None)) as get:
                with self.assertRaises(HTTPError):
                    PoliteFetch()('https://example.org/news', {})
                self.assertEqual(get.call_count, 1)

    def test_robots_disallow_still_stops_document_fetch(self):
        with patch('collect.fetch', return_value=(200, {}, b'User-agent: *\nDisallow: /')) as get:
            with self.assertRaisesRegex(ValueError, 'disallows'):
                PoliteFetch()('https://example.org/news', {})
            self.assertEqual(get.call_count, 1)

    def test_unreviewed_change_index_survives_noop_and_failures(self):
        first = self.initial()['recent_changes']
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0]['review_state'], 'unreviewed_content_change')
        self.assertNotIn('raw_key', first[0])
        later = self.run_collect(lambda u, h: (304, {}, b''), 30)
        self.assertEqual(later['recent_changes'], first)

        def denied(u, h):
            raise HTTPError(u, 403, 'blocked', {}, None)
        blocked = self.run_collect(denied, 60)
        self.assertEqual(blocked['sources']['official']['last_error_code'], 'http_403')
        self.assertEqual(blocked['recent_changes'], first)
        self.assertFalse(blocked['coverage']['safe_to_claim_current'])

    def test_corrections_are_review_candidates_not_automatic_facts(self):
        initial = self.initial()['recent_changes']
        later = self.run_collect(lambda u, h: (200, {}, b'new document'), 30)
        self.assertEqual(len(later['recent_changes']), 2)
        self.assertEqual(later['recent_changes'][0]['previous_sha256'], initial[0]['sha256'])
        self.assertEqual(later['recent_changes'][1], initial[0])
        self.assertTrue(all(e['review_state'] == 'unreviewed_content_change' for e in later['recent_changes']))
        unchanged = self.run_collect(lambda u, h: (304, {}, b''), 60)
        self.assertEqual(unchanged['recent_changes'], later['recent_changes'])

    def test_failure_codes_are_safe_and_clear_after_success(self):
        self.assertEqual(self.run_collect(lambda u, h: (304, {}, b''))['sources']['official']['last_error_code'], 'validation_error')
        healthy = self.run_collect(lambda u, h: (200, {}, b'document'), 30)
        self.assertIsNone(healthy['sources']['official']['last_error_code'])

    def test_documented_parliament_api_has_schema_validation(self):
        url = 'https://committees-api.parliament.uk/api/Publications/55076'
        transport = SourceTransport([{'url': url, 'adapter': 'parliament_api', 'expected_publication_id': 55076}])
        with patch('collect.fetch', return_value=(200, {}, b'{"id":55076}')) as get:
            self.assertEqual(transport(url, {})[0], 200)
            self.assertEqual(get.call_count, 1)
        with patch('collect.fetch', return_value=(200, {}, b'{"id":123}')):
            with self.assertRaisesRegex(ValueError, 'Wrong publication'):
                transport(url, {})

    def test_api_route_does_not_allow_arbitrary_hosts(self):
        url = 'https://example.org/api/Publications/55076'
        transport = SourceTransport([{'url': url, 'adapter': 'parliament_api'}])
        with patch('collect.fetch') as get:
            with self.assertRaises(ValueError):
                transport(url, {})
            get.assert_not_called()

    def test_supplemental_route_does_not_clear_original_outage(self):
        sources = self.sources + [{'source_id': 'supplement', 'url': 'https://example.org/api',
                                  'poll_target_minutes': 60, 'coverage_scope': 'metadata_only',
                                  'supports_sources': ['official']}]
        def get(url, headers):
            if url.endswith('/news'):
                raise OSError('original unavailable')
            return 200, {}, b'metadata'
        result = collect(sources, self.store, get, self.now)
        self.assertFalse(result['coverage']['safe_to_claim_current'])
        self.assertEqual(result['health']['official']['status'], 'unavailable')
        self.assertEqual(result['events'][0]['coverage_scope'], 'metadata_only')


if __name__ == '__main__':
    unittest.main()
