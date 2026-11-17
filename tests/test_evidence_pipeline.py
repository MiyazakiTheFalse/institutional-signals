import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from evidence_journal import event_from_review, append_event, replay, read_journal
from forecast_pipeline import issue
from forecast_engine import append_snapshot

T = '2026-11-15T12:00:00Z'
NEXT = '2026-11-16T12:00:00Z'

def review(rid='r1', digest='a'*64, available=T, verified=T):
    return {'id':rid, 'source_id':'S1', 'sha256':digest, 'available_at':available,
            'reviewed_at':verified, 'published_at':available,
            'primary_document_id':'official-report-1', 'review_state':'verified',
            'capabilities':['official_report']}

class EvidenceTests(unittest.TestCase):
    def test_refuses_unreviewed_and_naive_timestamp(self):
        r=review(); r['review_state']='unreviewed_content_change'
        with self.assertRaises(ValueError):
            event_from_review(r,event_type='filing',institution_ids=['I'])
        r=review(); r['available_at']='2026-11-15T12:00:00'
        with self.assertRaises(ValueError):
            event_from_review(r,event_type='filing',institution_ids=['I'])

    def test_append_only_and_correction_replay(self):
        base=event_from_review(review(),event_type='filing',institution_ids=['I'])
        correction=event_from_review(review('r2','b'*64,NEXT,NEXT),event_type='correction',
                                      institution_ids=['I'],supersedes=base['event_id'])
        with tempfile.TemporaryDirectory() as d:
            append_event(d,base); append_event(d,correction)
            with self.assertRaises(FileExistsError):
                append_event(d,base)
            self.assertEqual(replay(read_journal(d),T)[0]['event_id'],base['event_id'])
            self.assertEqual(replay(read_journal(d),NEXT)[0]['event_id'],correction['event_id'])

    def test_duplicate_source_document_not_multiplied(self):
        a=event_from_review(review(),event_type='filing',institution_ids=['I'])
        b=event_from_review(review('r2','b'*64),event_type='filing',institution_ids=['I'])
        self.assertEqual(len(replay([a,b],T)),1)

class PipelineTests(unittest.TestCase):
    def fixture(self):
        r=review()
        e=event_from_review(r,event_type='filing',institution_ids=['I'])
        requirements=[{'id':'report','label':'Report','capability':'official_report',
                       'routes':[{'source_id':'S1'}]}]
        sources=[{'source_id':'S1','poll_target_minutes':60}]
        state={'S1':{'last_success_at':T,'sha256':r['sha256'],'consecutive_failures':0}}
        case={'case_id':'synthetic','question':'Will event occur?',
              'resolution_rule':'Synthetic only','model_version':'beta-v1',
              'horizon_end':'2027-01-01T00:00:00Z'}
        outcomes=[{'id':str(i),'outcome':i%2,'resolved_at':T,
                   'available_at':T,'independence_group':str(i)} for i in range(20)]
        return case, requirements, sources, state, [r], [e], outcomes

    def test_issued_once_when_material_change(self):
        args=self.fixture()
        first=issue(*args,T)
        self.assertEqual(first['status'],'experimental_baseline')
        self.assertEqual(first['probability'],0.5)
        with tempfile.TemporaryDirectory() as d:
            append_snapshot(d,first)
            with self.assertRaises(FileExistsError):
                append_snapshot(d,first)
        self.assertEqual(issue(*args,T,previous=first)['status'],'no_change')

    def test_outage_holds_not_negative_outcome(self):
        args=list(self.fixture()); args[3]['S1']['consecutive_failures']=3
        self.assertEqual(issue(*args,T)['status'],'hold')

    def test_future_verified_evidence_excluded(self):
        args=list(self.fixture()); args[5][0]['verified_at']=NEXT
        self.assertEqual(issue(*args,T)['reason'],'no_verified_structured_events')

    def test_insufficient_outcomes_abstain(self):
        args=list(self.fixture()); args[6]=[]
        self.assertEqual(issue(*args,T)['reason'],'insufficient_independent_outcomes')

if __name__ == '__main__':
    unittest.main()
