from django.test import SimpleTestCase

from recommendations.services.progression_engine import calculate_next_set
from recommendations.services.training_coach_engine import calculate_training_coach_decision


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
