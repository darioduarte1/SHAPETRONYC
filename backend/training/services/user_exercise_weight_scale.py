from exercises.services.weight_scale import (
    get_exercise_weight_scale,
    normalize_micro_weight_options,
    normalize_weight_options,
)
from training.models import UserExerciseWeightScale


def get_user_exercise_scale_record(user, exercise):
    if not user or not exercise:
        return None

    return UserExerciseWeightScale.objects.filter(
        user=user,
        exercise=exercise,
    ).first()


def get_user_exercise_weight_scale(user, exercise):
    scale_record = get_user_exercise_scale_record(user, exercise)

    if not scale_record:
        return get_exercise_weight_scale({
            "main_weight_options": [],
            "micro_weight_options": [],
        })

    return get_exercise_weight_scale({
        "main_weight_options": scale_record.main_weight_options,
        "micro_weight_options": scale_record.micro_weight_options,
    })


def serialize_user_exercise_weight_scale(user, exercise):
    scale_record = get_user_exercise_scale_record(user, exercise)
    scale = get_user_exercise_weight_scale(user, exercise)

    return {
        "id": scale_record.id if scale_record else None,
        "exercise": exercise.id,
        "main_weight_options": scale["main_weight_options"],
        "micro_weight_options": scale["micro_weight_options"],
        "micro_weight_sums": scale["micro_weight_sums"],
        "available_weights": scale["available_weights"],
        "configured": scale["configured"],
    }


def upsert_user_exercise_weight_scale(user, exercise, main_weight_options, micro_weight_options):
    scale_record, _ = UserExerciseWeightScale.objects.get_or_create(
        user=user,
        exercise=exercise,
    )
    scale_record.main_weight_options = normalize_weight_options(main_weight_options)
    scale_record.micro_weight_options = normalize_micro_weight_options(micro_weight_options)
    scale_record.save()

    return serialize_user_exercise_weight_scale(user, exercise)
