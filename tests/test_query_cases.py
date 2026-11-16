"""Registered query cases remain auditable, cross-linked to the curated corpus."""
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
SPEC = importlib.util.spec_from_file_location('build_data_query_tests', ROOT / 'scripts' / 'build_data.py')
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class QueryCaseValidationTests(unittest.TestCase):
    def setUp(self):
        self.cases = MODULE.read_json('query_cases.json')
        self.original = MODULE.read_json

    def export_with(self, cases):
        with patch.object(MODULE, 'read_json',
                          side_effect=lambda name: cases if name == 'query_cases.json' else self.original(name)):
            return MODULE.validate_and_export()

    def test_case_register_is_exported_and_source_scoped(self):
        data = MODULE.validate_and_export()
        self.assertEqual(data['query_cases'][0]['id'], 'uk-water-thames')
        evidence_ids = {s['id'] for s in data['sources']}
        self.assertTrue(set(data['query_cases'][0]['source_ids']).issubset(evidence_ids))

    def test_new_empty_case_does_not_pretend_it_has_evidence(self):
        extra = {
            'id': 'synthetic-metro', 'title': 'Synthetic metro case',
            'summary': 'Placeholder for tests only', 'domain': 'transport',
            'geography': 'Test locality', 'aliases': ['synthetic metro'],
            'topics': [], 'source_ids': [], 'observation_ids': [], 'entity_ids': [],
            'readiness': 'research_only',
        }
        data = self.export_with(self.cases + [extra])
        self.assertEqual(len(data['query_cases']), 2)
        self.assertFalse(next(c for c in data['query_cases'] if c['id'] == 'synthetic-metro')['source_ids'])

    def test_rejects_cross_case_source_reference(self):
        candidate = copy.deepcopy(self.cases)
        candidate[0]['source_ids'].append('NOT-REGISTERED')
        with self.assertRaisesRegex(ValueError, 'unknown sources'):
            self.export_with(candidate)

    def test_rejects_case_observation_without_its_sources(self):
        candidate = copy.deepcopy(self.cases)
        candidate[0]['source_ids'].remove('PARL-2026-09')
        with self.assertRaisesRegex(ValueError, 'out-of-case evidence'):
            self.export_with(candidate)

    def test_rejects_duplicate_alias_even_across_cases(self):
        candidate = copy.deepcopy(self.cases)
        extra = copy.deepcopy(candidate[0])
        extra['id'] = 'duplicate-alias-case'
        with self.assertRaisesRegex(ValueError, 'Ambiguous'):
            self.export_with(candidate + [extra])

    def test_rejects_false_readiness_claim(self):
        candidate = copy.deepcopy(self.cases)
        candidate[0]['readiness'] = 'forecast_ready'
        with self.assertRaisesRegex(ValueError, 'cannot claim'):
            self.export_with(candidate)


if __name__ == '__main__':
    unittest.main()
