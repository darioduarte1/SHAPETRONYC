# =============================================================================
# tests.py
# -----------------------------------------------------------------------------
# Testes automáticos da app recommendations.
# Validam regras dos motores de decisão, progressão, feedback e coaching.
# Protegem o comportamento da IA local e das recomendações de treino.
# =============================================================================
from django.test import SimpleTestCase, override_settings
from types import SimpleNamespace
from unittest.mock import patch

from recommendations.services.progression_engine import calculate_next_set
from recommendations.services.ai_coach_engine import build_local_coach_summary
from recommendations.services.ai_training_decision_engine import generate_ai_training_decision
from recommendations.services.training_coach_engine import calculate_training_coach_decision
from recommendations.services.workout_progression_engine import calculate_exercise_progression


class ProgressionEngineTests(SimpleTestCase):
    def test_does_not_increase_without_registered_weight_scale(self):
        recommendation = calculate_next_set(weight=50, reps=12, rir=3)

        self.assertEqual(recommendation["recommended_weight"], 50)
        self.assertEqual(recommendation["target_reps"], 12)
        self.assertIn("escala", recommendation["guidance_title"].lower())

    def test_keeps_load_when_12_reps_are_normal_work(self):
        recommendation = calculate_next_set(weight=50, reps=12, rir=2)

        self.assertEqual(recommendation["recommended_weight"], 50)
        self.assertEqual(recommendation["target_reps"], 12)

    def test_reduces_load_when_failure_is_below_target_range(self):
        recommendation = calculate_next_set(weight=50, reps=9, rir=0, is_failure=True)

        self.assertEqual(recommendation["recommended_weight"], 46.0)
        self.assertEqual(recommendation["target_reps"], 12)


class TrainingCoachEngineTests(SimpleTestCase):
    def test_productive_failure_at_top_of_range_does_not_stop_exercise(self):
        decision = calculate_training_coach_decision(
            weight=36.6,
            reps=12,
            rir=None,
            is_failure=True,
            set_type="WORKING",
            current_sets=[
                {
                    "set_number": 1,
                    "set_type": "WORKING",
                    "weight_used": 36.6,
                    "reps_completed": 12,
                    "rir": 3,
                    "reached_failure": False,
                },
                {
                    "set_number": 2,
                    "set_type": "WORKING",
                    "weight_used": 36.6,
                    "reps_completed": 12,
                    "rir": None,
                    "reached_failure": True,
                },
            ],
            target_min_reps=10,
            target_max_reps=12,
            total_sets=3,
        )

        self.assertEqual(decision["context"]["failure_class"], "productive_failure")
        self.assertEqual(decision["action"], "maintain_or_small_backoff")
        self.assertEqual(decision["recommended_weight"], 34.5)
        self.assertEqual(decision["target_reps"], 12)
        self.assertFalse(decision["stop_exercise"])
        self.assertEqual(decision["exercise_status"], "continue")

    def test_acceptable_failure_inside_range_continues_with_caution(self):
        decision = calculate_training_coach_decision(
            weight=50,
            reps=10,
            rir=None,
            is_failure=True,
            set_type="WORKING",
            current_sets=[
                {
                    "set_number": 1,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 8,
                    "rir": None,
                    "reached_failure": True,
                },
            ],
            total_sets=3,
        )

        self.assertEqual(decision["context"]["failure_class"], "acceptable_failure")
        self.assertEqual(decision["action"], "maintain_or_small_backoff")
        self.assertEqual(decision["recommended_weight"], 47.5)
        self.assertEqual(decision["target_reps"], 12)
        self.assertFalse(decision["stop_exercise"])
        self.assertEqual(decision["next_set_type"], "WORKING")

    def test_bad_failure_below_range_reduces_load_or_stops(self):
        decision = calculate_training_coach_decision(
            weight=50,
            reps=8,
            rir=None,
            is_failure=True,
            set_type="WORKING",
            current_sets=[
                {
                    "set_number": 1,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 8,
                    "rir": None,
                    "reached_failure": True,
                },
            ],
            total_sets=3,
        )

        self.assertEqual(decision["context"]["failure_class"], "bad_failure")
        self.assertEqual(decision["action"], "decrease_weight")
        self.assertEqual(decision["recommended_weight"], 44.0)

    def test_decision_includes_structured_engine_state_and_scores(self):
        decision = calculate_training_coach_decision(
            weight=50,
            reps=12,
            rir=2,
            is_failure=False,
            set_type="WORKING",
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
            total_sets=3,
            exercise_context={
                "exercise_name": "Chest Press Machine",
                "movement_pattern": "HORIZONTAL_PUSH",
                "equipment": "Machine",
                "is_compound": True,
            },
            session_context={"total_sets_completed_in_session": 4},
        )

        self.assertIn(decision["exercise_state"], {"CONTINUE", "FINAL_SET", "ADJUST_LOAD"})
        self.assertEqual(decision["valid_working_sets"], 1)
        self.assertEqual(decision["minimum_valid_sets"], 3)
        self.assertEqual(decision["context"]["exercise_priority"], "PRIMARY")
        self.assertEqual(decision["context"]["exercise_type"], "COMPOUND")
        self.assertIn("local_fatigue_score", decision)
        self.assertIn("global_fatigue_score", decision)
        self.assertIn("stimulus_score", decision)
        self.assertIn("fatigue_cost", decision)
        self.assertIn("confidence_score", decision)

    def test_primary_exercise_can_add_fourth_set_after_three_strong_valid_sets(self):
        current_sets = [
            {
                "set_number": 1,
                "set_type": "WORKING",
                "weight_used": 50,
                "reps_completed": 12,
                "rir": 3,
                "reached_failure": False,
            },
            {
                "set_number": 2,
                "set_type": "WORKING",
                "weight_used": 50,
                "reps_completed": 12,
                "rir": 2,
                "reached_failure": False,
            },
            {
                "set_number": 3,
                "set_type": "WORKING",
                "weight_used": 50,
                "reps_completed": 12,
                "rir": 2,
                "reached_failure": False,
            },
        ]

        decision = calculate_training_coach_decision(
            weight=50,
            reps=12,
            rir=2,
            is_failure=False,
            set_type="WORKING",
            current_sets=current_sets,
            total_sets=3,
            exercise_context={
                "exercise_name": "Chest Press Machine",
                "movement_pattern": "HORIZONTAL_PUSH",
                "equipment": "Machine",
                "is_compound": True,
            },
        )

        self.assertEqual(decision["exercise_state"], "ADD_VOLUME")
        self.assertTrue(decision["add_set"])
        self.assertEqual(decision["maximum_allowed_sets"], 4)

    def test_finisher_ends_after_three_sets_without_clear_need_for_extra_volume(self):
        current_sets = [
            {
                "set_number": index,
                "set_type": "WORKING",
                "weight_used": 20,
                "reps_completed": 12,
                "rir": 2,
                "reached_failure": False,
            }
            for index in range(1, 4)
        ]

        decision = calculate_training_coach_decision(
            weight=20,
            reps=12,
            rir=2,
            is_failure=False,
            set_type="WORKING",
            current_sets=current_sets,
            total_sets=3,
            exercise_context={
                "exercise_name": "Cable Fly",
                "movement_pattern": "ISOLATION",
                "equipment": "Cable",
                "is_compound": False,
                "exercise_order_in_workout": 5,
            },
        )

        self.assertEqual(decision["context"]["exercise_priority"], "FINISHER")
        self.assertEqual(decision["exercise_state"], "END_EXERCISE")
        self.assertFalse(decision["add_set"])

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
                    "reps_completed": 8,
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

        self.assertEqual(decision["action"], "decrease_weight")
        self.assertEqual(decision["next_set_type"], "WORKING")
        self.assertEqual(decision["exercise_status"], "continue")
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
                    "reps_completed": 8,
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
            rir=3,
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
            rir=3,
            is_failure=False,
            set_type="WORKING",
            target_min_reps=6,
            target_max_reps=8,
            target_rir=2,
            exercise_context={
                "movement_pattern": "SQUAT",
                "is_compound": True,
                "main_weight_options": [80, 85],
                "micro_weight_options": [],
            },
        )

        self.assertEqual(decision["action"], "increase_weight")
        self.assertEqual(decision["target_reps"], 8)
        self.assertEqual(decision["target_reps_label"], "6-8")
        self.assertGreater(decision["recommended_weight"], 80)

    def test_uses_machine_weight_scale_for_next_working_set(self):
        decision = calculate_training_coach_decision(
            weight=50,
            reps=12,
            rir=3,
            is_failure=False,
            set_type="WORKING",
            exercise_context={
                "equipment": "Machine",
                "main_weight_options": [40, 50, 60],
                "micro_weight_options": [1, 2, 3],
            },
        )

        self.assertEqual(decision["action"], "increase_weight")
        self.assertEqual(decision["recommended_weight"], 51)

    def test_machine_jump_above_10_percent_requires_rir_4(self):
        decision = calculate_training_coach_decision(
            weight=46,
            reps=12,
            rir=3,
            is_failure=False,
            set_type="WORKING",
            exercise_context={
                "equipment": "Machine",
                "main_weight_options": [46, 52],
                "micro_weight_options": [],
            },
        )

        self.assertEqual(decision["action"], "maintain_weight")
        self.assertEqual(decision["recommended_weight"], 46)

        strong_decision = calculate_training_coach_decision(
            weight=46,
            reps=12,
            rir=4,
            is_failure=False,
            set_type="WORKING",
            exercise_context={
                "equipment": "Machine",
                "main_weight_options": [46, 52],
                "micro_weight_options": [],
            },
        )

        self.assertEqual(strong_decision["action"], "increase_weight")
        self.assertEqual(strong_decision["recommended_weight"], 52)

    def test_machine_does_not_increase_without_registered_next_weight(self):
        decision = calculate_training_coach_decision(
            weight=46,
            reps=12,
            rir=4,
            is_failure=False,
            set_type="WORKING",
            exercise_context={
                "equipment": "Machine",
                "main_weight_options": [46],
                "micro_weight_options": [],
            },
        )

        self.assertEqual(decision["action"], "maintain_weight")
        self.assertEqual(decision["recommended_weight"], 46)

    def test_requests_weight_scale_when_performance_allows_possible_increase(self):
        decision = calculate_training_coach_decision(
            weight=50,
            reps=12,
            rir=4,
            is_failure=False,
            set_type="WORKING",
            exercise_context={
                "equipment": "Machine",
                "main_weight_options": [],
                "micro_weight_options": [],
            },
        )

        self.assertEqual(decision["action"], "maintain_weight")
        self.assertEqual(decision["recommended_weight"], 50)
        self.assertIn("escala", decision["guidance_title"].lower())
        self.assertIn("escala de pesos", " ".join(decision["decision_basis"]).lower())

    def test_recent_failure_at_next_weight_blocks_increase(self):
        decision = calculate_training_coach_decision(
            weight=46,
            reps=12,
            rir=3,
            is_failure=False,
            set_type="WORKING",
            exercise_context={
                "equipment": "Machine",
                "main_weight_options": [46, 47],
                "micro_weight_options": [],
            },
            history_sets=[
                {
                    "set_number": 1,
                    "set_type": "WORKING",
                    "weight_used": 47,
                    "reps_completed": 8,
                    "rir": 0,
                    "reached_failure": True,
                }
            ],
        )

        self.assertEqual(decision["action"], "maintain_weight")
        self.assertEqual(decision["recommended_weight"], 46)


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
        self.assertEqual(decision["recommended_weight"], 37.5)
        self.assertTrue(decision["guardrail_applied"])
        self.assertIn("12 reps", decision["guardrail_reason"])

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
            exercise=SimpleNamespace(
                name="Bench Press",
                main_weight_options=[],
                micro_weight_options=[],
            ),
            sets=3,
            target_rir=2,
        )

    def test_increases_load_for_next_workout_after_clean_sets(self):
        training_exercise = self.make_training_exercise()
        training_exercise.exercise.main_weight_options = [50, 52.5]

        recommendation = calculate_exercise_progression(
            training_exercise,
            [
                {
                    "set_number": 1,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 12,
                    "rir": 3,
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
                {
                    "set_number": 3,
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

    def test_next_workout_progression_uses_machine_weight_scale(self):
        training_exercise = self.make_training_exercise()
        training_exercise.exercise.main_weight_options = [40, 50, 60]
        training_exercise.exercise.micro_weight_options = [1, 2, 3]

        recommendation = calculate_exercise_progression(
            training_exercise,
            [
                {
                    "set_number": 1,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 12,
                    "rir": 3,
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
                {
                    "set_number": 3,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 12,
                    "rir": 3,
                    "reached_failure": False,
                },
            ],
        )

        self.assertEqual(recommendation["action"], "increase_load")
        self.assertEqual(recommendation["recommended_weight"], 51)

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

    def test_next_workout_requests_scale_when_clean_sets_have_no_registered_weights(self):
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
                {
                    "set_number": 2,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 12,
                    "rir": 3,
                    "reached_failure": False,
                },
                {
                    "set_number": 3,
                    "set_type": "WORKING",
                    "weight_used": 50,
                    "reps_completed": 12,
                    "rir": 3,
                    "reached_failure": False,
                },
            ],
        )

        self.assertEqual(recommendation["action"], "maintain_load")
        self.assertIn("escala", recommendation["title"].lower())
        self.assertIn("escala de pesos", " ".join(recommendation["decision_basis"]).lower())


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
