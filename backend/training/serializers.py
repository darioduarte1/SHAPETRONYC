from rest_framework import serializers

from .models import (
    TrainingProgram,
    TrainingWorkout,
    TrainingWorkoutExercise,
    WorkoutSession,
)


class TrainingWorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(
        source="exercise.name",
        read_only=True
    )
    exercise_muscle_group = serializers.CharField(source="exercise.muscle_group", read_only=True)
    exercise_movement_pattern = serializers.CharField(source="exercise.movement_pattern", read_only=True)
    exercise_is_compound = serializers.BooleanField(source="exercise.is_compound", read_only=True)
    exercise_equipment = serializers.CharField(source="exercise.equipment", read_only=True)
    exercise_localized_name = serializers.CharField(source="exercise.localized_name", read_only=True)
    exercise_image_url = serializers.CharField(source="exercise.image_url", read_only=True)

    class Meta:
        model = TrainingWorkoutExercise
        fields = [
            "id",
            "exercise",
            "exercise_name",
            "exercise_localized_name",
            "exercise_image_url",
            "exercise_muscle_group",
            "exercise_movement_pattern",
            "exercise_is_compound",
            "exercise_equipment",
            "sets",
            "target_min_reps",
            "target_max_reps",
            "target_rir",
            "order",
            "workout",
        ]


class TrainingWorkoutSerializer(serializers.ModelSerializer):
    exercises = TrainingWorkoutExerciseSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = TrainingWorkout
        fields = [
            "id",
            "name",
            "order",
            "exercises",
        ]


class TrainingProgramSerializer(serializers.ModelSerializer):
    workouts = TrainingWorkoutSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = TrainingProgram
        fields = [
            "id",
            "name",
            "goal",
            "level",
            "days_per_week",
            "workouts",
        ]

class WorkoutSessionSerializer(serializers.ModelSerializer):
    workout_name = serializers.CharField(source="workout.name", read_only=True)

    class Meta:
        model = WorkoutSession
        fields = [
            "id",
            "user",
            "workout",
            "workout_name",
            "status",
            "started_at",
            "completed_at",
            "notes",
        ]
