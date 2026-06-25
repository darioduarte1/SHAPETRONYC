from django.contrib.auth.models import User
from django.test import TestCase

from rest_framework.test import APIClient

from accounts.models import UserProfile
from exercises.models import Exercise
from progression.models import SetLog
from training.models import (
    TrainingProgram,
    TrainingWorkout,
    TrainingWorkoutExercise,
    WorkoutSession,
)


class UserProfileEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def profile_payload(self, user_id, **overrides):
        payload = {
            "user": user_id,
            "gender": "MALE",
            "age": 34,
            "height_cm": 172,
            "weight_kg": 72,
            "goal": "HYPERTROPHY",
            "level": "INTERMEDIATE",
            "training_experience": "ONE_TO_THREE",
            "days_per_week": 5,
        }
        payload.update(overrides)
        return payload

    def test_creates_profile_for_new_user(self):
        user = User.objects.create(username="new_user")

        response = self.client.post(
            "/api/accounts/profiles/",
            self.profile_payload(user.id),
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)

    def test_updates_existing_profile_for_same_user(self):
        user = User.objects.create(username="existing_user")
        existing_payload = self.profile_payload(user.id)
        existing_payload["user"] = user
        UserProfile.objects.create(**existing_payload)

        response = self.client.post(
            "/api/accounts/profiles/",
            self.profile_payload(user.id, weight_kg=80, days_per_week=4),
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)

        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.weight_kg, 80)
        self.assertEqual(profile.days_per_week, 4)

    def test_exports_user_training_history_file(self):
        user = User.objects.create(username="export_user")
        profile = UserProfile.objects.create(
            user=user,
            gender="MALE",
            age=34,
            height_cm=172,
            weight_kg=72,
            goal="HYPERTROPHY",
            level="INTERMEDIATE",
            training_experience="ONE_TO_THREE",
            days_per_week=5,
        )
        program = TrainingProgram.objects.create(
            user=user,
            name="Export Program",
            goal="HYPERTROPHY",
            level="INTERMEDIATE",
            days_per_week=5,
        )
        workout = TrainingWorkout.objects.create(
            program=program,
            name="Push",
            order=1,
        )
        exercise = Exercise.objects.create(
            name="Chest Press Machine",
            muscle_group="Chest",
            equipment="Machine",
            movement_pattern="HORIZONTAL_PUSH",
            is_compound=True,
            main_weight_options=[10, 20, 30],
            micro_weight_options=[1, 2],
        )
        training_exercise = TrainingWorkoutExercise.objects.create(
            workout=workout,
            exercise=exercise,
            order=1,
            sets=3,
            target_min_reps=10,
            target_max_reps=12,
            target_rir=2,
        )
        session = WorkoutSession.objects.create(
            user=user,
            workout=workout,
            status="COMPLETED",
        )
        SetLog.objects.create(
            user=user,
            workout_session=session,
            training_exercise=training_exercise,
            exercise=exercise,
            set_number=1,
            set_type="WORKING",
            weight_used=20,
            reps_completed=12,
            rir=2,
            reached_failure=False,
        )

        response = self.client.get(f"/api/accounts/profiles/{profile.id}/export/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("attachment", response["Content-Disposition"])

        data = response.json()
        self.assertEqual(data["profile"]["username"], "export_user")
        self.assertEqual(data["programs"][0]["workouts"][0]["name"], "Push")
        self.assertEqual(data["set_logs"][0]["exercise_name"], "Chest Press Machine")
        self.assertEqual(
            data["programs"][0]["workouts"][0]["exercises"][0]["main_weight_options"],
            [10, 20, 30],
        )
