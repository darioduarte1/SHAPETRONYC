# =============================================================================
# models.py
# -----------------------------------------------------------------------------
# Define os modelos centrais da app training.
# Guarda sessões de treino, memória do atleta, blocos de periodização, calibrações experimentais, escalas por exercício e decisões adaptativas.
# Estes modelos ligam execução real, análise histórica e recomendações futuras.
# =============================================================================
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


class AthleteTrainingMemory(models.Model):
    MEMORY_TYPE_CHOICES = [
        ("PROGRESSION", "Progression"),
        ("WATCHLIST", "Watchlist"),
        ("EFFORT_PATTERN", "Effort pattern"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="training_memories",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="training_memories",
    )
    memory_type = models.CharField(max_length=30, choices=MEMORY_TYPE_CHOICES)
    title = models.CharField(max_length=120)
    summary = models.TextField()
    evidence = models.JSONField(default=list, blank=True)
    confidence = models.CharField(max_length=20, default="média")
    severity = models.PositiveIntegerField(default=1)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "exercise", "memory_type")
        ordering = ["-severity", "-updated_at"]

    def __str__(self):
        return f"{self.user.username} - {self.exercise.name} - {self.memory_type}"


class AdaptivePlanDecision(models.Model):
    STATUS_CHOICES = [
        ("APPLIED", "Applied"),
        ("DEFERRED", "Deferred"),
        ("IGNORED", "Ignored"),
    ]

    ACTION_CHOICES = [
        ("protect_recovery", "Protect recovery"),
        ("increase_margin", "Increase margin"),
        ("progress_load", "Progress load"),
        ("maintain_plan", "Maintain plan"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="adaptive_plan_decisions",
    )
    training_exercise = models.ForeignKey(
        "TrainingWorkoutExercise",
        on_delete=models.CASCADE,
        related_name="adaptive_plan_decisions",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="adaptive_plan_decisions",
    )
    workout_name = models.CharField(max_length=100)
    exercise_name = models.CharField(max_length=100)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    current_sets = models.PositiveIntegerField()
    recommended_sets = models.PositiveIntegerField()
    current_target_rir = models.PositiveIntegerField()
    recommended_target_rir = models.PositiveIntegerField()
    load_adjustment = models.FloatField(default=0)
    message = models.TextField(blank=True)
    evidence = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.exercise_name} - {self.action} - {self.status}"


class ExerciseCalibration(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("CALIBRATED", "Calibrated"),
        ("NEEDS_REVIEW", "Needs review"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="exercise_calibrations",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="exercise_calibrations",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    estimated_working_weight = models.FloatField(null=True, blank=True)
    target_reps = models.PositiveIntegerField(default=12)
    target_rir = models.PositiveIntegerField(default=2)
    confidence = models.CharField(max_length=20, default="baixa")
    calibration_sets = models.JSONField(default=list, blank=True)
    scale_snapshot = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "exercise")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.username} - {self.exercise.name} - {self.status}"


class UserExerciseWeightScale(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="exercise_weight_scales",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="user_weight_scales",
    )
    main_weight_options = models.JSONField(default=list, blank=True)
    micro_weight_options = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "exercise")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user.username} - {self.exercise.name} scale"


class TrainingBlock(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
    ]

    PHASE_CHOICES = [
        ("BUILD", "Build"),
        ("DELOAD", "Deload"),
        ("RETURN", "Return"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="training_blocks",
    )
    program = models.ForeignKey(
        TrainingProgram,
        on_delete=models.CASCADE,
        related_name="training_blocks",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=120)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default="BUILD")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    planned_weeks = models.PositiveIntegerField(default=4)
    summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date", "-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.name} - {self.status}"


class WorkoutSession(models.Model):
    STATUS_CHOICES = [
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    workout = models.ForeignKey(
        TrainingWorkout,
        on_delete=models.CASCADE,
        related_name="sessions"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="IN_PROGRESS"
    )

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    coach_feedback = models.JSONField(default=dict, blank=True)
    coach_feedback_source = models.CharField(max_length=60, blank=True)
    coach_feedback_status = models.CharField(max_length=60, blank=True)
    coach_feedback_model = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.workout.name} - {self.status}"
