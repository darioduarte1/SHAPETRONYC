# =============================================================================
# models.py
# -----------------------------------------------------------------------------
# Define os modelos da app programs.
# Representa programas de treino, workouts e exercícios planeados que o atleta vai executar.
# Estes modelos ligam o perfil do atleta à estrutura concreta do plano mostrado no frontend.
# =============================================================================
from django.db import models
from exercises.models import Exercise


class ProgramTemplate(models.Model):
    GOAL_CHOICES = [
        ("HYPERTROPHY", "Hypertrophy"),
        ("STRENGTH", "Strength"),
        ("FAT_LOSS", "Fat Loss"),
    ]

    LEVEL_CHOICES = [
        ("BEGINNER", "Beginner"),
        ("INTERMEDIATE", "Intermediate"),
        ("ADVANCED", "Advanced"),
    ]

    name = models.CharField(max_length=100)
    goal = models.CharField(max_length=30, choices=GOAL_CHOICES)
    level = models.CharField(max_length=30, choices=LEVEL_CHOICES)
    days_per_week = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class WorkoutTemplate(models.Model):
    program = models.ForeignKey(
        ProgramTemplate,
        on_delete=models.CASCADE,
        related_name="workouts"
    )
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.program.name} - {self.name}"


class WorkoutExerciseTemplate(models.Model):
    workout = models.ForeignKey(
        WorkoutTemplate,
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