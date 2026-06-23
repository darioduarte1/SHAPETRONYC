from django.test import SimpleTestCase
from types import SimpleNamespace

from recommendations.services.progression_engine import calculate_next_set
from recommendations.services.ai_coach_engine import build_local_coach_summary
from recommendations.services.training_coach_engine import calculate_training_coach_decision
from recommendations.services.workout_progression_engine import calculate_exercise_progression


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


class TrainingCoachEngineTests(SimpleTestCase):
    def test_working_set_below_target_is_treated_as_failure(self):
        decision = calculate_training_coach_decision(
            weight=50,
            reps=10,
            rir=None,
            is_failure=True,
            set_type="WORKING",
        )

        self.assertEqual(decision["action"], "reduce_load")
        self.assertEqual(decision["recommended_weight"], 47.5)
        self.assertEqual(decision["target_reps"], 12)
        self.assertEqual(decision["next_set_type"], "WORKING")

    def test_warmup_does_not_progress_load(self):
        decision = calculate_training_coach_decision(
            weight=20,
            reps=12,
            rir=4,
            is_failure=False,
            set_type="WARMUP",
        )

        self.assertEqual(decision["action"], "prepare_working_set")
        self.assertEqual(decision["recommended_weight"], "")
        self.assertEqual(decision["target_reps"], 12)

    def test_negative_feedback_blocks_load_increase(self):
        decision = calculate_training_coach_decision(
            weight=50,
            reps=12,
            rir=3,
            is_failure=False,
            notes="dormi mal e estou cansado",
            set_type="WORKING",
        )

        self.assertEqual(decision["action"], "maintain")
        self.assertEqual(decision["recommended_weight"], 50)

    def test_reduces_more_after_consecutive_working_misses(self):
        decision = calculate_training_coach_decision(
            weight=50,
            reps=9,
            rir=None,
            is_failure=True,
            set_type="WORKING",
            current_sets=[
                {
                    "set_number": 1,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 10,
                    "rir": None,
                    "reached_failure": True,
                },
                {
                    "set_number": 2,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 9,
                    "rir": None,
                    "reached_failure": True,
                },
            ],
        )

        self.assertEqual(decision["action"], "reduce_load_for_fatigue")
        self.assertEqual(decision["recommended_weight"], 45)
        self.assertEqual(decision["recommended_rest_seconds"], 180)
        self.assertEqual(decision["context"]["consecutive_working_misses"], 2)

    def test_stabilizes_load_after_previous_miss(self):
        decision = calculate_training_coach_decision(
            weight=50,
            reps=12,
            rir=3,
            is_failure=False,
            set_type="WORKING",
            current_sets=[
                {
                    "set_number": 1,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 10,
                    "rir": None,
                    "reached_failure": True,
                },
                {
                    "set_number": 2,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 12,
                    "rir": 3,
                    "reached_failure": False,
                },
            ],
        )

        self.assertEqual(decision["action"], "stabilize_after_miss")
        self.assertEqual(decision["recommended_weight"], 50)
        self.assertEqual(decision["recommended_rest_seconds"], 150)


class WorkoutProgressionEngineTests(SimpleTestCase):
    def make_training_exercise(self):
        return SimpleNamespace(
            id=1,
            exercise_id=10,
            exercise=SimpleNamespace(name="Bench Press"),
            sets=3,
            target_rir=2,
        )

    def test_increases_load_for_next_workout_after_clean_sets(self):
        recommendation = calculate_exercise_progression(
            self.make_training_exercise(),
            [
                {
                    "set_number": 1,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 12,
                    "rir": 2,
                    "reached_failure": False,
                },
                {
                    "set_number": 2,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 12,
                    "rir": 3,
                    "reached_failure": False,
                },
            ],
        )

        self.assertEqual(recommendation["action"], "increase_load")
        self.assertEqual(recommendation["recommended_weight"], 52.5)
        self.assertEqual(recommendation["recommended_sets"], 3)

    def test_reduces_volume_for_next_workout_after_repeated_misses(self):
        recommendation = calculate_exercise_progression(
            self.make_training_exercise(),
            [
                {
                    "set_number": 1,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 10,
                    "rir": None,
                    "reached_failure": True,
                },
                {
                    "set_number": 2,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 9,
                    "rir": None,
                    "reached_failure": True,
                },
            ],
        )

        self.assertEqual(recommendation["action"], "reduce_volume")
        self.assertEqual(recommendation["recommended_weight"], 47.5)
        self.assertEqual(recommendation["recommended_sets"], 2)
        self.assertEqual(recommendation["target_rir"], 3)


class AiCoachEngineTests(SimpleTestCase):
    def test_local_coach_highlights_progression_opportunity(self):
        summary = build_local_coach_summary(
            {
                "session": {
                    "notes": "",
                    "total_sets": 6,
                    "total_volume": 3600,
                    "failure_count": 0,
                    "exercise_count": 2,
                },
                "progression": {
                    "summary": {
                        "action_counts": {
                            "increase_load": 1,
                            "maintain_load": 1,
                        }
                    }
                },
            }
        )

        self.assertEqual(summary["status"], "llm_disabled")
        self.assertIn("margem", summary["headline"].lower())
        self.assertEqual(summary["metrics"]["total_sets"], 6)

    def test_local_coach_prioritizes_recovery_when_failures_accumulate(self):
        summary = build_local_coach_summary(
            {
                "session": {
                    "notes": "muito pesado",
                    "total_sets": 5,
                    "total_volume": 2200,
                    "failure_count": 2,
                    "exercise_count": 1,
                },
                "progression": {
                    "summary": {
                        "action_counts": {
                            "reduce_volume": 1,
                        }
                    }
                },
            }
        )

        self.assertIn("recuperação", summary["headline"].lower())
        self.assertIn("falha", " ".join(summary["focus_points"]).lower())
