from django.test import SimpleTestCase

from recommendations.services.progression_engine import calculate_next_set


class ProgressionEngineTests(SimpleTestCase):
    def test_increases_load_after_12_reps_with_reserve(self):
        recommendation = calculate_next_set(weight=50, reps=12, rir=2)

        self.assertEqual(recommendation["recommended_weight"], 52.5)
        self.assertEqual(recommendation["target_reps"], 12)

    def test_keeps_load_when_12_reps_are_close_to_failure(self):
        recommendation = calculate_next_set(weight=50, reps=12, rir=1)

        self.assertEqual(recommendation["recommended_weight"], 50)
        self.assertEqual(recommendation["target_reps"], 12)

    def test_reduces_load_when_missing_12_reps_near_failure(self):
        recommendation = calculate_next_set(weight=50, reps=10, rir=1)

        self.assertEqual(recommendation["recommended_weight"], 47.5)
        self.assertEqual(recommendation["target_reps"], 12)
