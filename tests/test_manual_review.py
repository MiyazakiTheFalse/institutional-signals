import sys
import unittest
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from review_evidence import reviewed_record
from coverage import evaluate
class ManualReviewTests(unittest.TestCase):
    def setUp(self):
        self.now=datetime(2026,11,15,12,tzinfo=timezone.utc)
        self.manifest={'id':'submission','sha256':'abc','published_at':'2026-01-01T00:00:00Z','received_at':'2026-11-15T11:00:00Z'}
        self.scan={'scan_state':'clean','sha256':'abc','scanned_at':'2026-11-15T11:30:00Z'}
        self.req={'id':'body','label':'Report','capability':'body','routes':[{'source_id':'publisher'}]}
        self.source={'source_id':'publisher','poll_target_minutes':60}
    def record(self): return reviewed_record(self.manifest,self.scan,self.req,self.source,'operator','document-1',self.now)
    def test_scan_integrity_required(self):
        self.scan['sha256']='other'
        with self.assertRaises(ValueError): self.record()
    def test_unavailable_route_can_be_filled_by_current_verified_manual_content(self):
        gate=evaluate([self.req],[self.source],{},[self.record()],self.now)
        self.assertTrue(gate['can_update_forecast'])
    def test_expired_manual_review_returns_to_hold(self):
        record=self.record()
        later=datetime(2026,11,15,16,tzinfo=timezone.utc)
        self.assertFalse(evaluate([self.req],[self.source],{},[record],later)['can_update_forecast'])
    def test_overlong_freshness_claim_rejected(self):
        record=self.record(); record['valid_until']='2027-01-01T00:00:00Z'
        self.assertFalse(evaluate([self.req],[self.source],{},[record],self.now)['can_update_forecast'])
