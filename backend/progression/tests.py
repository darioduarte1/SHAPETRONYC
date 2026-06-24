from types import SimpleNamespace

from django.test import SimpleTestCase

from progression.services.exercise_history_recommendation import (
    build_history_based_recommended_sets,
    calculate_recommended_set,
)


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

    def test_last_15_history_recommends_first_working_set_and_warmup(self):
        recent_session_sets = [
            [
                SimpleNamespace(
                    set_type="WORKING",
                    weight_used=50,
                    reps_completed=12,
                    rir=3,
                    reached_failure=False,
                )
            ]
            for _ in range(5)
        ]

        recommendations = build_history_based_recommended_sets(
            recent_session_sets,
            planned_working_sets=3,
        )

        self.assertEqual(recommendations[0]["set_type"], "WARMUP")
        self.assertEqual(recommendations[0]["recommended_weight"], 26.0)
        self.assertEqual(recommendations[1]["set_type"], "WORKING")
        self.assertEqual(recommendations[1]["recommended_weight"], 52.5)
        self.assertEqual(recommendations[1]["confidence"], "alta")
        self.assertEqual(len(recommendations), 4)

    def test_last_15_history_reduces_first_working_set_after_misses(self):
        recent_session_sets = [
            [
                SimpleNamespace(
                    set_type="WORKING",
                    weight_used=50,
                    reps_completed=10,
                    rir=1,
                    reached_failure=True,
                )
            ]
            for _ in range(3)
        ]

        recommendations = build_history_based_recommended_sets(
            recent_session_sets,
            planned_working_sets=3,
        )

        self.assertEqual(recommendations[1]["recommended_weight"], 47.5)
        self.assertIn("falhas", recommendations[1]["reason"])
