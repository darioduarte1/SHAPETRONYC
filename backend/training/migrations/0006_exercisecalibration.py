# =============================================================================
# 0006_exercisecalibration.py
# -----------------------------------------------------------------------------
# Migração Django da app training.
# É usada pelo sistema de migrations para criar ou alterar a estrutura da base de dados associada a training.
# O ficheiro 0006_exercisecalibration deve ser mantido como histórico técnico da evolução dos modelos e aplicado automaticamente pelo manage.py migrate.
# =============================================================================
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("exercises", "0005_exercise_weight_scale"),
        ("training", "0005_trainingblock"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExerciseCalibration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("CALIBRATED", "Calibrated"), ("NEEDS_REVIEW", "Needs review")], default="PENDING", max_length=20)),
                ("estimated_working_weight", models.FloatField(blank=True, null=True)),
                ("target_reps", models.PositiveIntegerField(default=12)),
                ("target_rir", models.PositiveIntegerField(default=2)),
                ("confidence", models.CharField(default="baixa", max_length=20)),
                ("calibration_sets", models.JSONField(blank=True, default=list)),
                ("scale_snapshot", models.JSONField(blank=True, default=dict)),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("exercise", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exercise_calibrations", to="exercises.exercise")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exercise_calibrations", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-updated_at"],
                "unique_together": {("user", "exercise")},
            },
        ),
    ]
