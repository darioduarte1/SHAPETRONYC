from django.db import models
from django.contrib.auth.models import User
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator
)


class UserProfile(models.Model):

    GOAL_CHOICES = [
        ("HYPERTROPHY", "Hypertrophy"),
        ("STRENGTH", "Strength"),
        ("FAT_LOSS", "Fat Loss"),
        ("RECOMPOSITION", "Recomposition"),
        ("GENERAL_FITNESS", "General Fitness"),
    ]

    LEVEL_CHOICES = [
        ("BEGINNER", "Beginner"),
        ("INTERMEDIATE", "Intermediate"),
        ("ADVANCED", "Advanced"),
    ]

    GENDER_CHOICES = [
        ("MALE", "Male"),
        ("FEMALE", "Female"),
    ]

    TRAINING_EXPERIENCE_CHOICES = [
        ("LESS_THAN_1", "< 1 year"),
        ("ONE_TO_THREE", "1-3 years"),
        ("THREE_TO_FIVE", "3-5 years"),
        ("MORE_THAN_FIVE", "> 5 years"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES
    )

    age = models.PositiveIntegerField(
        validators=[
            MinValueValidator(16),
            MaxValueValidator(100)
        ]
    )

    height_cm = models.PositiveIntegerField()

    weight_kg = models.FloatField()

    goal = models.CharField(
        max_length=30,
        choices=GOAL_CHOICES
    )

    level = models.CharField(
        max_length=30,
        choices=LEVEL_CHOICES
    )

    training_experience = models.CharField(
        max_length=30,
        choices=TRAINING_EXPERIENCE_CHOICES
    )

    days_per_week = models.PositiveIntegerField(
        validators=[
            MinValueValidator(2),
            MaxValueValidator(7)
        ]
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username