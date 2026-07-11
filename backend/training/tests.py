# =============================================================================
# tests.py
# -----------------------------------------------------------------------------
# Testes automáticos da app training.
# Validam sessões, dashboards, calibração, escalas, blocos, memória, feedback e plano adaptativo.
# Protegem a camada central que liga execução real e decisões futuras.
# =============================================================================
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import UserProfile
from exercises.models import Exercise
from progression.models import SetLog
from recommendations.services.workout_progression_engine import calculate_workout_progression
from training.models import (
    AdaptivePlanDecision,
    AthleteTrainingMemory,
    ExerciseCalibration,
    TrainingBlock,
    TrainingProgram,
    TrainingWorkout,
    TrainingWorkoutExercise,
    UserExerciseWeightScale,
    WorkoutSession,
)
from training.services.athlete_dashboard import build_athlete_dashboard
from training.services.adaptive_plan import build_adaptive_plan
from training.services.training_memory import refresh_training_memory
from training.services.training_blocks import build_training_block
from training.services.weekly_feedback import build_weekly_feedback


class AthleteDashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="dashboard_user")
        self.profile = UserProfile.objects.create(
            user=self.user,
            gender="MALE",
            age=34,
            height_cm=172,
            weight_kg=72,
            goal="HYPERTROPHY",
            level="INTERMEDIATE",
            training_experience="ONE_TO_THREE",
            days_per_week=5,
        )
        self.program = TrainingProgram.objects.create(
            user=self.user,
            name="Dashboard Program",
            goal="HYPERTROPHY",
            level="INTERMEDIATE",
            days_per_week=5,
        )
        self.workout = TrainingWorkout.objects.create(
            program=self.program,
            name="Push",
            order=1,
        )
        self.exercise = Exercise.objects.create(
            name="Chest Press Machine",
            muscle_group="Chest",
            equipment="Machine",
            movement_pattern="HORIZONTAL_PUSH",
            is_compound=True,
        )
        self.training_exercise = TrainingWorkoutExercise.objects.create(
            workout=self.workout,
            exercise=self.exercise,
            order=1,
            sets=3,
            target_min_reps=10,
            target_max_reps=12,
            target_rir=2,
        )

    def create_completed_session(self, days_ago, weight, reps=12, rir=2, reached_failure=False):
        completed_at = timezone.now() - timedelta(days=days_ago)
        session = WorkoutSession.objects.create(
            user=self.user,
            workout=self.workout,
            status="COMPLETED",
            completed_at=completed_at,
        )
        SetLog.objects.create(
            user=self.user,
            workout_session=session,
            training_exercise=self.training_exercise,
            exercise=self.exercise,
            set_number=1,
            set_type="WORKING",
            planned_weight=None,
            weight_used=weight,
            target_min_reps=10,
            target_max_reps=12,
            reps_completed=reps,
            rir=rir,
            reached_failure=reached_failure,
        )

        return session

    def test_new_exercise_history_requires_calibration(self):
        self.exercise.main_weight_options = [20, 30, 40]
        self.exercise.micro_weight_options = [1, 2]
        self.exercise.save(update_fields=["main_weight_options", "micro_weight_options"])
        session = WorkoutSession.objects.create(
            user=self.user,
            workout=self.workout,
            status="IN_PROGRESS",
        )
        client = APIClient()

        response = client.get(
            "/api/progression/exercise-history/",
            {
                "profile_id": self.profile.id,
                "exercise_id": self.exercise.id,
                "training_exercise_id": self.training_exercise.id,
                "session_id": session.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["calibration"]["needs_calibration"])
        self.assertEqual(response.data["calibration"]["reason"], "scale_required")
        self.assertFalse(response.data["calibration"]["scale_configured"])
        self.assertEqual(response.data["calibration"]["scale"]["main_weight_options"], [])
        self.assertEqual(response.data["calibration"]["next_step"]["action"], "fill_scale")

    def test_weight_scale_endpoint_stores_scale_for_current_athlete_only(self):
        other_user = User.objects.create_user(username="other_scale_user")
        other_profile = UserProfile.objects.create(
            user=other_user,
            gender="MALE",
            age=30,
            height_cm=180,
            weight_kg=80,
            goal="HYPERTROPHY",
            level="BEGINNER",
            training_experience="LESS_THAN_ONE",
            days_per_week=3,
        )
        TrainingProgram.objects.create(
            user=other_user,
            name="Other Program",
            goal="HYPERTROPHY",
            level="BEGINNER",
            days_per_week=3,
        )
        client = APIClient()

        response = client.patch(
            f"/api/training/exercise-weight-scale/{self.profile.id}/{self.training_exercise.id}/",
            {
                "main_weight_options": [20, 30, 40],
                "micro_weight_options": [1, 2],
            },
            format="json",
        )
        own_history = client.get(
            "/api/progression/exercise-history/",
            {
                "profile_id": self.profile.id,
                "exercise_id": self.exercise.id,
                "training_exercise_id": self.training_exercise.id,
            },
        )
        other_history = client.get(
            "/api/progression/exercise-history/",
            {
                "profile_id": other_profile.id,
                "exercise_id": self.exercise.id,
                "training_exercise_id": self.training_exercise.id,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["main_weight_options"], [20.0, 30.0, 40.0])
        self.assertTrue(own_history.data["calibration"]["scale_configured"])
        self.assertFalse(other_history.data["calibration"]["scale_configured"])

    def test_calibration_endpoint_requires_scale_before_storing_baseline(self):
        client = APIClient()

        response = client.post(
            "/api/training/exercise-calibration/",
            {
                "profile_id": self.profile.id,
                "training_exercise_id": self.training_exercise.id,
                "weight_used": 40,
                "result_color": "orange",
                "rir": 3,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["reason"], "scale_required")
        self.assertEqual(ExerciseCalibration.objects.count(), 0)

    def test_working_set_api_is_blocked_until_exercise_is_calibrated(self):
        session = WorkoutSession.objects.create(
            user=self.user,
            workout=self.workout,
            status="IN_PROGRESS",
        )
        client = APIClient()

        response = client.post(
            "/api/progression/set-logs/",
            {
                "user": self.user.id,
                "workout_session": session.id,
                "training_exercise": self.training_exercise.id,
                "exercise": self.exercise.id,
                "set_number": 1,
                "set_type": "WORKING",
                "weight_used": 40,
                "target_min_reps": 10,
                "target_max_reps": 12,
                "reps_completed": 12,
                "rir": 2,
                "reached_failure": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("calibration", response.data)
        self.assertEqual(response.data["reason"][0], "scale_required")

    def test_calibrated_exercise_unlocks_initial_recommended_sets(self):
        UserExerciseWeightScale.objects.create(
            user=self.user,
            exercise=self.exercise,
            main_weight_options=[20, 30, 40, 50],
            micro_weight_options=[1, 2],
        )
        client = APIClient()

        first_response = client.post(
            "/api/training/exercise-calibration/",
            {
                "profile_id": self.profile.id,
                "training_exercise_id": self.training_exercise.id,
                "weight_used": 40,
                "result_color": "green",
                "rir": 0,
                "reached_failure": True,
            },
            format="json",
        )
        second_response = client.post(
            "/api/training/exercise-calibration/",
            {
                "profile_id": self.profile.id,
                "training_exercise_id": self.training_exercise.id,
                "weight_used": first_response.data["next_step"]["recommended_weight"],
                "result_color": "orange",
                "rir": 0,
                "reached_failure": True,
            },
            format="json",
        )
        calibration_response = client.post(
            "/api/training/exercise-calibration/",
            {
                "profile_id": self.profile.id,
                "training_exercise_id": self.training_exercise.id,
                "weight_used": second_response.data["next_step"]["recommended_weight"],
                "result_color": "orange",
                "rir": 0,
                "reached_failure": True,
            },
            format="json",
        )
        session = WorkoutSession.objects.create(
            user=self.user,
            workout=self.workout,
            status="IN_PROGRESS",
        )
        history_response = client.get(
            "/api/progression/exercise-history/",
            {
                "profile_id": self.profile.id,
                "exercise_id": self.exercise.id,
                "training_exercise_id": self.training_exercise.id,
                "session_id": session.id,
            },
        )

        self.assertEqual(calibration_response.status_code, 200)
        self.assertFalse(calibration_response.data["needs_calibration"])
        self.assertEqual(calibration_response.data["set_count"], 3)
        self.assertEqual(calibration_response.data["next_step"]["action"], "calibration_complete")
        self.assertFalse(history_response.data["calibration"]["needs_calibration"])
        self.assertEqual(len(history_response.data["recommended_sets"]), 2)
        self.assertEqual(history_response.data["recommended_sets"][0]["set_type"], "WARMUP")
        self.assertEqual(history_response.data["recommended_sets"][1]["set_type"], "WORKING")
        self.assertEqual(history_response.data["recommended_sets"][1]["source"], "exercise_calibration")

    def test_dashboard_summarizes_volume_progression_and_watchlist(self):
        self.create_completed_session(days_ago=14, weight=50, reps=12, rir=3)
        self.create_completed_session(days_ago=7, weight=55, reps=12, rir=2)
        self.create_completed_session(days_ago=1, weight=55, reps=8, rir=None, reached_failure=True)

        dashboard = build_athlete_dashboard(self.profile)

        self.assertEqual(dashboard["summary"]["completed_workouts"], 3)
        self.assertEqual(dashboard["summary"]["total_sets"], 3)
        self.assertEqual(dashboard["summary"]["failure_count"], 1)
        self.assertEqual(dashboard["summary"]["total_volume"], 1700.0)
        self.assertEqual(len(dashboard["recent_sessions"]), 3)
        self.assertEqual(dashboard["top_progressing_exercises"][0]["exercise_name"], "Chest Press Machine")
        self.assertEqual(dashboard["top_progressing_exercises"][0]["load_change"], 5.0)
        self.assertEqual(dashboard["watchlist_exercises"][0]["exercise_name"], "Chest Press Machine")
        self.assertIn("falha", dashboard["watchlist_exercises"][0]["reason"])

    def test_dashboard_includes_experimental_calibration_data(self):
        completed_at = timezone.now()
        session = WorkoutSession.objects.create(
            user=self.user,
            workout=self.workout,
            status="COMPLETED",
            completed_at=completed_at,
        )
        WorkoutSession.objects.filter(id=session.id).update(
            started_at=completed_at - timedelta(minutes=12),
        )
        calibration = ExerciseCalibration.objects.create(
            user=self.user,
            exercise=self.exercise,
            status="CALIBRATED",
            estimated_working_weight=32,
            confidence="média",
            calibration_sets=[
                {"weight_used": 24, "reps_completed": 15, "reached_failure": True},
                {"weight_used": 30, "reps_completed": 13, "reached_failure": True},
                {"weight_used": 32, "reps_completed": 12, "reached_failure": True},
            ],
        )
        ExerciseCalibration.objects.filter(id=calibration.id).update(
            updated_at=completed_at - timedelta(minutes=2),
        )

        dashboard = build_athlete_dashboard(self.profile)

        self.assertEqual(dashboard["summary"]["completed_workouts"], 1)
        self.assertEqual(dashboard["summary"]["total_sets"], 3)
        self.assertEqual(dashboard["summary"]["calibration_sets"], 3)
        self.assertEqual(dashboard["summary"]["calibrated_exercises"], 1)
        self.assertEqual(dashboard["summary"]["total_volume"], 1134.0)
        self.assertEqual(dashboard["recent_sessions"][0]["volume"], 1134.0)
        self.assertEqual(dashboard["recent_sessions"][0]["calibration_sets"], 3)
        self.assertEqual(dashboard["calibrated_exercises"][0]["estimated_working_weight"], 32.0)

    def test_workout_progression_uses_calibrated_weight_without_normal_sets(self):
        calibration = ExerciseCalibration.objects.create(
            user=self.user,
            exercise=self.exercise,
            status="CALIBRATED",
            estimated_working_weight=32,
            confidence="média",
            calibration_sets=[
                {"weight_used": 32, "reps_completed": 12, "reached_failure": True},
            ],
        )

        progression = calculate_workout_progression(self.workout, [], [calibration])
        recommendation = progression["recommendations"][0]

        self.assertEqual(recommendation["action"], "use_calibrated_load")
        self.assertEqual(recommendation["recommended_weight"], 32)
        self.assertEqual(recommendation["confidence"], "média")
        self.assertIn("calibrado", recommendation["title"].lower())

    def test_workout_progression_uses_calibration_scale_snapshot(self):
        self.exercise.main_weight_options = [27.3]
        self.exercise.save(update_fields=["main_weight_options"])
        calibration = ExerciseCalibration.objects.create(
            user=self.user,
            exercise=self.exercise,
            status="CALIBRATED",
            estimated_working_weight=29.6,
            confidence="alta",
            scale_snapshot={
                "main_weight_options": [27.3, 29.6],
                "micro_weight_options": [],
            },
            calibration_sets=[
                {"weight_used": 29.6, "reps_completed": 12, "reached_failure": True},
            ],
        )

        progression = calculate_workout_progression(self.workout, [], [calibration])
        recommendation = progression["recommendations"][0]

        self.assertEqual(recommendation["action"], "use_calibrated_load")
        self.assertEqual(recommendation["recommended_weight"], 29.6)

    def test_dashboard_endpoint_returns_profile_dashboard(self):
        self.create_completed_session(days_ago=1, weight=50, reps=12, rir=2)
        client = APIClient()

        response = client.get(f"/api/training/dashboard/{self.profile.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile_id"], self.profile.id)
        self.assertEqual(response.data["summary"]["completed_workouts"], 1)

    def test_training_memory_persists_progression_and_watchlist_patterns(self):
        self.create_completed_session(days_ago=21, weight=50, reps=12, rir=3)
        self.create_completed_session(days_ago=14, weight=55, reps=12, rir=2)
        self.create_completed_session(days_ago=7, weight=57.5, reps=12, rir=2)

        memories = refresh_training_memory(self.profile)

        self.assertEqual(AthleteTrainingMemory.objects.count(), 1)
        self.assertEqual(memories[0]["memory_type"], "PROGRESSION")
        self.assertIn("está a progredir", memories[0]["title"])

        self.create_completed_session(days_ago=1, weight=57.5, reps=8, rir=None, reached_failure=True)
        memories = refresh_training_memory(self.profile)
        memory_types = {memory["memory_type"] for memory in memories}

        self.assertIn("WATCHLIST", memory_types)
        self.assertTrue(
            AthleteTrainingMemory.objects.filter(
                user=self.user,
                exercise=self.exercise,
                memory_type="WATCHLIST",
            ).exists()
        )

    def test_dashboard_includes_training_memories(self):
        self.create_completed_session(days_ago=14, weight=50, reps=12, rir=3)
        self.create_completed_session(days_ago=7, weight=55, reps=12, rir=2)
        self.create_completed_session(days_ago=1, weight=57.5, reps=12, rir=2)

        dashboard = build_athlete_dashboard(self.profile)

        self.assertEqual(dashboard["training_memories"][0]["memory_type"], "PROGRESSION")
        self.assertEqual(dashboard["training_memories"][0]["exercise_name"], "Chest Press Machine")

    def test_adaptive_plan_recommends_progression_from_training_memory(self):
        self.create_completed_session(days_ago=14, weight=50, reps=12, rir=3)
        self.create_completed_session(days_ago=7, weight=55, reps=12, rir=2)
        self.create_completed_session(days_ago=1, weight=57.5, reps=12, rir=2)

        adaptive_plan = build_adaptive_plan(self.profile)
        recommendation = adaptive_plan["recommendations"][0]

        self.assertEqual(recommendation["action"], "progress_load")
        self.assertEqual(recommendation["load_adjustment"], 2.5)
        self.assertEqual(recommendation["recommended_sets"], self.training_exercise.sets)

    def test_adaptive_plan_protects_recovery_from_watchlist_memory(self):
        self.create_completed_session(days_ago=14, weight=55, reps=12, rir=2)
        self.create_completed_session(days_ago=7, weight=55, reps=8, rir=None, reached_failure=True)
        self.create_completed_session(days_ago=1, weight=55, reps=8, rir=None, reached_failure=True)

        adaptive_plan = build_adaptive_plan(self.profile)
        recommendation = adaptive_plan["recommendations"][0]

        self.assertEqual(recommendation["action"], "protect_recovery")
        self.assertEqual(recommendation["priority"], "high")
        self.assertEqual(recommendation["recommended_sets"], self.training_exercise.sets - 1)
        self.assertEqual(recommendation["recommended_target_rir"], 3)

    def test_adaptive_plan_endpoint_returns_recommendations(self):
        self.create_completed_session(days_ago=14, weight=50, reps=12, rir=3)
        self.create_completed_session(days_ago=7, weight=55, reps=12, rir=2)
        self.create_completed_session(days_ago=1, weight=57.5, reps=12, rir=2)
        client = APIClient()

        response = client.get(f"/api/training/adaptive-plan/{self.profile.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile_id"], self.profile.id)
        self.assertEqual(response.data["recommendations"][0]["action"], "progress_load")

    def test_apply_adaptive_plan_recommendation_updates_plan_and_records_decision(self):
        self.training_exercise.target_rir = 1
        self.training_exercise.save(update_fields=["target_rir"])
        self.create_completed_session(days_ago=14, weight=55, reps=12, rir=2)
        self.create_completed_session(days_ago=7, weight=55, reps=8, rir=None, reached_failure=True)
        self.create_completed_session(days_ago=1, weight=55, reps=8, rir=None, reached_failure=True)
        client = APIClient()

        response = client.post(
            "/api/training/adaptive-plan/apply/",
            {
                "profile_id": self.profile.id,
                "training_exercise_id": self.training_exercise.id,
                "status": "APPLIED",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.training_exercise.refresh_from_db()
        self.assertEqual(self.training_exercise.sets, 2)
        self.assertEqual(self.training_exercise.target_rir, 3)
        self.assertEqual(AdaptivePlanDecision.objects.count(), 1)
        self.assertEqual(AdaptivePlanDecision.objects.first().status, "APPLIED")

    def test_defer_adaptive_plan_recommendation_records_without_updating_plan(self):
        self.create_completed_session(days_ago=14, weight=50, reps=12, rir=3)
        self.create_completed_session(days_ago=7, weight=55, reps=12, rir=2)
        self.create_completed_session(days_ago=1, weight=57.5, reps=12, rir=2)
        client = APIClient()

        response = client.post(
            "/api/training/adaptive-plan/apply/",
            {
                "profile_id": self.profile.id,
                "training_exercise_id": self.training_exercise.id,
                "status": "DEFERRED",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.training_exercise.refresh_from_db()
        self.assertEqual(self.training_exercise.sets, 3)
        self.assertEqual(self.training_exercise.target_rir, 2)
        self.assertEqual(AdaptivePlanDecision.objects.count(), 1)
        self.assertEqual(AdaptivePlanDecision.objects.first().status, "DEFERRED")

    def test_adaptive_decision_endpoint_lists_recent_decisions(self):
        self.create_completed_session(days_ago=14, weight=50, reps=12, rir=3)
        self.create_completed_session(days_ago=7, weight=55, reps=12, rir=2)
        self.create_completed_session(days_ago=1, weight=57.5, reps=12, rir=2)
        client = APIClient()
        client.post(
            "/api/training/adaptive-plan/apply/",
            {
                "profile_id": self.profile.id,
                "training_exercise_id": self.training_exercise.id,
                "status": "APPLIED",
            },
            format="json",
        )

        response = client.get(f"/api/training/adaptive-plan/decisions/{self.profile.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["decisions"][0]["action"], "progress_load")

    def test_weekly_feedback_recommends_deload_from_repeated_recovery_signals(self):
        self.create_completed_session(days_ago=21, weight=55, reps=12, rir=2)
        self.create_completed_session(days_ago=14, weight=55, reps=8, rir=None, reached_failure=True)
        self.create_completed_session(days_ago=7, weight=55, reps=8, rir=None, reached_failure=True)
        self.create_completed_session(days_ago=1, weight=52.5, reps=8, rir=None, reached_failure=True)

        feedback = build_weekly_feedback(self.profile)

        self.assertEqual(feedback["status"], "deload_recommended")
        self.assertTrue(feedback["deload"]["recommended"])
        self.assertEqual(feedback["deload"]["volume_multiplier"], 0.7)
        self.assertEqual(feedback["deload"]["target_rir"], 3)
        self.assertIn("falhas recentes acumuladas", feedback["deload"]["reasons"])

    def test_weekly_feedback_marks_progressing_when_no_recovery_signals(self):
        self.create_completed_session(days_ago=21, weight=50, reps=12, rir=3)
        self.create_completed_session(days_ago=14, weight=52.5, reps=12, rir=2)
        self.create_completed_session(days_ago=7, weight=55, reps=12, rir=2)
        self.create_completed_session(days_ago=1, weight=57.5, reps=12, rir=2)

        feedback = build_weekly_feedback(self.profile)

        self.assertEqual(feedback["status"], "progressing")
        self.assertFalse(feedback["deload"]["recommended"])
        self.assertEqual(feedback["signals"]["recent_failure_count"], 0)

    def test_weekly_feedback_ignores_calibration_failure_sets_for_deload(self):
        completed_at = timezone.now()
        session = WorkoutSession.objects.create(
            user=self.user,
            workout=self.workout,
            status="COMPLETED",
            completed_at=completed_at,
        )
        WorkoutSession.objects.filter(id=session.id).update(
            started_at=completed_at - timedelta(minutes=12),
        )
        calibration = ExerciseCalibration.objects.create(
            user=self.user,
            exercise=self.exercise,
            status="CALIBRATED",
            estimated_working_weight=29.6,
            confidence="alta",
            calibration_sets=[
                {"weight_used": 27.3, "reps_completed": 15, "reached_failure": True},
                {"weight_used": 29.6, "reps_completed": 13, "reached_failure": True},
                {"weight_used": 29.6, "reps_completed": 12, "reached_failure": True},
            ],
        )
        ExerciseCalibration.objects.filter(id=calibration.id).update(
            updated_at=completed_at - timedelta(minutes=2),
        )

        feedback = build_weekly_feedback(self.profile)

        self.assertEqual(feedback["signals"]["recent_failure_count"], 0)
        self.assertEqual(feedback["status"], "progressing")
        self.assertFalse(feedback["deload"]["recommended"])

    def test_weekly_feedback_endpoint_returns_deload_state(self):
        self.create_completed_session(days_ago=14, weight=55, reps=12, rir=2)
        self.create_completed_session(days_ago=7, weight=55, reps=8, rir=None, reached_failure=True)
        self.create_completed_session(days_ago=1, weight=55, reps=8, rir=None, reached_failure=True)
        client = APIClient()

        response = client.get(f"/api/training/weekly-feedback/{self.profile.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile_id"], self.profile.id)
        self.assertTrue(response.data["deload"]["recommended"])

    def test_training_block_builds_active_block_from_recent_sessions(self):
        self.create_completed_session(days_ago=21, weight=50, reps=12, rir=3)
        self.create_completed_session(days_ago=14, weight=52.5, reps=12, rir=2)
        self.create_completed_session(days_ago=7, weight=55, reps=12, rir=2)
        self.create_completed_session(days_ago=1, weight=57.5, reps=12, rir=2)

        block = build_training_block(self.profile)

        self.assertEqual(block["block"]["status"], "ACTIVE")
        self.assertEqual(block["block"]["phase"], "BUILD")
        self.assertEqual(block["summary"]["completed_sessions"], 4)
        self.assertEqual(TrainingBlock.objects.count(), 1)
        self.assertEqual(TrainingBlock.objects.first().phase, "BUILD")

    def test_training_block_switches_to_deload_phase_when_feedback_requires_it(self):
        self.create_completed_session(days_ago=21, weight=55, reps=12, rir=2)
        self.create_completed_session(days_ago=14, weight=55, reps=8, rir=None, reached_failure=True)
        self.create_completed_session(days_ago=7, weight=55, reps=8, rir=None, reached_failure=True)
        self.create_completed_session(days_ago=1, weight=52.5, reps=8, rir=None, reached_failure=True)

        block = build_training_block(self.profile)

        self.assertEqual(block["block"]["phase"], "DELOAD")
        self.assertEqual(block["summary"]["weekly_feedback_status"], "deload_recommended")
        self.assertTrue(block["weekly_feedback"]["deload"]["recommended"])

    def test_training_block_endpoint_returns_history(self):
        self.create_completed_session(days_ago=14, weight=50, reps=12, rir=3)
        self.create_completed_session(days_ago=7, weight=52.5, reps=12, rir=2)
        self.create_completed_session(days_ago=1, weight=55, reps=12, rir=2)
        client = APIClient()

        response = client.get(f"/api/training/training-blocks/{self.profile.id}/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["profile_id"], self.profile.id)
        self.assertEqual(response.data["block"]["status"], "ACTIVE")
        self.assertEqual(len(response.data["history"]), 1)

    def test_exercise_substitution_options_are_limited_to_same_muscle_group(self):
        Exercise.objects.create(
            name="Smith Machine Bench Press",
            localized_name="Supino no Smith (Máquina)",
            muscle_group="Chest",
            equipment="Machine",
            movement_pattern="HORIZONTAL_PUSH",
            is_compound=True,
        )
        Exercise.objects.create(
            name="Leg Press Test",
            localized_name="Leg Press",
            muscle_group="Quadriceps",
            equipment="Machine",
            movement_pattern="SQUAT",
            is_compound=True,
        )
        client = APIClient()

        response = client.get(f"/api/training/exercise-substitutions/{self.training_exercise.id}/")

        self.assertEqual(response.status_code, 200)
        option_names = {option["name"] for option in response.data["options"]}
        self.assertIn("Smith Machine Bench Press", option_names)
        self.assertNotIn("Leg Press Test", option_names)

    def test_replace_training_exercise_accepts_same_muscle_group(self):
        replacement = Exercise.objects.create(
            name="Smith Machine Bench Press",
            localized_name="Supino no Smith (Máquina)",
            muscle_group="Chest",
            equipment="Machine",
            movement_pattern="HORIZONTAL_PUSH",
            is_compound=True,
        )
        client = APIClient()

        response = client.post(
            "/api/training/replace-exercise/",
            {
                "training_exercise_id": self.training_exercise.id,
                "replacement_exercise_id": replacement.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.training_exercise.refresh_from_db()
        self.assertEqual(self.training_exercise.exercise_id, replacement.id)

    def test_replace_training_exercise_rejects_different_muscle_group(self):
        replacement = Exercise.objects.create(
            name="Leg Press Test",
            localized_name="Leg Press",
            muscle_group="Quadriceps",
            equipment="Machine",
            movement_pattern="SQUAT",
            is_compound=True,
        )
        client = APIClient()

        response = client.post(
            "/api/training/replace-exercise/",
            {
                "training_exercise_id": self.training_exercise.id,
                "replacement_exercise_id": replacement.id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.training_exercise.refresh_from_db()
        self.assertNotEqual(self.training_exercise.exercise_id, replacement.id)
