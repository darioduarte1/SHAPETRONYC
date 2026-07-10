# =============================================================================
# 0007_userexerciseweightscale.py
# -----------------------------------------------------------------------------
# Migração Django da app training.
# É usada pelo sistema de migrations para criar ou alterar a estrutura da base de dados associada a training.
# O ficheiro 0007_userexerciseweightscale deve ser mantido como histórico técnico da evolução dos modelos e aplicado automaticamente pelo manage.py migrate.
# =============================================================================
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("exercises", "0005_exercise_weight_scale"),
        ("training", "0006_exercisecalibration"),
    ]

    operations = [
        migrations.CreateModel(
            name="UserExerciseWeightScale",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("main_weight_options", models.JSONField(blank=True, default=list)),
                ("micro_weight_options", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("exercise", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="user_weight_scales", to="exercises.exercise")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="exercise_weight_scales", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-updated_at"],
                "unique_together": {("user", "exercise")},
            },
        ),
    ]
