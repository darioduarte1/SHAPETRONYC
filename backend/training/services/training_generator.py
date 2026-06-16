from programs.services.program_generator import generate_program_structure
from training.models import (
    TrainingProgram,
    TrainingWorkout,
    TrainingWorkoutExercise,
)
from exercises.models import Exercise


def generate_training_program(user_profile):
    structure = generate_program_structure(
        goal=user_profile.goal,
        level=user_profile.level,
        days_per_week=user_profile.days_per_week,
    )

    TrainingProgram.objects.filter(
        user=user_profile.user,
        is_active=True
    ).update(is_active=False)

    program = TrainingProgram.objects.create(
        user=user_profile.user,
        name=f"{user_profile.goal} {user_profile.level} {user_profile.days_per_week} Days",
        goal=user_profile.goal,
        level=user_profile.level,
        days_per_week=user_profile.days_per_week,
        is_active=True,
    )

    for index, workout_name in enumerate(structure["workouts"], start=1):
        workout = TrainingWorkout.objects.create(
            program=program,
            name=workout_name,
            order=index,
        )

        exercises = select_exercises_for_workout(workout_name)

        for exercise_index, exercise_config in enumerate(exercises, start=1):
            TrainingWorkoutExercise.objects.create(
                workout=workout,
                exercise=exercise_config["exercise"],
                order=exercise_index,
                sets=exercise_config["sets"],
                target_min_reps=exercise_config["target_min_reps"],
                target_max_reps=exercise_config["target_max_reps"],
                target_rir=exercise_config["target_rir"],
            )

    return program


def select_exercises_for_workout(workout_name):
    name = workout_name.upper()

    if "PUSH" in name:
        return build_push_workout()

    if "PULL" in name:
        return build_pull_workout()

    if "LEGS" in name or "LOWER" in name:
        return build_legs_workout()

    if "UPPER" in name:
        return build_upper_workout()

    if "FULL BODY" in name:
        return build_full_body_workout()

    if "CARDIO" in name:
        return build_cardio_core_workout()

    return build_full_body_workout()


def get_exercise(name):
    return Exercise.objects.get(name=name)


def build_push_workout():
    return [
        exercise_item("Chest Press Machine", 3, 10, 12, 2),
        exercise_item("Incline Chest Press", 3, 10, 12, 2),
        exercise_item("Pec Deck", 3, 12, 15, 2),
        exercise_item("Shoulder Press", 3, 8, 10, 2),
        exercise_item("Lateral Raise Machine", 3, 12, 15, 2),
        exercise_item("Triceps Pushdown", 3, 10, 12, 2),
    ]


def build_pull_workout():
    return [
        exercise_item("Lat Pulldown", 3, 10, 12, 2),
        exercise_item("Seated Row Machine", 3, 10, 12, 2),
        exercise_item("Chest Supported Row", 3, 10, 12, 2),
        exercise_item("Rear Delt Fly", 3, 12, 15, 2),
        exercise_item("Biceps Curl Machine", 3, 10, 12, 2),
        exercise_item("Hammer Curl", 3, 10, 12, 2),
    ]


def build_legs_workout():
    return [
        exercise_item("Leg Press", 3, 10, 12, 2),
        exercise_item("Leg Extension", 3, 12, 15, 2),
        exercise_item("Seated Leg Curl", 3, 10, 12, 2),
        exercise_item("Hip Thrust Machine", 3, 10, 12, 2),
        exercise_item("Standing Calf Raise", 4, 12, 15, 2),
    ]


def build_upper_workout():
    return [
        exercise_item("Incline Chest Press", 3, 8, 10, 2),
        exercise_item("Lat Pulldown", 3, 8, 10, 2),
        exercise_item("Shoulder Press", 3, 8, 10, 2),
        exercise_item("Seated Row Machine", 3, 10, 12, 2),
        exercise_item("Lateral Raise Machine", 3, 12, 15, 2),
        exercise_item("Triceps Pushdown", 2, 10, 12, 2),
        exercise_item("Biceps Curl Machine", 2, 10, 12, 2),
    ]


def build_full_body_workout():
    return [
        exercise_item("Leg Press", 3, 10, 12, 2),
        exercise_item("Chest Press Machine", 3, 10, 12, 2),
        exercise_item("Lat Pulldown", 3, 10, 12, 2),
        exercise_item("Seated Leg Curl", 2, 10, 12, 2),
        exercise_item("Lateral Raise Machine", 2, 12, 15, 2),
        exercise_item("Crunch Machine", 2, 12, 15, 2),
    ]


def build_cardio_core_workout():
    return [
        exercise_item("Treadmill Incline Walk", 1, 20, 30, 3),
        exercise_item("Crunch Machine", 3, 12, 15, 2),
        exercise_item("Plank", 3, 30, 60, 2),
    ]


def exercise_item(name, sets, min_reps, max_reps, rir):
    return {
        "exercise": get_exercise(name),
        "sets": sets,
        "target_min_reps": min_reps,
        "target_max_reps": max_reps,
        "target_rir": rir,
    }