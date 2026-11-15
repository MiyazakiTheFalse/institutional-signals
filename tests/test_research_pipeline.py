import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collect import LocalStore,packed
from research_pipeline import run
class PipelineTests(unittest.TestCase):
    def test_no_registered_target_produces_no_prediction(self):
        with tempfile.TemporaryDirectory() as directory:
            store=LocalStore(directory)
            report=run(store,[],[],[],'2026-11-15T12:00:00Z')
            self.assertEqual(report['cases'],[])
            self.assertFalse((Path(directory)/'forecasts').exists())
    def test_missing_gate_abstains_even_with_registered_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            store=LocalStore(directory)
            case={'case_id':'test','case_family':'synthetic','question':'Synthetic?','resolution_rule':'Test','model_version':'base-v1','horizon_end':'2027-01-01T00:00:00Z','evidence_ids':[]}
            report=run(store,[case],[],[],'2026-11-15T12:00:00Z')
            self.assertEqual(report['cases'][0]['status'],'hold')
