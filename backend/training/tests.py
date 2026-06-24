from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import UserProfile
from exercises.models import Exercise
from progression.models import SetLog
from training.models import (
    AthleteTrainingMemory,
    TrainingProgram,
    TrainingWorkout,
    TrainingWorkoutExercise,
    WorkoutSession,
)
from training.services.athlete_dashboard import build_athlete_dashboard
from training.services.adaptive_plan import build_adaptive_plan
from training.services.training_memory import refresh_training_memory


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
