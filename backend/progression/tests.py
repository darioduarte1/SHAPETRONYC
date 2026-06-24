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
        self.assertEqual(recommendations[0]["recommended_weight"], 29.0)
        self.assertEqual(recommendations[1]["set_type"], "WORKING")
        self.assertEqual(recommendations[1]["recommended_weight"], 52.5)
        self.assertEqual(recommendations[1]["confidence"], "alta")
        self.assertEqual(len(recommendations), 4)

    def test_heavier_compound_exercise_uses_multiple_warmup_ramp_sets(self):
        recent_session_sets = [
            [
                SimpleNamespace(
                    set_type="WORKING",
                    weight_used=70,
                    reps_completed=12,
                    rir=3,
                    reached_failure=False,
                )
            ]
            for _ in range(5)
        ]
        exercise_profile = SimpleNamespace(
            is_compound=True,
            movement_pattern="HORIZONTAL_PUSH",
        )

        recommendations = build_history_based_recommended_sets(
            recent_session_sets,
            planned_working_sets=3,
            exercise_profile=exercise_profile,
        )

        self.assertEqual([set_log["set_type"] for set_log in recommendations[:3]], ["WARMUP", "WARMUP", "WORKING"])
        self.assertEqual(recommendations[0]["recommended_weight"], 32.5)
        self.assertEqual(recommendations[0]["recommended_reps"], 8)
        self.assertEqual(recommendations[1]["recommended_weight"], 51.0)
        self.assertEqual(recommendations[1]["recommended_reps"], 4)
        self.assertEqual(recommendations[2]["recommended_weight"], 72.5)
        self.assertEqual(recommendations[2]["set_number"], 3)
        self.assertEqual(len(recommendations), 5)

    def test_very_heavy_compound_exercise_uses_three_warmups_before_working_set(self):
        recent_session_sets = [
            [
                SimpleNamespace(
                    set_type="WORKING",
                    weight_used=100,
                    reps_completed=12,
                    rir=2,
                    reached_failure=False,
                )
            ]
            for _ in range(5)
        ]
        exercise_profile = SimpleNamespace(
            is_compound=True,
            movement_pattern="SQUAT",
        )

        recommendations = build_history_based_recommended_sets(
            recent_session_sets,
            planned_working_sets=3,
            exercise_profile=exercise_profile,
        )

        self.assertEqual([set_log["set_type"] for set_log in recommendations[:4]], ["WARMUP", "WARMUP", "WARMUP", "WORKING"])
        self.assertEqual([set_log["recommended_reps"] for set_log in recommendations[:3]], [8, 5, 2])
        self.assertEqual(recommendations[3]["recommended_weight"], 102.5)
        self.assertEqual(recommendations[3]["set_number"], 4)

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
