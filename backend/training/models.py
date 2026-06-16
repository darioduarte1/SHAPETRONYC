from django.db import models
from django.contrib.auth.models import User

from exercises.models import Exercise


class TrainingProgram(models.Model):
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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    goal = models.CharField(max_length=30, choices=GOAL_CHOICES)
    level = models.CharField(max_length=30, choices=LEVEL_CHOICES)
    days_per_week = models.PositiveIntegerField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class TrainingWorkout(models.Model):
    program = models.ForeignKey(
        TrainingProgram,
        on_delete=models.CASCADE,
        related_name="workouts"
    )

    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.program.name} - {self.name}"


class TrainingWorkoutExercise(models.Model):
    workout = models.ForeignKey(
        TrainingWorkout,
        on_delete=models.CASCADE,
        related_name="exercises"
    )

    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)

    order = models.PositiveIntegerField()
    sets = models.PositiveIntegerField(default=3)
    target_min_reps = models.PositiveIntegerField(default=10)
    target_max_reps = models.PositiveIntegerField(default=12)
    target_rir = models.PositiveIntegerField(default=2)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.workout.name} - {self.exercise.name}"