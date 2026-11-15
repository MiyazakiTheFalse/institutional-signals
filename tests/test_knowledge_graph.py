"""Evidence and temporal replay regression tests for institutional decision graph."""
from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("knowledge_graph", ROOT / "scripts" / "knowledge_graph.py")
assert spec and spec.loader
graph_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graph_module)


def fixture():
    edge = {
        "edge_id": "E1",
        "subject_id": "regulator",
        "predicate": "can_approve",
        "object_id": "decision",
        "evidence_ids": ["SRC-1"],
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_to": None,
        "published_at": "2026-01-02T00:00:00Z",
        "first_observed_at": "2026-01-03T00:00:00Z",
        "recorded_at": "2026-01-03T00:00:00Z",
        "reviewed_at": "2026-01-04T00:00:00Z",
        "review_state": "verified",
        "assertion_type": "documented_fact",
        "scope": "Example approval procedure",
        "limitations": "Test data only; not a claim about an institution",
        "independence_group": "PRIMARY-1",
    }
    return {
        "version": "0.1",
        "nodes": [
            {"id": "regulator", "type": "public_body", "label": "Example regulator"},
            {"id": "decision", "type": "decision", "label": "Example decision"},
        ],
        "edges": [edge],
    }


class GraphIntegrityTests(unittest.TestCase):
    def test_valid_documented_relationship(self):
        graph = fixture()
        self.assertIs(graph_module.validate(graph, {"SRC-1"}), graph)
        report = graph_module.features(graph, "decision", "2026-02-01T00:00:00Z")
        self.assertEqual(report["documented_approvers"], 1)
        self.assertEqual(report["independent_source_groups"], 1)

    def test_no_lookahead_from_publication_first_seen_or_review(self):
        graph = fixture()
        for instant in (
            "2026-01-01T12:00:00Z",  # before published
            "2026-01-02T12:00:00Z",  # published but not observed
            "2026-01-03T12:00:00Z",  # observed, but not reviewed
        ):
            with self.subTest(cutoff=instant):
                self.assertEqual(graph_module.replay(graph, instant), [])
        self.assertEqual(
            [e["edge_id"] for e in graph_module.replay(graph, "2026-01-04T00:00:00Z")],
            ["E1"],
        )

    def test_correction_never_rewrites_prior_forecast(self):
        graph = fixture()
        revised = copy.deepcopy(graph["edges"][0])
        revised.update(
            edge_id="E2", supersedes="E1", predicate="can_block",
            published_at="2026-02-01T00:00:00Z",
            first_observed_at="2026-02-02T00:00:00Z",
            recorded_at="2026-02-02T00:00:00Z",
            reviewed_at="2026-02-03T00:00:00Z",
        )
        graph["edges"].append(revised)
        graph_module.validate(graph, {"SRC-1"})
        self.assertEqual(
            [e["edge_id"] for e in graph_module.replay(graph, "2026-01-10T00:00:00Z")],
            ["E1"],
        )
        self.assertEqual(
            [e["edge_id"] for e in graph_module.replay(graph, "2026-02-04T00:00:00Z")],
            ["E2"],
        )

    def test_unknown_or_missing_source_rejected(self):
        graph = fixture()
        graph["edges"][0]["evidence_ids"] = ["UNKNOWN"]
        with self.assertRaises(ValueError):
            graph_module.validate(graph, {"SRC-1"})

    def test_naive_and_non_utc_time_rejected(self):
        for value in ("2026-01-01T00:00:00", "2026-01-01T01:00:00+01:00"):
            graph = fixture()
            graph["edges"][0]["recorded_at"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                graph_module.validate(graph, {"SRC-1"})

    def test_source_update_identifies_affected_decision(self):
        graph = fixture()
        graph_module.validate(graph, {"SRC-1"})
        self.assertEqual(
            graph_module.impacted_decisions(graph, ["SRC-1"], "2026-01-05T00:00:00Z"),
            ["decision"],
        )
        self.assertEqual(
            graph_module.impacted_decisions(graph, ["UNKNOWN"], "2026-01-05T00:00:00Z"),
            [],
        )


if __name__ == "__main__":
    unittest.main()
