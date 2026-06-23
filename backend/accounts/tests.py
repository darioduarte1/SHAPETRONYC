from django.contrib.auth.models import User
from django.test import TestCase

from rest_framework.test import APIClient

from accounts.models import UserProfile


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
