from exercises.services.weight_scale import (
    get_exercise_weight_scale,
    next_available_weight,
    previous_available_weight,
    snap_to_available_weight,
)

TARGET_REPS = 12
WEIGHT_STEP = 2.5
MIN_COMPLETION_RATIO_FOR_LOAD_INCREASE = 0.66
LARGE_MACHINE_JUMP_RATIO = 0.10


def round_recommended_weight(weight):
    return round(float(weight) * 2) / 2


def number_or_none(value):
    if value in ("", None):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def average(values):
    clean_values = [value for value in values if value is not None]

    if not clean_values:
        return None

    return round(sum(clean_values) / len(clean_values), 1)


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

    return bool(set_log.get("reached_failure")) or reps is not None and reps < 10 or rir is not None and rir <= 0


def set_has_reserve(set_log):
    reps = number_or_none(set_log.get("reps_completed"))
    rir = number_or_none(set_log.get("rir"))

    return reps is not None and reps >= TARGET_REPS and rir is not None and rir >= 3 and not bool(set_log.get("reached_failure"))


def is_machine_or_stack_exercise(exercise):
    equipment = str(getattr(exercise, "equipment", "") or "").lower()

    return any(keyword in equipment for keyword in ["machine", "máquina", "maquina", "cable", "polia"])


def next_weight_available(weight, exercise):
    scale = get_exercise_weight_scale(exercise)

    if scale["configured"]:
        return next_available_weight(weight, exercise) > weight

    return False


def weight_scale_missing(exercise):
    return not get_exercise_weight_scale(exercise)["configured"]


def next_weight_jump_ratio(weight, exercise):
    next_weight = next_available_weight(weight, exercise)

    if not weight or next_weight <= weight:
        return 0

    return (next_weight - weight) / weight


def clean_completed_target_sets(working_sets):
    return [
        set_log for set_log in working_sets
        if set_has_reserve(set_log)
    ]


def summarize_working_sets(working_sets, planned_sets):
    rir_values = [number_or_none(set_log.get("rir")) for set_log in working_sets]
    volumes = [
        (number_or_none(set_log.get("weight_used")) or 0)
        * (number_or_none(set_log.get("reps_completed")) or 0)
        for set_log in working_sets
    ]
    missed_sets = [set_log for set_log in working_sets if set_missed_target(set_log)]
    reserve_sets = clean_completed_target_sets(working_sets)
    completed_ratio = round(len(working_sets) / planned_sets, 2) if planned_sets else 0

    return {
        "working_set_count": len(working_sets),
        "planned_sets": planned_sets,
        "completed_ratio": completed_ratio,
        "missed_set_count": len(missed_sets),
        "reserve_set_count": len(reserve_sets),
        "failure_count": len([set_log for set_log in working_sets if set_log.get("reached_failure")]),
        "missed_ratio": round(len(missed_sets) / len(working_sets), 2) if working_sets else 0,
        "reserve_ratio": round(len(reserve_sets) / len(working_sets), 2) if working_sets else 0,
        "average_rir": average(rir_values),
        "volume": round(sum(volumes), 1),
    }


def confidence_from_summary(summary):
    if summary["working_set_count"] == 0:
        return "baixa"

    if summary["completed_ratio"] >= 1 and summary["reserve_ratio"] >= 0.8 and summary["missed_set_count"] == 0:
        return "alta"

    if summary["missed_ratio"] >= 0.5 or summary["completed_ratio"] < MIN_COMPLETION_RATIO_FOR_LOAD_INCREASE:
        return "média"

    return "média"


def with_progression_metadata(recommendation, summary, decision_basis):
    return {
        **recommendation,
        "confidence": recommendation.get("confidence") or confidence_from_summary(summary),
        "decision_basis": decision_basis,
        "progression_context": summary,
        "source": "hybrid_local_workout_progression",
    }


def serialize_calibration(calibration):
    if not calibration:
        return None

    return {
        "status": calibration.status,
        "estimated_working_weight": calibration.estimated_working_weight,
        "target_reps": calibration.target_reps,
        "target_rir": calibration.target_rir,
        "confidence": calibration.confidence,
        "set_count": len(calibration.calibration_sets or []),
    }


def calibration_scale_context(calibration, exercise):
    if calibration and calibration.scale_snapshot:
        return calibration.scale_snapshot

    return exercise


def calculate_exercise_progression(training_exercise, current_sets, calibration=None):
    working_sets = [set_log for set_log in current_sets if is_working_set(set_log)]
    planned_sets = training_exercise.sets
    target_rir = training_exercise.target_rir
    summary = summarize_working_sets(working_sets, planned_sets)
    calibration_context = serialize_calibration(calibration)

    if not working_sets:
        if calibration and calibration.estimated_working_weight:
            recommended_weight = snap_to_available_weight(
                calibration.estimated_working_weight,
                calibration_scale_context(calibration, training_exercise.exercise),
            )
            summary["calibration"] = calibration_context

            return with_progression_metadata(
                {
                    "training_exercise": training_exercise.id,
                    "exercise": training_exercise.exercise_id,
                    "exercise_name": training_exercise.exercise.name,
                    "action": "use_calibrated_load",
                    "recommended_weight": recommended_weight,
                    "recommended_sets": planned_sets,
                    "target_reps": calibration.target_reps or TARGET_REPS,
                    "target_rir": calibration.target_rir or target_rir,
                    "title": "Usar peso calibrado",
                    "message": (
                        "Treino experimental concluído. No próximo treino, a primeira série normal "
                        f"deve começar com {recommended_weight}kg e 12 reps como objetivo."
                    ),
                    "reason": "A calibração inicial encontrou um peso de trabalho para este exercício.",
                    "confidence": calibration.confidence,
                },
                summary,
                ["Peso de trabalho calibrado", "Sem séries normais ainda", "Escala da máquina respeitada"],
            )

        return with_progression_metadata(
            {
                "training_exercise": training_exercise.id,
                "exercise": training_exercise.exercise_id,
                "exercise_name": training_exercise.exercise.name,
                "action": "maintain",
                "recommended_weight": "",
                "recommended_sets": planned_sets,
                "target_reps": training_exercise.target_max_reps or TARGET_REPS,
                "target_rir": target_rir,
                "title": "Mantém o plano",
                "message": "Sem séries normais registadas neste exercício. Mantém o plano no próximo treino.",
                "reason": "Não existem dados suficientes para ajustar a progressão.",
            },
            summary,
            ["Sem séries normais registadas"],
        )

    last_working_set = working_sets[-1]
    missed_sets = [set_log for set_log in working_sets if set_missed_target(set_log)]
    reserve_sets = [set_log for set_log in working_sets if set_has_reserve(set_log)]
    last_weight = number_or_none(last_working_set.get("weight_used")) or 0
    missed_ratio = len(missed_sets) / len(working_sets)
    completed_ratio = len(working_sets) / planned_sets if planned_sets else 0

    base_response = {
        "training_exercise": training_exercise.id,
        "exercise": training_exercise.exercise_id,
        "exercise_name": training_exercise.exercise.name,
        "target_reps": TARGET_REPS,
        "current_sets": len(working_sets),
        "completed_sets": len(current_sets),
    }

    if len(missed_sets) >= 2 or missed_ratio >= 0.5:
        return with_progression_metadata(
            {
                **base_response,
                "action": "reduce_volume",
                "recommended_weight": previous_available_weight(last_weight, training_exercise.exercise),
                "recommended_sets": max(1, planned_sets - 1),
                "target_rir": max(target_rir, 3),
                "title": "Reduz volume",
                "message": "No próximo treino, faz menos uma série normal e baixa ligeiramente a carga.",
                "reason": "Houve falhas ou séries abaixo das 12 reps em metade ou mais das séries normais.",
            },
            summary,
            ["Falhas ou misses em metade ou mais das séries normais", "Prioridade: recuperação e qualidade técnica"],
        )

    can_increase = (
        len(reserve_sets) == len(working_sets)
        and len(working_sets) >= planned_sets
        and completed_ratio >= 1
        and next_weight_available(last_weight, training_exercise.exercise)
        and (
            next_weight_jump_ratio(last_weight, training_exercise.exercise) <= LARGE_MACHINE_JUMP_RATIO
            or all((number_or_none(set_log.get("rir")) or 0) >= 4 for set_log in working_sets)
        )
    )

    if can_increase:
        return with_progression_metadata(
            {
                **base_response,
                "action": "increase_load",
                "recommended_weight": next_available_weight(last_weight, training_exercise.exercise),
                "recommended_sets": planned_sets,
                "target_rir": target_rir,
                "title": "Sobe carga",
                "message": "No próximo treino, aumenta a carga mantendo o mesmo volume.",
                "reason": "Todas as séries normais planeadas chegaram às 12 reps com RIR suficiente e existe próximo peso disponível.",
            },
            summary,
            ["Todas as séries normais planeadas chegaram ao alvo", "RIR >= 3", "Próximo peso disponível respeitado"],
        )

    if len(reserve_sets) == len(working_sets) and weight_scale_missing(training_exercise.exercise):
        return with_progression_metadata(
            {
                **base_response,
                "action": "maintain_load",
                "recommended_weight": snap_to_available_weight(last_weight, training_exercise.exercise),
                "recommended_sets": planned_sets,
                "target_rir": target_rir,
                "title": "Regista a escala",
                "message": "A performance sugere possível progressão, mas primeiro é preciso preencher a escala de pesos deste exercício.",
                "reason": "Sem pesos disponíveis registados, a IA não pode confirmar qual é o próximo salto real.",
            },
            summary,
            ["Séries com margem", "Subida bloqueada por escala de pesos em falta"],
        )

    if len(reserve_sets) == len(working_sets):
        return with_progression_metadata(
            {
                **base_response,
                "action": "maintain_load",
                "recommended_weight": snap_to_available_weight(last_weight, training_exercise.exercise),
                "recommended_sets": planned_sets,
                "target_rir": target_rir,
                "title": "Confirma volume",
                "message": "A performance foi boa, mas ainda não cumpre todos os critérios para subir. Repete a carga no próximo treino.",
                "reason": "A subida só acontece com todas as séries planeadas completas, RIR suficiente e próximo peso disponível.",
            },
            summary,
            ["Séries com margem", "Critérios completos de progressão ainda não foram cumpridos"],
        )

    if missed_sets:
        return with_progression_metadata(
            {
                **base_response,
                "action": "maintain_load",
                "recommended_weight": snap_to_available_weight(last_weight, training_exercise.exercise),
                "recommended_sets": planned_sets,
                "target_rir": max(target_rir, 2),
                "title": "Mantém carga",
                "message": "No próximo treino, repete a carga e tenta completar as 12 reps com melhor margem.",
                "reason": "Algumas séries ainda não justificam subida de carga.",
            },
            summary,
            ["Pelo menos uma série falhou o alvo", "Carga mantida para consolidar"],
        )

    return with_progression_metadata(
        {
            **base_response,
            "action": "adjust_target_rir",
            "recommended_weight": snap_to_available_weight(last_weight, training_exercise.exercise),
            "recommended_sets": planned_sets,
            "target_reps": TARGET_REPS,
            "target_rir": max(target_rir, 3),
            "title": "Ajusta RIR",
            "message": "No próximo treino, mantém a carga e procura terminar com mais reserva.",
            "reason": "O alvo de reps foi atingido, mas a margem de esforço ainda ficou curta.",
        },
        summary,
        ["Alvo de reps atingido", "RIR ainda curto para subir carga"],
    )


def calculate_workout_progression(workout, set_logs, calibrations=None):
    sets_by_training_exercise = {}
    calibrations_by_exercise = {
        calibration.exercise_id: calibration
        for calibration in calibrations or []
    }

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
            calibrations_by_exercise.get(training_exercise.exercise_id),
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
