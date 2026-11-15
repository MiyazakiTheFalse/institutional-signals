import unittest
from datetime import datetime, timedelta, timezone

from scripts.freshness import source_health, required_source_coverage
from scripts.probability import horizon_event_probability, beta_binomial_base_rate, brier_score


class TestFreshnessAndProbability(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 15, 12, tzinfo=timezone.utc)

    def test_current_check_with_old_publication(self):
        check = source_health(checked_at=self.now - timedelta(minutes=8), now=self.now,
                              target_minutes=15,
                              published_at=self.now - timedelta(days=365))
        self.assertEqual(check["status"], "current")
        self.assertGreater(check["publication_age_minutes"], 500_000)

    def test_late_check(self):
        check = source_health(checked_at=self.now - timedelta(minutes=40), now=self.now,
                              target_minutes=15)
        self.assertEqual(check["status"], "delayed")

    def test_outage_is_not_current(self):
        check = source_health(checked_at=self.now - timedelta(minutes=10), now=self.now,
                              target_minutes=15, consecutive_failures=3)
        self.assertEqual(check["status"], "unavailable")
        self.assertFalse(required_source_coverage(["current", check["status"]])["safe_to_claim_current"])

    def test_missing_source_check(self):
        self.assertEqual(source_health(checked_at=None, now=self.now,
                                       target_minutes=30)["status"], "unavailable")

    def test_reject_naive_datetime(self):
        with self.assertRaises(ValueError):
            source_health(checked_at=datetime(2026, 11, 15, 11), now=self.now, target_minutes=15)

    def test_horizon(self):
        self.assertAlmostEqual(horizon_event_probability([0.1, 0.2]), 0.28)

    def test_zero_outcomes_baseline_not_zero(self):
        self.assertAlmostEqual(beta_binomial_base_rate(events=0, observations=8), 0.1)

    def test_brier(self):
        self.assertAlmostEqual(brier_score([(0.75, 1), (0.25, 0)]), 0.0625)


if __name__ == "__main__":
    unittest.main()
