from django.db import models
from django.contrib.auth.models import User

from exercises.models import Exercise
from training.models import TrainingWorkoutExercise, WorkoutSession


class SetLog(models.Model):
    SET_TYPE_CHOICES = [
        ("WARMUP", "Warm-up"),
        ("WORKING", "Working set"),
        ("DROP", "Drop set"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    training_exercise = models.ForeignKey(
        TrainingWorkoutExercise,
        on_delete=models.CASCADE,
        related_name="set_logs",
        null=True,
        blank=True,
    )

    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE
    )

    set_number = models.PositiveIntegerField()

    set_type = models.CharField(
        max_length=20,
        choices=SET_TYPE_CHOICES,
        default="WORKING",
    )

    planned_weight = models.FloatField(
        null=True,
        blank=True
    )

    weight_used = models.FloatField()

    target_min_reps = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    target_max_reps = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    reps_completed = models.PositiveIntegerField()

    rir = models.IntegerField(
        null=True,
        blank=True
    )

    reached_failure = models.BooleanField(default=False)

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.exercise.name} - Set {self.set_number}"

    workout_session = models.ForeignKey(
        WorkoutSession,
        on_delete=models.CASCADE,
        related_name="set_logs",
        null=True,
        blank=True,
    )
