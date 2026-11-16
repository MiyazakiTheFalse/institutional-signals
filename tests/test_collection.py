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
from collect import collect, LocalStore, packed, PoliteFetch, SourceTransport, load_sources


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

    def test_parliament_document_returns_only_verified_format_bytes(self):
        url = 'https://committees-api.parliament.uk/api/Publications/55076/Document/305807/OriginalFormat'
        source = {'url': url, 'adapter': 'parliament_document',
                  'expected_publication_id': 55076, 'expected_document_id': 305807,
                  'response_kind': 'pdf'}
        transport = SourceTransport([source])
        with patch('collect.fetch', return_value=(200, {'Content-Type': 'application/pdf'}, b'%PDF-1.7\\ncontent')) as fetch_mock:
            code, _, body = transport(url, {})
            self.assertEqual(code, 200)
            self.assertTrue(body.startswith(b'%PDF-'))
            self.assertEqual(fetch_mock.call_args.args[1]['Accept'], 'application/pdf')
        with patch('collect.fetch', return_value=(200, {'Content-Type': 'text/html'}, b'<html>please sign in</html>')):
            with self.assertRaisesRegex(ValueError, 'not a PDF'):
                transport(url, {})
        with patch('collect.fetch', return_value=(200, {'Content-Type': 'text/html'}, b'%PDF-challenge')):
            with self.assertRaisesRegex(ValueError, 'not a PDF'):
                transport(url, {})
        with patch('collect.fetch', return_value=(304, {}, b'')):
            self.assertEqual(transport(url, {})[0], 304)

    def test_parliament_document_blocks_unapproved_hosts_and_operations(self):
        for url in (
            'https://example.org/api/Publications/55076/Document/305807/OriginalFormat',
            'https://committees-api.parliament.uk/api/Publications/55077/Document/305807/OriginalFormat',
            'https://committees-api.parliament.uk/api/Publications/55076/Document/999999/OriginalFormat',
            'https://committees-api.parliament.uk/api/Publications/55076/Document/305807/OriginalFormat?extra=1',
        ):
            with self.subTest(url=url), patch('collect.fetch') as request:
                transport = SourceTransport([{'url': url, 'adapter': 'parliament_document',
                                              'expected_publication_id': 55076, 'expected_document_id': 305807,
                                              'response_kind': 'pdf'}])
                with self.assertRaisesRegex(ValueError, 'allowlisted'):
                    transport(url, {})
                request.assert_not_called()

    def test_parliament_format_based_pdf_route_is_strict(self):
        url = 'https://committees-api.parliament.uk/api/Publications/55076/Standard/pdf'
        source = {'url': url, 'adapter': 'parliament_document',
                  'expected_publication_id': 55076, 'response_kind': 'pdf'}
        transport = SourceTransport([source])
        with patch('collect.fetch', return_value=(200, {'Content-Type': 'application/pdf'}, b'%PDF-1.7\\nreport')):
            self.assertEqual(transport(url, {})[0], 200)
        wrong = 'https://committees-api.parliament.uk/api/Publications/55076/Standard/OriginalFormat'
        with patch('collect.fetch') as requested:
            with self.assertRaisesRegex(ValueError, 'allowlisted'):
                SourceTransport([{**source, 'url': wrong}])(wrong, {})
            requested.assert_not_called()

    def test_access_denials_wait_one_day_before_retrying(self):
        attempts = []
        def forbidden(url, headers):
            attempts.append(url)
            raise HTTPError(url, 403, 'forbidden', {}, None)
        first = self.run_collect(forbidden)
        self.assertEqual(first['sources']['official']['last_error_code'], 'http_403')
        self.assertEqual(datetime.fromisoformat(first['sources']['official']['next_attempt_at']), self.now + timedelta(days=1))
        self.run_collect(forbidden, 60)
        self.assertEqual(len(attempts), 1)

    def test_optional_official_routes_do_not_mask_original_failure(self):
        sources = self.sources + [{
            'source_id': 'official-pdf', 'url': 'https://example.org/report.pdf',
            'required_for_health': False, 'poll_target_minutes': 1440,
            'coverage_scope': 'original_document_candidate', 'supports_sources': ['official']
        }]
        def retrieve(url, headers):
            if url.endswith('/news'):
                raise HTTPError(url, 403, 'forbidden', {}, None)
            return 200, {'Content-Type': 'application/pdf'}, b'%PDF-1.7\\ntest'
        report = collect(sources, self.store, retrieve, self.now)
        self.assertFalse(report['coverage']['safe_to_claim_current'])
        self.assertTrue(report['supplemental_coverage']['safe_to_claim_current'])
        self.assertEqual(report['sources']['official']['last_error_code'], 'http_403')
        self.assertEqual(report['events'][0]['coverage_scope'], 'original_document_candidate')

    def test_registry_validates_document_routes_and_scope(self):
        real = Path(__file__).resolve().parents[1] / 'config' / 'collection.json'
        configured = load_sources(real)
        self.assertIn('PARL-REPORT-PDF-API', [s['source_id'] for s in configured])
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory) / 'collection.json'
            bad = [{
                'source_id': 'fake', 'url': 'https://example.org/fake',
                'poll_target_minutes': 60, 'adapter': 'parliament_document'
            }]
            tmp.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, 'PDF format'):
                load_sources(tmp)
            bad[0].update(adapter='public_document', supports_sources=['not-configured'])
            tmp.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, 'coverage scope'):
                load_sources(tmp)
            bad[0]['coverage_scope'] = 'metadata_only'
            tmp.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, 'known source IDs'):
                load_sources(tmp)

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
