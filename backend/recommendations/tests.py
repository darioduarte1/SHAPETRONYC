from django.test import SimpleTestCase, override_settings
from types import SimpleNamespace
from unittest.mock import patch

from recommendations.services.progression_engine import calculate_next_set
from recommendations.services.ai_coach_engine import build_local_coach_summary
from recommendations.services.ai_training_decision_engine import generate_ai_training_decision
from recommendations.services.training_coach_engine import calculate_training_coach_decision
from recommendations.services.workout_progression_engine import calculate_exercise_progression


class ProgressionEngineTests(SimpleTestCase):
    def test_increases_load_after_12_reps_with_reserve(self):
        recommendation = calculate_next_set(weight=50, reps=12, rir=2)

        self.assertEqual(recommendation["recommended_weight"], 51.0)
        self.assertEqual(recommendation["target_reps"], 12)

    def test_keeps_load_when_12_reps_are_close_to_failure(self):
        recommendation = calculate_next_set(weight=50, reps=12, rir=1)

        self.assertEqual(recommendation["recommended_weight"], 50)
        self.assertEqual(recommendation["target_reps"], 12)

    def test_reduces_load_when_missing_12_reps_near_failure(self):
        recommendation = calculate_next_set(weight=50, reps=10, rir=1)

        self.assertEqual(recommendation["recommended_weight"], 50)
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

        self.assertEqual(decision["action"], "decrease_weight")
        self.assertEqual(decision["recommended_weight"], 45.0)
        self.assertEqual(decision["target_reps"], 12)
        self.assertEqual(decision["next_set_type"], "WORKING")

    def test_warmup_does_not_progress_load(self):
        decision = calculate_training_coach_decision(
            weight=20,
            reps=12,
            rir=None,
            is_failure=False,
            set_type="WARMUP",
        )

        self.assertEqual(decision["action"], "maintain_weight")
        self.assertEqual(decision["recommended_weight"], 20)
        self.assertEqual(decision["target_reps"], 12)

    def test_warmup_can_request_another_warmup_before_working_sets(self):
        decision = calculate_training_coach_decision(
            weight=20,
            reps=8,
            rir=None,
            is_failure=False,
            set_type="WARMUP",
            current_sets=[
                {
                    "set_number": 1,
                    "set_type": "WARMUP",
                    "weight_used": 20,
                    "reps_completed": 8,
                    "rir": None,
                    "reached_failure": False,
                }
            ],
            history_sets=[
                {
                    "set_number": 1,
                    "set_type": "WORKING",
                    "weight_used": 60,
                    "reps_completed": 12,
                    "rir": 2,
                    "reached_failure": False,
                }
            ],
        )

        self.assertEqual(decision["action"], "add_set")
        self.assertEqual(decision["next_set_type"], "WARMUP")
        self.assertEqual(decision["recommended_weight"], 25)

    def test_negative_feedback_blocks_load_increase(self):
        decision = calculate_training_coach_decision(
            weight=50,
            reps=12,
            rir=3,
            is_failure=False,
            notes="dormi mal e estou cansado",
            set_type="WORKING",
        )

        self.assertEqual(decision["action"], "maintain_weight")
        self.assertEqual(decision["recommended_weight"], 50)
        self.assertFalse(decision["guardrails"]["has_pain_or_risk"])

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

        self.assertEqual(decision["action"], "stop_exercise")
        self.assertEqual(decision["next_set_type"], "COMPLETE")
        self.assertEqual(decision["exercise_status"], "complete")
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

        self.assertEqual(decision["action"], "maintain_weight")
        self.assertEqual(decision["recommended_weight"], 50)
        self.assertEqual(decision["recommended_rest_seconds"], 150)

    def test_previous_history_can_block_immediate_load_increase(self):
        decision = calculate_training_coach_decision(
            weight=50,
            reps=12,
            rir=2,
            is_failure=False,
            set_type="WORKING",
            set_number=1,
            current_sets=[
                {
                    "set_number": 1,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 12,
                    "rir": 2,
                    "reached_failure": False,
                },
            ],
            previous_sets=[
                {
                    "set_number": 1,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 14,
                    "rir": 3,
                    "reached_failure": False,
                },
            ],
        )

        self.assertEqual(decision["action"], "maintain_weight")
        self.assertEqual(decision["recommended_weight"], 50)
        self.assertEqual(decision["source"], "hybrid_local_training_coach")
        self.assertEqual(decision["context"]["history_signal"], "regressing")

    def test_pain_feedback_stops_exercise_even_with_good_performance(self):
        decision = calculate_training_coach_decision(
            weight=50,
            reps=12,
            rir=4,
            is_failure=False,
            notes="senti dor no ombro",
            set_type="WORKING",
        )

        self.assertEqual(decision["action"], "flag_pain_or_risk")
        self.assertTrue(decision["stop_exercise"])
        self.assertEqual(decision["exercise_status"], "complete")

    def test_no_pain_feedback_does_not_trigger_pain_guardrail(self):
        decision = calculate_training_coach_decision(
            weight=50,
            reps=12,
            rir=3,
            is_failure=False,
            notes="boa energia, sem dor, técnica estável",
            set_type="WORKING",
        )

        self.assertFalse(decision["guardrails"]["has_pain_or_risk"])
        self.assertNotEqual(decision["action"], "flag_pain_or_risk")

    def test_uses_exercise_target_range_instead_of_fixed_12_reps(self):
        decision = calculate_training_coach_decision(
            weight=80,
            reps=8,
            rir=2,
            is_failure=False,
            set_type="WORKING",
            target_min_reps=6,
            target_max_reps=8,
            target_rir=2,
            exercise_context={"movement_pattern": "SQUAT", "is_compound": True},
        )

        self.assertEqual(decision["action"], "increase_weight")
        self.assertEqual(decision["target_reps"], 8)
        self.assertEqual(decision["target_reps_label"], "6-8")
        self.assertGreater(decision["recommended_weight"], 80)

    @override_settings(
        OPENAI_API_KEY="test-key",
        AI_TRAINING_DECISION_PROVIDER="openai",
        AI_TRAINING_DECISION_MODEL="gpt-test",
    )
    @patch("recommendations.services.ai_training_decision_engine._request_openai_training_decision")
    def test_openai_can_take_next_set_decision_inside_guardrails(self, mock_request):
        mock_request.return_value = {
            "recommended_weight": 42.5,
            "target_reps": 8,
            "recommended_rest_seconds": 75,
            "next_set_type": "WARMUP",
            "exercise_status": "continue",
            "action": "continue_warmup",
            "reason": "A IA quer mais uma aproximação antes da série normal.",
            "guidance_title": "Mais um aquecimento",
            "guidance_message": "Sobe progressivamente sem gastar fadiga.",
            "confidence": "alta",
            "decision_basis": ["Histórico dos últimos treinos", "Aquecimento ainda distante da carga alvo"],
        }
        local_decision = {
            "recommended_weight": 50,
            "target_reps": 12,
            "recommended_rest_seconds": 90,
            "next_set_type": "WORKING",
            "exercise_status": "continue",
            "action": "prepare_working_set",
            "reason": "Local",
            "guidance_title": "Local",
            "guidance_message": "Local",
            "confidence": "média",
            "decision_basis": [],
        }

        decision = generate_ai_training_decision(local_decision, {"history_sets": []})

        self.assertEqual(decision["source"], "openai_training_decision")
        self.assertEqual(decision["llm_status"], "llm_enabled")
        self.assertEqual(decision["next_set_type"], "WARMUP")
        self.assertEqual(decision["recommended_weight"], 42.5)

    @override_settings(
        AI_TRAINING_DECISION_PROVIDER="ollama",
        OLLAMA_TRAINING_DECISION_MODEL="qwen3:8b",
    )
    @patch("recommendations.services.ai_training_decision_engine._request_ollama_training_decision")
    def test_ollama_can_take_next_set_decision(self, mock_request):
        mock_request.return_value = {
            "recommended_weight": "40",
            "target_reps": "10",
            "recommended_rest_seconds": 90,
            "next_set_type": "WORKING",
            "exercise_status": "continue",
            "action": "start_working_set",
            "reason": "Ollama decidiu começar trabalho com carga conservadora.",
            "guidance_title": "Começa a série normal",
            "guidance_message": "Usa uma carga controlada e confirma a resposta do músculo.",
            "confidence": "média",
            "decision_basis": ["Histórico recente", "Aquecimento suficiente"],
        }
        local_decision = {
            "recommended_weight": 37.5,
            "target_reps": 12,
            "recommended_rest_seconds": 90,
            "next_set_type": "WORKING",
            "exercise_status": "continue",
            "action": "prepare_working_set",
            "reason": "Local",
            "guidance_title": "Local",
            "guidance_message": "Local",
            "confidence": "média",
            "decision_basis": [],
        }

        decision = generate_ai_training_decision(local_decision, {"history_sets": []})

        self.assertEqual(decision["source"], "ollama_training_decision")
        self.assertEqual(decision["llm_status"], "llm_enabled")
        self.assertEqual(decision["model"], "qwen3:8b")
        self.assertEqual(decision["recommended_weight"], "40")

    @override_settings(
        AI_TRAINING_DECISION_PROVIDER="ollama",
        OLLAMA_TRAINING_DECISION_MODEL="qwen3:8b",
    )
    @patch("recommendations.services.ai_training_decision_engine._request_ollama_training_decision")
    def test_ollama_guardrail_keeps_warmup_load_from_becoming_working_set(self, mock_request):
        mock_request.return_value = {
            "recommended_weight": "40",
            "target_reps": "8",
            "recommended_rest_seconds": 75,
            "next_set_type": "WORKING",
            "exercise_status": "continue",
            "action": "start_working_set",
            "reason": "Ollama tentou começar trabalho cedo.",
            "guidance_title": "Começa trabalho",
            "guidance_message": "Usa a carga sugerida.",
            "confidence": "alta",
            "decision_basis": ["IA local"],
        }
        local_decision = {
            "recommended_weight": 40,
            "target_reps": 8,
            "recommended_rest_seconds": 75,
            "next_set_type": "WARMUP",
            "exercise_status": "continue",
            "action": "continue_warmup",
            "reason": "Local pede mais aquecimento.",
            "guidance_title": "Faz mais um aquecimento",
            "guidance_message": "Ainda nao esta na zona de trabalho.",
            "confidence": "média",
            "decision_basis": [],
        }

        decision = generate_ai_training_decision(local_decision, {"history_sets": []})

        self.assertEqual(decision["source"], "ollama_training_decision")
        self.assertEqual(decision["llm_status"], "llm_enabled")
        self.assertEqual(decision["next_set_type"], "WARMUP")
        self.assertTrue(decision["guardrail_applied"])
        self.assertEqual(decision["action"], "maintain_weight")

    @override_settings(
        AI_TRAINING_DECISION_PROVIDER="ollama",
        OLLAMA_TRAINING_DECISION_MODEL="qwen3:8b",
    )
    @patch("recommendations.services.ai_training_decision_engine._request_ollama_training_decision")
    def test_ollama_receives_compact_history_context(self, mock_request):
        mock_request.return_value = {
            "recommended_weight": "60",
            "target_reps": "12",
            "recommended_rest_seconds": 90,
            "next_set_type": "WORKING",
            "exercise_status": "continue",
            "action": "prepare_working_set",
            "reason": "Contexto compacto analisado.",
            "guidance_title": "Comeca trabalho",
            "guidance_message": "Usa a carga historica.",
            "confidence": "alta",
            "decision_basis": ["Histórico compacto"],
        }
        local_decision = {
            "recommended_weight": 60,
            "target_reps": 12,
            "recommended_rest_seconds": 90,
            "next_set_type": "WORKING",
            "exercise_status": "continue",
            "action": "prepare_working_set",
            "reason": "Local",
            "guidance_title": "Local",
            "guidance_message": "Local",
            "confidence": "média",
            "decision_basis": [],
            "context": {"history_summary": {"working_set_count": 30}},
        }
        history_sets = [
            {
                "workout_session": index,
                "set_number": 1,
                "set_type": "WORKING",
                "weight_used": 50 + index,
                "reps_completed": 12,
                "rir": 2,
                "reached_failure": False,
                "notes": "extra text that should not be sent to the LLM",
            }
            for index in range(25)
        ]

        generate_ai_training_decision(local_decision, {"history_sets": history_sets})

        context = mock_request.call_args.args[0]
        self.assertEqual(len(context["recent_history_sets"]), 25)
        self.assertEqual(context["recent_history_sets"][0]["weight"], 50)
        self.assertIn("notes", context["recent_history_sets"][0])


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

    def test_keeps_load_when_clean_work_is_too_small_to_progress(self):
        recommendation = calculate_exercise_progression(
            self.make_training_exercise(),
            [
                {
                    "set_number": 1,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 12,
                    "rir": 3,
                    "reached_failure": False,
                },
            ],
        )

        self.assertEqual(recommendation["action"], "maintain_load")
        self.assertEqual(recommendation["recommended_weight"], 50)
        self.assertEqual(recommendation["source"], "hybrid_local_workout_progression")
        self.assertEqual(recommendation["progression_context"]["completed_ratio"], 0.33)


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
