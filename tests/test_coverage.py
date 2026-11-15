import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from coverage import evaluate


class Gates(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 15, 12, tzinfo=timezone.utc)
        self.sources = [{'source_id': s, 'poll_target_minutes': 60} for s in ('original', 'mirror')]
        self.state = {s: {'last_success_at': '2026-11-15T12:00:00Z', 'sha256': 'abc'} for s in ('original', 'mirror')}
        self.requirements = [{'id': 'body', 'label': 'Report content', 'capability': 'body',
                              'routes': [{'source_id': 'original'}, {'source_id': 'mirror'}]}]
        self.records = [{'source_id': s, 'sha256': 'abc', 'reviewed_at': '2026-11-15T12:00:00Z',
                         'available_at': '2026-11-15T11:00:00Z', 'review_state': 'verified',
                         'capabilities': ['body'], 'primary_document_id': 'same-document'} for s in ('original', 'mirror')]

    def gate(self):
        return evaluate(self.requirements, self.sources, self.state, self.records, self.now)

    def test_reviewed_equivalent_mirror_can_satisfy_missing_original(self):
        self.state['original'] = {}
        self.assertTrue(self.gate()['can_update_forecast'])

    def test_discovery_is_not_content(self):
        for r in self.records:
            r['capabilities'] = ['metadata']
        self.assertEqual(self.gate()['decision'], 'hold')

    def test_repetition_is_not_independent_evidence(self):
        self.requirements[0]['min_independent_documents'] = 2
        self.assertFalse(self.gate()['can_update_forecast'])

    def test_unreviewed_or_changed_content_holds_forecast(self):
        for r in self.records:
            r['sha256'] = 'old-version'
        self.assertFalse(self.gate()['can_update_forecast'])

    def test_stale_checks_hold_forecast(self):
        for row in self.state.values():
            row['last_success_at'] = '2026-11-14T12:00:00Z'
        self.assertFalse(self.gate()['can_update_forecast'])

    def test_future_evidence_rejected_from_asof_gate(self):
        for row in self.records:
            row['available_at'] = '2026-11-16T12:00:00Z'
        self.assertFalse(self.gate()['can_update_forecast'])
