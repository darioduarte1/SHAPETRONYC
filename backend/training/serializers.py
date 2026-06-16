from rest_framework import serializers

from .models import (
    TrainingProgram,
    TrainingWorkout,
    TrainingWorkoutExercise,
)


class TrainingWorkoutExerciseSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(
        source="exercise.name",
        read_only=True
    )

    class Meta:
        model = TrainingWorkoutExercise
        fields = [
            "id",
            "exercise",
            "exercise_name",
            "sets",
            "target_min_reps",
            "target_max_reps",
            "target_rir",
            "order",
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