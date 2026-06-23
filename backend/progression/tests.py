from types import SimpleNamespace

from django.test import SimpleTestCase

from progression.services.exercise_history_recommendation import calculate_recommended_set


class ExerciseHistoryRecommendationTests(SimpleTestCase):
    def test_history_recommendation_targets_12_reps(self):
        previous_set = SimpleNamespace(
            weight_used=50,
            reps_completed=12,
            rir=2,
            reached_failure=False,
        )

        recommendation = calculate_recommended_set(previous_set)

        self.assertEqual(recommendation["recommended_weight"], 52.5)
        self.assertEqual(recommendation["recommended_reps"], 12)

    def test_history_recommendation_keeps_weight_until_12_reps_are_reached(self):
        previous_set = SimpleNamespace(
            weight_used=50,
            reps_completed=10,
            rir=2,
            reached_failure=False,
        )

        recommendation = calculate_recommended_set(previous_set)

        self.assertEqual(recommendation["recommended_weight"], 50)
        self.assertEqual(recommendation["recommended_reps"], 12)
