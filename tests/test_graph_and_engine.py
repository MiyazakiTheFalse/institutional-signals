import copy
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from knowledge_graph import validate, replay, impacted_decisions, features
from forecast_engine import baseline_snapshot, append_snapshot, evaluate_predictions

T = '2026-11-15T12:00:00Z'
class ResearchTests(unittest.TestCase):
    def setUp(self):
        self.edge = dict(edge_id='e1', subject_id='body', predicate='can_approve', object_id='decision', evidence_ids=['source'], valid_from=T, valid_to=None, published_at=T, first_observed_at=T, recorded_at=T, reviewed_at=T, review_state='verified', assertion_type='documented_fact', scope='Test fixture only', limitations='Synthetic', independence_group='doc1')
        self.graph = {'nodes': [{'id':'body','type':'public_body','label':'Synthetic body'}, {'id':'decision','type':'decision','label':'Synthetic decision'}], 'edges':[self.edge]}
    def test_missing_provenance_rejected(self):
        self.edge['evidence_ids'] = []
        with self.assertRaises(ValueError): validate(self.graph, {'source'})
    def test_future_observation_excluded(self):
        self.edge['first_observed_at'] = '2026-11-16T12:00:00Z'
        self.assertEqual(replay(self.graph, T), [])
    def test_review_cannot_leak_backwards(self):
        self.edge['reviewed_at'] = '2026-11-16T12:00:00Z'
        self.assertEqual(replay(self.graph, T), [])
    def test_correction_preserves_past(self):
        revised = {**self.edge, 'edge_id':'e2', 'supersedes':'e1', 'recorded_at':'2026-11-16T12:00:00Z', 'reviewed_at':'2026-11-16T12:00:00Z', 'predicate':'can_block'}
        self.graph['edges'].append(revised); validate(self.graph, {'source'})
        self.assertEqual(replay(self.graph,T)[0]['edge_id'],'e1')
        self.assertEqual(replay(self.graph,'2026-11-17T12:00:00Z')[0]['edge_id'],'e2')
    def test_impact_and_features_keep_provenance(self):
        self.assertEqual(impacted_decisions(self.graph,['source'],T), ['decision'])
        self.assertEqual(features(self.graph,'decision',T)['edge_ids'], ['e1'])
    def fixture(self):
        return dict(case={'case_id':'test','question':'Synthetic event?','resolution_rule':'Synthetic binary outcome','model_version':'baseline-v1','horizon_end':'2027-01-01T00:00:00Z'}, gate={'can_update_forecast':True,'evaluated_at':T}, outcomes=[{'id':str(i),'outcome':i%2,'resolved_at':T,'available_at':T,'independence_group':str(i)} for i in range(20)], evidence=[{'id':'source','available_at':T,'reviewed_at':T,'review_state':'verified'}], as_of=T)
    def test_abstains_on_missing_evidence_or_labels(self):
        x=self.fixture(); x['gate']['can_update_forecast']=False
        self.assertEqual(baseline_snapshot(**x)['status'],'hold')
        x=self.fixture(); x['outcomes']=[]
        self.assertEqual(baseline_snapshot(**x)['reason'],'insufficient_independent_outcomes')
    def test_future_and_duplicate_labels_do_not_inflate_count(self):
        x=self.fixture(); x['outcomes'][0]['available_at']='2027-01-01T00:00:00Z'
        self.assertEqual(baseline_snapshot(**x)['outcome_count'],19)
        x=self.fixture(); x['outcomes'][0]['independence_group']='1'
        self.assertEqual(baseline_snapshot(**x)['outcome_count'],19)
    def test_snapshot_cannot_be_overwritten(self):
        s=baseline_snapshot(**self.fixture()); self.assertEqual(s['probability'],.5)
        with tempfile.TemporaryDirectory() as folder:
            append_snapshot(folder,s)
            with self.assertRaises(FileExistsError): append_snapshot(folder,s)
            changed=copy.deepcopy(s); changed['probability']=.9
            with self.assertRaises(ValueError): append_snapshot(folder,changed)
    def test_worse_model_not_promoted(self):
        rows=[{'as_of':T,'resolved_at':'2027-01-01T00:00:00Z','probability':.9,'baseline_probability':.5,'outcome':0,'independence_group':str(i)} for i in range(100)]
        self.assertFalse(evaluate_predictions(rows)['promotion_eligible'])
