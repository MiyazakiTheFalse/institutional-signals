"""Provenance and as-of checks for the first curated publication graph."""
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from knowledge_graph import validate, replay

class PublishedGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {r['id']: r for r in json.loads((ROOT / 'data/source_registry.json').read_text())}
        cls.graph = json.loads((ROOT / 'data/knowledge_graph.json').read_text())

    def test_publisher_edges_are_curated_and_independently_sourced(self):
        validate(self.graph, set(self.sources))
        publication_edges = [r for r in self.graph['edges'] if r['predicate'] == 'issued']
        self.assertGreaterEqual(len(publication_edges), 4)
        for edge in publication_edges:
            with self.subTest(edge=edge['edge_id']):
                self.assertEqual(edge['review_state'], 'verified')
                self.assertEqual(edge['assertion_type'], 'documented_fact')
                self.assertEqual(len(edge['evidence_ids']), 1)
                source = self.sources[edge['evidence_ids'][0]]
                self.assertEqual(edge['independence_group'], source['id'])
                self.assertEqual(edge['published_at'][:10], source['published_at'])
                self.assertEqual(edge['first_observed_at'][:10], source['verified_at'])
                self.assertIn('day precision', edge['limitations'])
                self.assertEqual(edge['review_method'], 'source_register_publisher_attribution')

    def test_current_graph_is_not_backdated_into_old_forecasts(self):
        # All edges were constructed on 16 November: earlier as-of views must be empty.
        self.assertEqual(replay(self.graph, '2026-11-15T23:59:59Z'), [])
        latest = max(e['reviewed_at'] for e in self.graph['edges'])
        self.assertEqual(len(replay(self.graph, latest)), len(self.graph['edges']))

    def test_no_influence_or_decision_rights_are_inferred(self):
        # Publisher attribution is useful provenance, not proof of authority.
        self.assertTrue(all(e['predicate'] == 'issued' for e in self.graph['edges']))

    def test_export_matches_bundled_dashboard(self):
        dashboard = json.loads((ROOT / 'public/data/dashboard.json').read_text())
        self.assertEqual(dashboard['knowledge_graph'], self.graph)

if __name__ == '__main__':
    unittest.main()
