TARGET_REPS = 12
WEIGHT_STEP = 2.5


def round_recommended_weight(weight):
    return round(float(weight) * 2) / 2


def number_or_none(value):
    if value in ("", None):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def serialize_progression_set(set_log):
    return {
        "set_number": set_log.set_number,
        "set_type": set_log.set_type,
        "weight_used": float(set_log.weight_used),
        "reps_completed": set_log.reps_completed,
        "rir": set_log.rir,
        "reached_failure": set_log.reached_failure,
    }


def is_working_set(set_log):
    return set_log.get("set_type") == "WORKING"


def set_missed_target(set_log):
    reps = number_or_none(set_log.get("reps_completed"))
    rir = number_or_none(set_log.get("rir"))

    return bool(set_log.get("reached_failure")) or reps is not None and reps < TARGET_REPS or rir is not None and rir <= 1


def set_has_reserve(set_log):
    reps = number_or_none(set_log.get("reps_completed"))
    rir = number_or_none(set_log.get("rir"))

    return reps is not None and reps >= TARGET_REPS and rir is not None and rir >= 2


def calculate_exercise_progression(training_exercise, current_sets):
    working_sets = [set_log for set_log in current_sets if is_working_set(set_log)]
    planned_sets = training_exercise.sets
    target_rir = training_exercise.target_rir

    if not working_sets:
        return {
            "training_exercise": training_exercise.id,
            "exercise": training_exercise.exercise_id,
            "exercise_name": training_exercise.exercise.name,
            "action": "maintain",
            "recommended_weight": "",
            "recommended_sets": planned_sets,
            "target_reps": TARGET_REPS,
            "target_rir": target_rir,
            "title": "Mantém o plano",
            "message": "Sem séries normais registadas neste exercício. Mantém o plano no próximo treino.",
            "reason": "Não existem dados suficientes para ajustar a progressão.",
        }

    last_working_set = working_sets[-1]
    missed_sets = [set_log for set_log in working_sets if set_missed_target(set_log)]
    reserve_sets = [set_log for set_log in working_sets if set_has_reserve(set_log)]
    last_weight = number_or_none(last_working_set.get("weight_used")) or 0
    missed_ratio = len(missed_sets) / len(working_sets)

    base_response = {
        "training_exercise": training_exercise.id,
        "exercise": training_exercise.exercise_id,
        "exercise_name": training_exercise.exercise.name,
        "target_reps": TARGET_REPS,
        "current_sets": len(working_sets),
        "completed_sets": len(current_sets),
    }

    if len(missed_sets) >= 2 or missed_ratio >= 0.5:
        return {
            **base_response,
            "action": "reduce_volume",
            "recommended_weight": round_recommended_weight(max(last_weight - WEIGHT_STEP, 0)),
            "recommended_sets": max(1, planned_sets - 1),
            "target_rir": max(target_rir, 3),
            "title": "Reduz volume",
            "message": "No próximo treino, faz menos uma série normal e baixa ligeiramente a carga.",
            "reason": "Houve falhas ou séries abaixo das 12 reps em metade ou mais das séries normais.",
        }

    if len(reserve_sets) == len(working_sets):
        return {
            **base_response,
            "action": "increase_load",
            "recommended_weight": round_recommended_weight(last_weight + WEIGHT_STEP),
            "recommended_sets": planned_sets,
            "target_rir": target_rir,
            "title": "Sobe carga",
            "message": "No próximo treino, aumenta a carga mantendo o mesmo volume.",
            "reason": "Todas as séries normais chegaram às 12 reps com margem.",
        }

    if missed_sets:
        return {
            **base_response,
            "action": "maintain_load",
            "recommended_weight": round_recommended_weight(last_weight),
            "recommended_sets": planned_sets,
            "target_rir": max(target_rir, 2),
            "title": "Mantém carga",
            "message": "No próximo treino, repete a carga e tenta completar as 12 reps com melhor margem.",
            "reason": "Algumas séries ainda não justificam subida de carga.",
        }

    return {
        **base_response,
        "action": "adjust_target_rir",
        "recommended_weight": round_recommended_weight(last_weight),
        "recommended_sets": planned_sets,
        "target_rir": max(target_rir, 3),
        "title": "Ajusta RIR",
        "message": "No próximo treino, mantém a carga e procura terminar com mais reserva.",
        "reason": "O alvo de reps foi atingido, mas a margem de esforço ainda ficou curta.",
    }


def calculate_workout_progression(workout, set_logs):
    sets_by_training_exercise = {}

    for set_log in set_logs:
        if not set_log.training_exercise_id:
            continue

        sets_by_training_exercise.setdefault(set_log.training_exercise_id, []).append(
            serialize_progression_set(set_log)
        )

    recommendations = [
        calculate_exercise_progression(
            training_exercise,
            sorted(
                sets_by_training_exercise.get(training_exercise.id, []),
                key=lambda set_log: (set_log["set_number"], set_log["set_type"]),
            ),
        )
        for training_exercise in workout.exercises.select_related("exercise").all()
    ]

    action_counts = {}

    for recommendation in recommendations:
        action = recommendation["action"]
        action_counts[action] = action_counts.get(action, 0) + 1

    return {
        "workout": workout.id,
        "workout_name": workout.name,
        "recommendations": recommendations,
        "summary": {
            "exercise_count": len(recommendations),
            "action_counts": action_counts,
        },
    }
