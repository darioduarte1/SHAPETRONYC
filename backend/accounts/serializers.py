from rest_framework import serializers
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "username",
            "gender",
            "age",
            "height_cm",
            "weight_kg",
            "goal",
            "level",
            "training_experience",
            "days_per_week",
            "created_at",
            "updated_at",
        ]