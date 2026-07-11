# =============================================================================
# serializers.py
# -----------------------------------------------------------------------------
# Transforma programas, workouts e exercícios planeados em JSON para a API.
# É usado pelas views para devolver ao frontend a estrutura completa do plano de treino.
# Também organiza dados relacionados para a interface poder renderizar treinos e exercícios.
# =============================================================================
from rest_framework import serializers

from .models import ProgramTemplate, WorkoutTemplate, WorkoutExerciseTemplate


class WorkoutExerciseTemplateSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source="exercise.name", read_only=True)
    muscle_group = serializers.CharField(source="exercise.muscle_group", read_only=True)
    equipment = serializers.CharField(source="exercise.equipment", read_only=True)

    class Meta:
        model = WorkoutExerciseTemplate
        fields = [
            "id",
            "exercise",
            "exercise_name",
            "muscle_group",
            "equipment",
            "order",
            "sets",
            "target_min_reps",
            "target_max_reps",
            "target_rir",
        ]


class WorkoutTemplateSerializer(serializers.ModelSerializer):
    exercises = WorkoutExerciseTemplateSerializer(many=True, read_only=True)

    class Meta:
        model = WorkoutTemplate
        fields = [
            "id",
            "name",
            "order",
            "exercises",
        ]


class ProgramTemplateSerializer(serializers.ModelSerializer):
    workouts = WorkoutTemplateSerializer(many=True, read_only=True)

    class Meta:
        model = ProgramTemplate
        fields = [
            "id",
            "name",
            "goal",
            "level",
            "days_per_week",
            "workouts",
        ]