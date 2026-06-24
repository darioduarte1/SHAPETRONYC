TARGET_REPS = 12
WEIGHT_STEP = 2.5
HISTORY_LIMIT = 15
MIN_HISTORY_FOR_HIGH_CONFIDENCE = 5


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


def is_working_set(set_log):
    return getattr(set_log, "set_type", None) == "WORKING"


def set_reached_target(set_log, target_reps=TARGET_REPS):
    return int(set_log.reps_completed) >= target_reps and not set_log.reached_failure


def set_has_reserve(set_log, target_reps=TARGET_REPS):
    return set_reached_target(set_log, target_reps) and set_log.rir is not None and set_log.rir >= 2


def calculate_recommended_set(previous_set, target_reps=12):
    if not previous_set:
        return {
            "recommended_weight": "",
            "recommended_reps": "",
            "reason": "",
        }

    previous_weight = float(previous_set.weight_used)
    previous_reps = int(previous_set.reps_completed)
    effective_rir = previous_set.rir if previous_set.rir is not None else 2
    reached_target = previous_reps >= target_reps

    if not reached_target:
        should_reduce_load = previous_set.reached_failure or effective_rir <= 1

        if should_reduce_load:
            return {
                "recommended_weight": round_recommended_weight(max(0, previous_weight - 2.5)),
                "recommended_reps": target_reps,
                "reason": "A série anterior falhou as 12 reps perto da falha, por isso baixa a carga.",
            }

        return {
            "recommended_weight": round_recommended_weight(previous_weight),
            "recommended_reps": target_reps,
            "reason": "A série anterior falhou as 12 reps, por isso mantém a carga e constrói reps.",
        }

    if effective_rir >= 2:
        return {
            "recommended_weight": round_recommended_weight(previous_weight + 2.5),
            "recommended_reps": target_reps,
            "reason": "A série anterior chegou às 12 reps com margem, por isso progride a carga.",
        }

    return {
        "recommended_weight": round_recommended_weight(previous_weight),
        "recommended_reps": target_reps,
        "reason": "A série anterior chegou às 12 reps perto da falha, por isso mantém a carga.",
    }


def serialize_history_set(set_log):
    return {
        "session_id": set_log.workout_session_id,
        "workout_name": set_log.workout_session.workout.name if set_log.workout_session_id else "",
        "set_number": set_log.set_number,
        "set_type": set_log.set_type,
        "weight_used": float(set_log.weight_used),
        "reps_completed": set_log.reps_completed,
        "rir": set_log.rir,
        "reached_failure": set_log.reached_failure,
        "created_at": set_log.created_at,
    }


def group_sets_by_session(set_logs):
    grouped_sets = {}

    for set_log in set_logs:
        grouped_sets.setdefault(set_log.workout_session_id, []).append(set_log)

    return list(grouped_sets.values())


def summarize_recent_sessions(recent_session_sets, target_reps=TARGET_REPS):
    first_working_sets = []
    all_working_sets = []

    for session_sets in recent_session_sets:
        working_sets = [set_log for set_log in session_sets if is_working_set(set_log)]

        if not working_sets:
            continue

        first_working_sets.append(working_sets[0])
        all_working_sets.extend(working_sets)

    successful_first_sets = [
        set_log for set_log in first_working_sets if set_reached_target(set_log, target_reps)
    ]
    reserve_first_sets = [
        set_log for set_log in first_working_sets if set_has_reserve(set_log, target_reps)
    ]
    failed_working_sets = [
        set_log
        for set_log in all_working_sets
        if set_log.reached_failure or int(set_log.reps_completed) < target_reps
    ]
    first_set_weights = [float(set_log.weight_used) for set_log in first_working_sets]
    first_set_rirs = [set_log.rir for set_log in first_working_sets]
    latest_first_set = first_working_sets[0] if first_working_sets else None

    return {
        "session_count": len(recent_session_sets),
        "usable_session_count": len(first_working_sets),
        "first_set_success_rate": round(
            len(successful_first_sets) / len(first_working_sets),
            2,
        ) if first_working_sets else 0,
        "first_set_reserve_rate": round(
            len(reserve_first_sets) / len(first_working_sets),
            2,
        ) if first_working_sets else 0,
        "working_set_failure_rate": round(
            len(failed_working_sets) / len(all_working_sets),
            2,
        ) if all_working_sets else 0,
        "average_first_set_weight": average(first_set_weights),
        "average_first_set_rir": average(first_set_rirs),
        "latest_first_set_weight": float(latest_first_set.weight_used) if latest_first_set else None,
        "latest_first_set_reps": latest_first_set.reps_completed if latest_first_set else None,
        "latest_first_set_rir": latest_first_set.rir if latest_first_set else None,
        "latest_first_set_failed": bool(latest_first_set.reached_failure) if latest_first_set else False,
    }


def confidence_from_history(summary):
    if summary["usable_session_count"] >= MIN_HISTORY_FOR_HIGH_CONFIDENCE:
        return "alta"

    if summary["usable_session_count"] >= 2:
        return "média"

    return "baixa"


def calculate_first_working_set_from_history(recent_session_sets, target_reps=TARGET_REPS):
    summary = summarize_recent_sessions(recent_session_sets, target_reps)
    latest_weight = summary["latest_first_set_weight"]

    if latest_weight is None:
        return {
            "recommended_weight": "",
            "recommended_reps": target_reps,
            "reason": "Sem histórico suficiente para prever a primeira série normal.",
            "confidence": "baixa",
            "decision_basis": ["Sem séries normais anteriores neste treino"],
            "history_summary": summary,
            "source": "last_15_workout_history",
        }

    should_reduce = (
        summary["latest_first_set_failed"]
        or summary["latest_first_set_reps"] < target_reps
        or summary["first_set_success_rate"] < 0.5
        or summary["working_set_failure_rate"] >= 0.5
    )
    should_increase = (
        summary["usable_session_count"] >= 2
        and summary["first_set_success_rate"] >= 0.8
        and summary["first_set_reserve_rate"] >= 0.6
        and summary["working_set_failure_rate"] <= 0.25
        and summary["latest_first_set_rir"] is not None
        and summary["latest_first_set_rir"] >= 2
    )

    if should_reduce:
        return {
            "recommended_weight": round_recommended_weight(max(latest_weight - WEIGHT_STEP, 0)),
            "recommended_reps": target_reps,
            "reason": "O histórico recente mostra falhas ou reps insuficientes na primeira série. Começa ligeiramente mais baixo.",
            "confidence": confidence_from_history(summary),
            "decision_basis": [
                f"{summary['usable_session_count']} treino(s) recentes analisados",
                "Falhas ou misses pesaram contra subir carga",
            ],
            "history_summary": summary,
            "source": "last_15_workout_history",
        }

    if should_increase:
        return {
            "recommended_weight": round_recommended_weight(latest_weight + WEIGHT_STEP),
            "recommended_reps": target_reps,
            "reason": "O histórico recente mostra primeiras séries fortes e com margem. Começa um passo acima.",
            "confidence": confidence_from_history(summary),
            "decision_basis": [
                f"{summary['usable_session_count']} treino(s) recentes analisados",
                "Primeiras séries chegaram ao alvo com margem",
            ],
            "history_summary": summary,
            "source": "last_15_workout_history",
        }

    return {
        "recommended_weight": round_recommended_weight(latest_weight),
        "recommended_reps": target_reps,
        "reason": "O histórico recente pede consolidação. Começa com a mesma carga da primeira série anterior.",
        "confidence": confidence_from_history(summary),
        "decision_basis": [
            f"{summary['usable_session_count']} treino(s) recentes analisados",
            "Sinais mistos: manter é mais seguro do que subir",
        ],
        "history_summary": summary,
        "source": "last_15_workout_history",
    }


def calculate_warmup_from_first_working_set(first_working_set, target_reps=TARGET_REPS):
    first_weight = number_or_none(first_working_set.get("recommended_weight"))

    if first_weight is None:
        return {
            "recommended_weight": "",
            "recommended_reps": "",
            "reason": "Aquecimento depende da primeira série normal prevista.",
            "confidence": "baixa",
            "decision_basis": ["Sem carga prevista para a primeira série normal"],
            "source": "warmup_from_first_working_set",
        }

    warmup_ratio = 0.5 if first_weight >= 30 else 0.6

    return {
        "recommended_weight": round_recommended_weight(first_weight * warmup_ratio),
        "recommended_reps": min(target_reps, 10),
        "reason": "Aquecimento calculado como proporção direta da primeira série normal prevista.",
        "confidence": first_working_set.get("confidence", "média"),
        "decision_basis": [
            f"Primeira série normal prevista: {first_weight}kg",
            f"Aquecimento a {int(warmup_ratio * 100)}% da carga alvo",
        ],
        "source": "warmup_from_first_working_set",
    }


def build_history_based_recommended_sets(recent_session_sets, planned_working_sets, target_reps=TARGET_REPS):
    first_working_set = calculate_first_working_set_from_history(recent_session_sets, target_reps)
    warmup_set = calculate_warmup_from_first_working_set(first_working_set, target_reps)
    recommended_sets = [
        {
            "set_number": 1,
            "set_type": "WARMUP",
            **warmup_set,
        }
    ]

    for set_number in range(1, planned_working_sets + 1):
        if set_number == 1:
            set_recommendation = first_working_set
        else:
            set_recommendation = {
                **first_working_set,
                "reason": "Esta série começa pela previsão do histórico e será ajustada depois das séries anteriores de hoje.",
                "decision_basis": [
                    *first_working_set.get("decision_basis", []),
                    "Será recalculada com o desempenho da sessão atual",
                ],
            }

        recommended_sets.append(
            {
                "set_number": set_number + 1,
                "set_type": "WORKING",
                **set_recommendation,
            }
        )

    return recommended_sets
