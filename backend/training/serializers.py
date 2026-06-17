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