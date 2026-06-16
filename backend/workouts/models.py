from django.db import models
from django.contrib.auth.models import User
from exercises.models import Exercise


class Workout(models.Model):
    WORKOUT_TYPES = [
        ('PUSH', 'Push'),
        ('PULL', 'Pull'),
        ('LEGS', 'Legs'),
        ('UPPER', 'Upper'),
        ('LOWER', 'Lower'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workout_type = models.CharField(max_length=20, choices=WORKOUT_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.workout_type}"


class WorkoutExercise(models.Model):
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.workout} - {self.exercise.name}"