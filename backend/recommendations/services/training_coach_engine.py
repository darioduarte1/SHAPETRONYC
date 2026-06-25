import re


DEFAULT_TARGET_MIN_REPS = 10
DEFAULT_TARGET_MAX_REPS = 12
DEFAULT_TARGET_RIR = 2
WEIGHT_STEP = 2.5
HIGH_READINESS_SCORE = 70
MEDIUM_READINESS_SCORE = 50
MAX_EXTRA_PRODUCTIVE_SETS = 1
MIN_WORKING_SETS_BEFORE_STOP = 2

ALLOWED_ACTIONS = {
    "increase_weight",
    "maintain_weight",
    "decrease_weight",
    "add_set",
    "stop_exercise",
    "do_backoff_set",
    "skip_backoff_set",
    "deload",
    "reduce_volume",
    "increase_volume",
    "flag_pain_or_risk",
    "suggest_exercise_replacement",
}

PAIN_OR_RISK_KEYWORDS = [
    "dor",
    "dores",
    "articular",
    "ombro",
    "cotovelo",
    "joelho",
    "lombar",
    "tontura",
    "tonto",
    "risco",
    "pontada",
]

NO_PAIN_KEYWORDS = [
    "sem dor",
    "sem dores",
    "não tenho dor",
    "nao tenho dor",
    "não senti dor",
    "nao senti dor",
    "sem desconforto",
]

BAD_TECHNIQUE_KEYWORDS = [
    "técnica má",
    "tecnica má",
    "técnica ma",
    "tecnica ma",
    "perdi técnica",
    "perdi tecnica",
    "forma má",
    "forma ma",
    "instável",
    "instavel",
]

STRONG_FATIGUE_KEYWORDS = [
    "muito cansado",
    "cansaço",
    "exausto",
    "exaustão",
    "exaustao",
    "sem energia",
    "fadiga forte",
    "muito pesado",
]

READINESS_NEGATIVE_KEYWORDS = [
    "dormi mal",
    "sono mau",
    "stress",
    "desmotivado",
    "indisposto",
    "motivação baixa",
    "motivacao baixa",
]

STOP_REQUEST_KEYWORDS = [
    "quero parar",
    "vou parar",
    "não quero continuar",
    "nao quero continuar",
    "quero desistir",
]

NO_INCREASE_KEYWORDS = [
    "não quero subir",
    "nao quero subir",
    "não subir",
    "nao subir",
    "não aumentes",
    "nao aumentes",
]


def normalize_text(value):
    return str(value or "").lower().strip()


def notes_include(notes, keywords):
    normalized_notes = normalize_text(notes)

    for keyword in keywords:
        if len(keyword) <= 3:
            if re.search(rf"(^|\W){re.escape(keyword)}(\W|$)", normalized_notes):
                return True
        elif keyword in normalized_notes:
            return True

    return False


def has_pain_or_risk(notes):
    if notes_include(notes, NO_PAIN_KEYWORDS):
        return False

    return notes_include(notes, PAIN_OR_RISK_KEYWORDS)


def has_bad_technique(notes):
    return notes_include(notes, BAD_TECHNIQUE_KEYWORDS)


def has_strong_fatigue(notes):
    return notes_include(notes, STRONG_FATIGUE_KEYWORDS)


def has_stop_request(notes):
    return notes_include(notes, STOP_REQUEST_KEYWORDS)


def has_no_increase_request(notes):
    return notes_include(notes, NO_INCREASE_KEYWORDS)


def has_negative_feedback(notes):
    return (
        has_pain_or_risk(notes)
        or has_bad_technique(notes)
        or has_strong_fatigue(notes)
        or has_stop_request(notes)
        or has_no_increase_request(notes)
        or notes_include(notes, READINESS_NEGATIVE_KEYWORDS)
    )


def number_or_none(value):
    if value in ("", None):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def int_or_default(value, default):
    parsed_value = number_or_none(value)

    if parsed_value is None:
        return default

    return int(parsed_value)


def clamp(value, minimum, maximum):
    return max(minimum, min(value, maximum))


def average(values):
    clean_values = [value for value in values if value is not None]

    if not clean_values:
        return None

    return round(sum(clean_values) / len(clean_values), 1)


def round_recommended_weight(weight):
    return round(float(max(weight, 0)) * 2) / 2


def target_reps_label(target_min_reps, target_max_reps):
    if target_min_reps == target_max_reps:
        return str(target_max_reps)

    return f"{target_min_reps}-{target_max_reps}"


def is_working_set(set_log):
    return set_log.get("set_type", "WORKING") == "WORKING"


def set_reached_failure(set_log, target_min_reps=DEFAULT_TARGET_MIN_REPS):
    reps = number_or_none(set_log.get("reps_completed"))

    return bool(set_log.get("reached_failure")) or reps is not None and reps < target_min_reps


def set_has_reserve(set_log, target_max_reps=DEFAULT_TARGET_MAX_REPS, target_rir=DEFAULT_TARGET_RIR):
    rir = number_or_none(set_log.get("rir"))
    reps = number_or_none(set_log.get("reps_completed"))

    return (
        reps is not None
        and reps >= target_max_reps
        and rir is not None
        and rir >= target_rir
        and not bool(set_log.get("reached_failure"))
    )


def summarize_working_sets(sets, target_min_reps, target_max_reps, target_rir):
    working_sets = [set_log for set_log in sets if is_working_set(set_log)]
    missed_sets = [
        set_log
        for set_log in working_sets
        if set_reached_failure(set_log, target_min_reps)
        or (number_or_none(set_log.get("rir")) is not None and number_or_none(set_log.get("rir")) < target_rir)
    ]
    reserve_sets = [
        set_log
        for set_log in working_sets
        if set_has_reserve(set_log, target_max_reps, target_rir)
    ]
    rir_values = [number_or_none(set_log.get("rir")) for set_log in working_sets]
    weights = [number_or_none(set_log.get("weight_used")) for set_log in working_sets]
    reps = [number_or_none(set_log.get("reps_completed")) for set_log in working_sets]

    return {
        "working_set_count": len(working_sets),
        "missed_set_count": len(missed_sets),
        "reserve_set_count": len(reserve_sets),
        "failure_count": len([set_log for set_log in working_sets if set_log.get("reached_failure")]),
        "average_rir": average(rir_values),
        "average_reps": average(reps),
        "last_weight": next((weight for weight in reversed(weights) if weight is not None), None),
        "missed_ratio": round(len(missed_sets) / len(working_sets), 2) if working_sets else 0,
        "reserve_ratio": round(len(reserve_sets) / len(working_sets), 2) if working_sets else 0,
    }


def group_sets_by_session(sets):
    grouped_sets = {}

    for set_log in sets:
        session_id = set_log.get("workout_session") or set_log.get("session_id") or "unknown"
        grouped_sets.setdefault(session_id, []).append(set_log)

    return list(grouped_sets.values())


def summarize_history(history_sets, target_min_reps, target_max_reps, target_rir):
    recent_session_sets = group_sets_by_session(history_sets)[:15]
    working_sets = [set_log for session_sets in recent_session_sets for set_log in session_sets if is_working_set(set_log)]
    failed_sets = [set_log for set_log in working_sets if set_reached_failure(set_log, target_min_reps)]
    negative_notes = [
        set_log
        for set_log in working_sets
        if has_negative_feedback(set_log.get("notes", "")) or has_negative_feedback(set_log.get("session_notes", ""))
    ]
    successful_sessions = 0

    for session_sets in recent_session_sets[:3]:
        session_working_sets = [set_log for set_log in session_sets if is_working_set(set_log)]

        if session_working_sets and all(
            set_has_reserve(set_log, target_max_reps, target_rir)
            for set_log in session_working_sets
        ):
            successful_sessions += 1

    first_half = working_sets[: max(1, len(working_sets) // 2)]
    second_half = working_sets[max(1, len(working_sets) // 2):]
    recent_average_reps = average([number_or_none(set_log.get("reps_completed")) for set_log in first_half])
    older_average_reps = average([number_or_none(set_log.get("reps_completed")) for set_log in second_half])
    recent_average_weight = average([number_or_none(set_log.get("weight_used")) for set_log in first_half])
    older_average_weight = average([number_or_none(set_log.get("weight_used")) for set_log in second_half])
    trend = "no_history"

    if working_sets and older_average_reps is not None and recent_average_reps is not None:
        if (
            recent_average_reps >= older_average_reps
            and (older_average_weight is None or recent_average_weight is None or recent_average_weight >= older_average_weight)
            and len(failed_sets) <= max(1, len(working_sets) * 0.25)
        ):
            trend = "positive"
        elif recent_average_reps < older_average_reps or len(failed_sets) >= max(2, len(working_sets) * 0.4):
            trend = "regression"
        else:
            trend = "stable"

    return {
        "session_count": len(recent_session_sets),
        "working_set_count": len(working_sets),
        "failure_count": len(failed_sets),
        "failure_rate": round(len(failed_sets) / len(working_sets), 2) if working_sets else 0,
        "negative_note_count": len(negative_notes),
        "recent_successful_sessions": successful_sessions,
        "trend": trend,
        "average_rir": average([number_or_none(set_log.get("rir")) for set_log in working_sets]),
    }


def find_previous_matching_set(previous_sets, set_number):
    if set_number is None:
        return None

    for set_log in previous_sets:
        if is_working_set(set_log) and set_log.get("set_number") == set_number:
            return set_log

    return None


def calculate_performance_drop(current_sets, current_reps):
    working_sets = [set_log for set_log in current_sets if is_working_set(set_log)]

    if not working_sets:
        return 0

    first_reps = number_or_none(working_sets[0].get("reps_completed"))

    if not first_reps or current_reps is None:
        return 0

    return round(max(0, (first_reps - current_reps) / first_reps) * 100, 1)


def build_history_signal(weight, reps, rir, is_failure, previous_matching_set):
    if not previous_matching_set:
        return "no_history"

    previous_weight = number_or_none(previous_matching_set.get("weight_used"))
    previous_reps = number_or_none(previous_matching_set.get("reps_completed"))
    previous_rir = number_or_none(previous_matching_set.get("rir"))

    if previous_weight is None or previous_reps is None:
        return "no_history"

    if weight >= previous_weight and reps >= previous_reps and not is_failure:
        if previous_rir is None or rir is None or rir >= previous_rir:
            return "improving"

        return "stable"

    if weight <= previous_weight and reps < previous_reps:
        return "regressing"

    return "stable"


def build_exercise_context(
    current_sets,
    previous_sets,
    history_sets,
    weight,
    reps,
    rir,
    is_failure,
    set_number,
    target_min_reps,
    target_max_reps,
    target_rir,
):
    working_sets = [set_log for set_log in current_sets if is_working_set(set_log)]
    consecutive_working_misses = 0

    for set_log in reversed(working_sets):
        if set_reached_failure(set_log, target_min_reps):
            consecutive_working_misses += 1
        else:
            break

    previous_matching_set = find_previous_matching_set(previous_sets, set_number)

    return {
        "completed_set_count": len(current_sets),
        "working_set_count": len(working_sets),
        "consecutive_working_misses": consecutive_working_misses,
        "previous_working_set": working_sets[-2] if len(working_sets) >= 2 else None,
        "last_two_working_sets": working_sets[-2:],
        "current_summary": summarize_working_sets(current_sets, target_min_reps, target_max_reps, target_rir),
        "previous_summary": summarize_working_sets(previous_sets, target_min_reps, target_max_reps, target_rir),
        "history_summary": summarize_working_sets(history_sets, target_min_reps, target_max_reps, target_rir),
        "history_analysis": summarize_history(history_sets, target_min_reps, target_max_reps, target_rir),
        "all_current_sets": current_sets,
        "performance_drop_percent": calculate_performance_drop(current_sets, reps),
        "history_signal": build_history_signal(
            weight,
            reps,
            rir,
            is_failure,
            previous_matching_set,
        ),
        "previous_matching_set": previous_matching_set,
    }


def calculate_fatigue_score(reps, rir, is_failure, notes, context, target_min_reps, target_rir, planned_sets):
    score = 20
    performance_drop = context["performance_drop_percent"]

    if reps < target_min_reps:
        score += 20

    if is_failure:
        score += 20

    if rir is not None:
        if rir <= 0 and target_rir >= 2:
            score += 20
        elif rir < target_rir:
            score += 12

    if performance_drop >= 35:
        score += 35
    elif performance_drop >= 25:
        score += 25
    elif performance_drop >= 15:
        score += 12

    if has_strong_fatigue(notes):
        score += 25

    if context["consecutive_working_misses"] >= 2:
        score += 18

    if context["working_set_count"] > (planned_sets or 3):
        score += 8

    score += int(context["history_analysis"]["failure_rate"] * 15)

    return clamp(score, 0, 100)


def calculate_readiness_score(reps, rir, is_failure, notes, context, target_min_reps, target_max_reps, target_rir):
    score = 55

    if reps >= target_max_reps:
        score += 15
    elif reps >= target_min_reps:
        score += 6
    else:
        score -= 24

    if is_failure:
        score -= 22

    if rir is not None:
        if rir >= target_rir + 1:
            score += 12
        elif rir >= target_rir:
            score += 6
        elif rir <= 0:
            score -= 18
        else:
            score -= 10

    if context["performance_drop_percent"] >= 35:
        score -= 30
    elif context["performance_drop_percent"] >= 25:
        score -= 20
    elif context["performance_drop_percent"] >= 15:
        score -= 10

    if context["history_signal"] == "improving":
        score += 8
    elif context["history_signal"] == "regressing":
        score -= 12

    if context["history_analysis"]["trend"] == "positive":
        score += 5
    elif context["history_analysis"]["trend"] == "regression":
        score -= 12

    if has_no_increase_request(notes) or notes_include(notes, READINESS_NEGATIVE_KEYWORDS):
        score -= 18

    if has_strong_fatigue(notes):
        score -= 24

    if has_pain_or_risk(notes) or has_bad_technique(notes) or has_stop_request(notes):
        score -= 45

    return clamp(score, 0, 100)


def calculate_recovery_score(notes, context, fatigue_score, user_context):
    score = 72
    history = context["history_analysis"]
    days_per_week = int_or_default(user_context.get("days_per_week"), 3)

    score -= int(history["failure_rate"] * 25)
    score -= min(history["negative_note_count"] * 4, 18)

    if history["trend"] == "regression":
        score -= 14
    elif history["trend"] == "positive":
        score += 6

    if days_per_week >= 6:
        score -= 8

    if fatigue_score >= 80:
        score -= 22
    elif fatigue_score >= 60:
        score -= 12

    if has_strong_fatigue(notes) or notes_include(notes, READINESS_NEGATIVE_KEYWORDS):
        score -= 18

    if has_pain_or_risk(notes):
        score -= 25

    return clamp(score, 0, 100)


def confidence_from_scores(readiness_score, fatigue_score, recovery_score):
    if readiness_score >= HIGH_READINESS_SCORE and fatigue_score < 50 and recovery_score >= 60:
        return "alta"

    if readiness_score >= MEDIUM_READINESS_SCORE and fatigue_score < 75:
        return "média"

    return "baixa"


def public_context(context, previous_sets, planned_sets):
    return {
        "completed_set_count": context["completed_set_count"],
        "working_set_count": context["working_set_count"],
        "planned_sets": planned_sets,
        "consecutive_working_misses": context["consecutive_working_misses"],
        "previous_history_count": len(previous_sets),
        "performance_drop_percent": context["performance_drop_percent"],
        "current_summary": context["current_summary"],
        "previous_summary": context["previous_summary"],
        "history_summary": context["history_summary"],
        "history_analysis": context["history_analysis"],
        "history_signal": context["history_signal"],
    }


def with_decision_metadata(
    decision,
    context,
    previous_sets,
    planned_sets,
    readiness_score,
    fatigue_score,
    recovery_score,
    target_min_reps,
    target_max_reps,
    target_rir,
    decision_basis,
    guardrails=None,
):
    action = decision.get("action", "maintain_weight")

    if action not in ALLOWED_ACTIONS:
        action = "maintain_weight"

    stop_exercise = bool(decision.get("stop_exercise", False))
    add_set = bool(decision.get("add_set", False))
    do_backoff_set = bool(decision.get("do_backoff_set", False))

    if stop_exercise:
        add_set = False
        do_backoff_set = False

    return {
        **decision,
        "action": action,
        "target_reps": decision.get("target_reps", target_max_reps),
        "target_reps_label": target_reps_label(target_min_reps, target_max_reps),
        "target_rir": decision.get("target_rir", target_rir),
        "add_set": add_set,
        "stop_exercise": stop_exercise,
        "do_backoff_set": do_backoff_set,
        "backoff_weight": decision.get("backoff_weight"),
        "confidence": confidence_from_scores(readiness_score, fatigue_score, recovery_score),
        "readiness_score": readiness_score,
        "fatigue_score": fatigue_score,
        "recovery_score": recovery_score,
        "decision_basis": decision_basis,
        "context": public_context(context, previous_sets, planned_sets),
        "guardrails": guardrails or {},
        "source": "hybrid_local_training_coach",
    }


def infer_first_working_weight(context, fallback_weight):
    previous_weight = context["previous_summary"].get("last_weight")

    if previous_weight:
        return previous_weight

    history_weight = context["history_summary"].get("last_weight")

    if history_weight:
        return history_weight

    return fallback_weight


def calculate_increase_step(weight, exercise_context):
    movement_pattern = normalize_text(exercise_context.get("movement_pattern"))
    equipment = normalize_text(exercise_context.get("equipment"))
    is_compound = bool(exercise_context.get("is_compound"))

    if "dumbbell" in equipment or "halter" in equipment:
        return WEIGHT_STEP

    if "machine" in equipment or "máquina" in equipment or "maquina" in equipment:
        return WEIGHT_STEP

    if movement_pattern in {"squat", "hinge", "lunge", "hip_thrust"} and is_compound:
        return max(WEIGHT_STEP, round_recommended_weight(weight * 0.05))

    if movement_pattern == "isolation" or not is_compound:
        return max(1, min(WEIGHT_STEP, round_recommended_weight(weight * 0.025)))

    return max(WEIGHT_STEP, round_recommended_weight(weight * 0.025))


def reduce_weight(weight, percent):
    return round_recommended_weight(weight * (1 - percent))


def backoff_weight(weight, fatigue_score, is_failure, exercise_context):
    if not bool(exercise_context.get("is_compound")):
        return reduce_weight(weight, 0.1)

    if is_failure or fatigue_score >= 60:
        return reduce_weight(weight, 0.15)

    return reduce_weight(weight, 0.1)


def next_warmup_weight(current_weight, first_working_weight):
    if not first_working_weight:
        return current_weight

    target = first_working_weight * 0.75

    if current_weight >= target:
        return current_weight

    return round_recommended_weight(min(target, current_weight + WEIGHT_STEP * 2))


def should_continue_warming_up(weight, context):
    first_working_weight = infer_first_working_weight(context, weight)
    completed_warmups = len(
        [set_log for set_log in context["all_current_sets"] if set_log.get("set_type") == "WARMUP"]
    )

    if completed_warmups >= 3 or not first_working_weight:
        return False

    if weight < first_working_weight * 0.65:
        return True

    return False


def should_stop_exercise(context, planned_sets, readiness_score, fatigue_score):
    working_count = context["working_set_count"]
    current_summary = context["current_summary"]
    planned_sets = planned_sets or 3
    max_productive_sets = planned_sets + MAX_EXTRA_PRODUCTIVE_SETS
    latest_working_set = context["last_two_working_sets"][-1] if context["last_two_working_sets"] else None
    latest_set_recovered = latest_working_set is not None and set_has_reserve(latest_working_set)

    if working_count == 0:
        return False

    if context["performance_drop_percent"] >= 35:
        return True

    if fatigue_score > 80:
        return True

    if context["consecutive_working_misses"] >= 2:
        return True

    if working_count >= MIN_WORKING_SETS_BEFORE_STOP and readiness_score < MEDIUM_READINESS_SCORE:
        return True

    if (
        working_count >= MIN_WORKING_SETS_BEFORE_STOP
        and current_summary["missed_ratio"] >= 0.5
        and not latest_set_recovered
    ):
        return True

    if working_count >= planned_sets and current_summary["reserve_ratio"] < 0.8:
        return True

    return working_count >= max_productive_sets


def can_add_productive_set(context, planned_sets, readiness_score, fatigue_score, recovery_score, exercise_context):
    working_count = context["working_set_count"]
    planned_sets = planned_sets or 3

    if working_count < planned_sets:
        return True

    if working_count >= planned_sets + MAX_EXTRA_PRODUCTIVE_SETS:
        return False

    if bool(exercise_context.get("is_compound")) and working_count >= planned_sets:
        return False

    return (
        readiness_score >= 82
        and fatigue_score < 35
        and recovery_score >= 70
        and context["current_summary"]["missed_set_count"] == 0
        and context["current_summary"]["reserve_ratio"] >= 0.8
    )


def safety_guardrails(notes, reps, is_failure, target_min_reps, fatigue_score, context):
    return {
        "has_pain_or_risk": has_pain_or_risk(notes),
        "has_bad_technique": has_bad_technique(notes),
        "has_stop_request": has_stop_request(notes),
        "has_no_increase_request": has_no_increase_request(notes),
        "block_increase": (
            has_negative_feedback(notes)
            or is_failure
            or reps < target_min_reps
            or fatigue_score >= 60
            or context["performance_drop_percent"] >= 15
            or context["history_analysis"]["trend"] == "regression"
        ),
        "must_stop": (
            has_pain_or_risk(notes)
            or has_bad_technique(notes)
            or has_stop_request(notes)
            or fatigue_score > 80
            or context["performance_drop_percent"] >= 35
        ),
    }


def make_stop_decision(action, reason, title, message):
    return {
        "recommended_weight": "",
        "target_reps": "",
        "recommended_rest_seconds": 0,
        "next_set_type": "COMPLETE",
        "exercise_status": "complete",
        "action": action,
        "add_set": False,
        "stop_exercise": True,
        "do_backoff_set": False,
        "backoff_weight": None,
        "reason": reason,
        "guidance_title": title,
        "guidance_message": message,
    }


def calculate_training_coach_decision(
    weight,
    reps,
    rir=None,
    is_failure=False,
    notes="",
    set_type="WORKING",
    set_number=None,
    total_sets=None,
    current_sets=None,
    previous_sets=None,
    history_sets=None,
    target_min_reps=DEFAULT_TARGET_MIN_REPS,
    target_max_reps=DEFAULT_TARGET_MAX_REPS,
    target_rir=DEFAULT_TARGET_RIR,
    exercise_context=None,
    user_context=None,
    session_context=None,
):
    current_sets = current_sets or []
    previous_sets = previous_sets or []
    history_sets = (history_sets or previous_sets)[:150]
    exercise_context = exercise_context or {}
    user_context = user_context or {}
    session_context = session_context or {}
    weight = number_or_none(weight) or 0
    reps = int_or_default(reps, 0)
    rir = None if rir in ("", None) else int_or_default(rir, 0)
    planned_sets = int_or_default(total_sets or session_context.get("planned_sets"), 3)
    target_min_reps = int_or_default(target_min_reps, DEFAULT_TARGET_MIN_REPS)
    target_max_reps = int_or_default(target_max_reps, DEFAULT_TARGET_MAX_REPS)
    target_rir = int_or_default(target_rir, DEFAULT_TARGET_RIR)
    target_reps = target_max_reps
    is_warmup = set_type == "WARMUP"

    if is_warmup:
        rir = None
        is_failure = False

    scoring_reps = target_max_reps if is_warmup else reps

    context = build_exercise_context(
        current_sets,
        previous_sets,
        history_sets,
        weight,
        scoring_reps,
        rir,
        is_failure,
        set_number,
        target_min_reps,
        target_max_reps,
        target_rir,
    )
    fatigue_score = calculate_fatigue_score(
        scoring_reps,
        rir,
        is_failure,
        notes,
        context,
        target_min_reps,
        target_rir,
        planned_sets,
    )
    readiness_score = calculate_readiness_score(
        scoring_reps,
        rir,
        is_failure,
        notes,
        context,
        target_min_reps,
        target_max_reps,
        target_rir,
    )
    recovery_score = calculate_recovery_score(notes, context, fatigue_score, user_context)
    guardrails = safety_guardrails(notes, scoring_reps, is_failure, target_min_reps, fatigue_score, context)

    if guardrails["has_pain_or_risk"] or guardrails["has_bad_technique"] or guardrails["has_stop_request"]:
        return with_decision_metadata(
            make_stop_decision(
                "flag_pain_or_risk" if guardrails["has_pain_or_risk"] else "stop_exercise",
                "O feedback do utilizador indica dor, risco, perda técnica ou vontade de parar. A segurança tem prioridade absoluta.",
                "Termina este exercício",
                "Para aqui neste exercício e volta a treinar este padrão apenas quando a sensação estiver controlada.",
            ),
            context,
            previous_sets,
            planned_sets,
            readiness_score,
            fatigue_score,
            recovery_score,
            target_min_reps,
            target_max_reps,
            target_rir,
            ["Feedback do utilizador teve prioridade sobre a performance", "Segurança acima de progressão"],
            guardrails,
        )

    if is_warmup:
        completed_warmups = len([set_log for set_log in current_sets if set_log.get("set_type") == "WARMUP"])
        first_working_weight = infer_first_working_weight(context, weight)

        if should_continue_warming_up(weight, context):
            recommended_weight = next_warmup_weight(weight, first_working_weight)

            return with_decision_metadata(
                {
                    "recommended_weight": recommended_weight,
                    "target_reps": min(target_max_reps, 8),
                    "recommended_rest_seconds": 75,
                    "next_set_type": "WARMUP",
                    "exercise_status": "continue",
                    "action": "add_set",
                    "add_set": True,
                    "stop_exercise": False,
                    "do_backoff_set": False,
                    "backoff_weight": None,
                    "reason": "Ainda vale a pena fazer mais uma série de aquecimento antes da primeira série normal.",
                    "guidance_title": "Faz mais um aquecimento",
                    "guidance_message": "A carga ainda está longe da primeira série prevista. Sobe progressivamente sem gastar fadiga.",
                },
                context,
                previous_sets,
                planned_sets,
                MEDIUM_READINESS_SCORE,
                fatigue_score,
                recovery_score,
                target_min_reps,
                target_max_reps,
                target_rir,
                [
                    f"{completed_warmups} aquecimento(s) feito(s)",
                    "Carga ainda abaixo da zona útil para começar trabalho",
                ],
                guardrails,
            )

        return with_decision_metadata(
            {
                "recommended_weight": first_working_weight,
                "target_reps": target_reps,
                "recommended_rest_seconds": 90,
                "next_set_type": "WORKING",
                "exercise_status": "continue",
                "action": "maintain_weight",
                "add_set": False,
                "stop_exercise": False,
                "do_backoff_set": False,
                "backoff_weight": None,
                "reason": "Aquecimento registado. A próxima decisão deve aproximar o user da série normal.",
                "guidance_title": "Prepara a primeira série normal",
                "guidance_message": "Aquecimento suficiente. A próxima série deve começar o trabalho efetivo do exercício.",
            },
            context,
            previous_sets,
            planned_sets,
            MEDIUM_READINESS_SCORE,
            fatigue_score,
            recovery_score,
            target_min_reps,
            target_max_reps,
            target_rir,
            [
                f"{completed_warmups} aquecimento(s) feito(s)",
                "Próxima série passa a contar como trabalho",
            ],
            guardrails,
        )

    if should_stop_exercise(context, planned_sets, readiness_score, fatigue_score):
        return with_decision_metadata(
            make_stop_decision(
                "stop_exercise",
                "A queda de performance, falhas ou fadiga acumulada tornam a próxima série menos útil do que recuperar.",
                "Termina este exercício",
                "Passa para o próximo exercício e preserva performance para o resto do treino.",
            ),
            context,
            previous_sets,
            planned_sets,
            readiness_score,
            fatigue_score,
            recovery_score,
            target_min_reps,
            target_max_reps,
            target_rir,
            [
                f"{context['working_set_count']} série(s) de trabalho feitas",
                f"Fadiga estimada: {fatigue_score}/100",
            ],
            guardrails,
        )

    if reps < target_min_reps or is_failure or (rir is not None and rir <= 0 and target_rir >= 2):
        if (
            bool(exercise_context.get("is_compound"))
            and reps >= max(1, target_min_reps - 1)
            and not has_strong_fatigue(notes)
            and context["working_set_count"] < planned_sets
        ):
            recommended_backoff_weight = backoff_weight(weight, fatigue_score, is_failure, exercise_context)

            return with_decision_metadata(
                {
                    "recommended_weight": recommended_backoff_weight,
                    "target_reps": target_reps,
                    "recommended_rest_seconds": 180,
                    "next_set_type": "DROP",
                    "exercise_status": "continue",
                    "action": "do_backoff_set",
                    "add_set": True,
                    "stop_exercise": False,
                    "do_backoff_set": True,
                    "backoff_weight": recommended_backoff_weight,
                    "reason": "A série ficou muito perto do limite, mas ainda há espaço seguro para acumular volume com menos carga.",
                    "guidance_title": "Faz uma backoff set",
                    "guidance_message": "Baixa a carga, mantém técnica limpa e evita nova falha.",
                },
                context,
                previous_sets,
                planned_sets,
                readiness_score,
                fatigue_score,
                recovery_score,
                target_min_reps,
                target_max_reps,
                target_rir,
                ["Exercício composto", "Falha ou RIR muito baixo", "Backoff reduz stress mantendo volume útil"],
                guardrails,
            )

        reduction = 0.05

        if reps <= target_min_reps - 2 or is_failure or context["performance_drop_percent"] >= 25:
            reduction = 0.10

        if fatigue_score >= 75:
            reduction = 0.15

        return with_decision_metadata(
            {
                "recommended_weight": reduce_weight(weight, reduction),
                "target_reps": target_reps,
                "recommended_rest_seconds": 150 if reduction <= 0.10 else 180,
                "next_set_type": "WORKING",
                "exercise_status": "continue",
                "action": "decrease_weight",
                "add_set": context["working_set_count"] < planned_sets,
                "stop_exercise": False,
                "do_backoff_set": False,
                "backoff_weight": None,
                "reason": "A série ficou abaixo da faixa alvo ou demasiado perto da falha. Reduzir carga protege técnica e recuperação.",
                "guidance_title": "Baixa a carga",
                "guidance_message": "Volta à faixa de reps com melhor controlo antes de pensar em progressão.",
            },
            context,
            previous_sets,
            planned_sets,
            readiness_score,
            fatigue_score,
            recovery_score,
            target_min_reps,
            target_max_reps,
            target_rir,
            ["Reps abaixo do mínimo ou esforço acima do alvo", "Progressão bloqueada por fadiga"],
            guardrails,
        )

    if has_negative_feedback(notes):
        return with_decision_metadata(
            {
                "recommended_weight": weight,
                "target_reps": target_reps,
                "recommended_rest_seconds": 150,
                "next_set_type": "WORKING",
                "exercise_status": "continue",
                "action": "maintain_weight",
                "add_set": context["working_set_count"] < planned_sets,
                "stop_exercise": False,
                "do_backoff_set": False,
                "backoff_weight": None,
                "reason": "Apesar da performance permitir mais, o feedback indica baixa prontidão. O feedback do utilizador tem prioridade.",
                "guidance_title": "Mantém a carga",
                "guidance_message": "Repete a carga com boa técnica e evita transformar hoje num teste de progressão.",
            },
            context,
            previous_sets,
            planned_sets,
            readiness_score,
            fatigue_score,
            recovery_score,
            target_min_reps,
            target_max_reps,
            target_rir,
            ["Notas indicam fadiga, stress, sono mau ou recusa de subir", "Feedback do utilizador bloqueia subida"],
            guardrails,
        )

    previous_working_set = context["previous_working_set"]

    if previous_working_set and set_reached_failure(previous_working_set, target_min_reps) and rir is not None and rir >= target_rir:
        return with_decision_metadata(
            {
                "recommended_weight": weight,
                "target_reps": target_reps,
                "recommended_rest_seconds": 150,
                "next_set_type": "WORKING",
                "exercise_status": "continue",
                "action": "maintain_weight",
                "add_set": context["working_set_count"] < planned_sets,
                "stop_exercise": False,
                "do_backoff_set": False,
                "backoff_weight": None,
                "reason": "A série anterior falhou o alvo. Apesar da melhoria agora, mantém a carga para estabilizar.",
                "guidance_title": "Estabiliza a carga",
                "guidance_message": "Confirma outra série sólida antes de aumentar peso.",
            },
            context,
            previous_sets,
            planned_sets,
            readiness_score,
            fatigue_score,
            recovery_score,
            target_min_reps,
            target_max_reps,
            target_rir,
            ["A série anterior falhou o alvo", "A série atual melhorou, mas ainda pede consolidação"],
            guardrails,
        )

    if context["history_signal"] == "regressing" or context["history_analysis"]["trend"] == "regression":
        return with_decision_metadata(
            {
                "recommended_weight": weight,
                "target_reps": target_reps,
                "recommended_rest_seconds": 150,
                "next_set_type": "WORKING",
                "exercise_status": "continue",
                "action": "maintain_weight",
                "add_set": context["working_set_count"] < planned_sets,
                "stop_exercise": False,
                "do_backoff_set": False,
                "backoff_weight": None,
                "reason": "O histórico recente mostra regressão ou recuperação instável. Mantém a carga antes de tentar subir.",
                "guidance_title": "Consolida antes de subir",
                "guidance_message": "Procura estabilidade de reps e RIR antes de nova progressão.",
            },
            context,
            previous_sets,
            planned_sets,
            readiness_score,
            fatigue_score,
            recovery_score,
            target_min_reps,
            target_max_reps,
            target_rir,
            ["Histórico recente não sustenta progressão", "Subida bloqueada até estabilizar performance"],
            guardrails,
        )

    if reps >= target_max_reps and rir is not None and rir >= target_rir and not guardrails["block_increase"]:
        step = calculate_increase_step(weight, exercise_context)
        next_working_set_allowed = can_add_productive_set(
            context,
            planned_sets,
            readiness_score,
            fatigue_score,
            recovery_score,
            exercise_context,
        )

        if next_working_set_allowed:
            action = "increase_weight" if context["working_set_count"] <= planned_sets else "increase_volume"

            return with_decision_metadata(
                {
                    "recommended_weight": round_recommended_weight(weight + step),
                    "target_reps": target_reps,
                    "recommended_rest_seconds": 120,
                    "next_set_type": "WORKING",
                    "exercise_status": "continue",
                    "action": action,
                    "add_set": context["working_set_count"] >= planned_sets,
                    "stop_exercise": False,
                    "do_backoff_set": False,
                    "backoff_weight": None,
                    "reason": "Atingiste o topo da faixa com RIR suficiente, sem falha e sem sinais negativos. A progressão é permitida.",
                    "guidance_title": "Sobe a carga",
                    "guidance_message": "Mantém a mesma qualidade técnica e confirma se a nova carga ainda fica dentro do alvo.",
                },
                context,
                previous_sets,
                planned_sets,
                readiness_score,
                fatigue_score,
                recovery_score,
                target_min_reps,
                target_max_reps,
                target_rir,
                ["Topo da faixa atingido", "RIR dentro ou acima do alvo", "Sem dor, falha ou fadiga forte"],
                guardrails,
            )

    if context["working_set_count"] >= planned_sets:
        return with_decision_metadata(
            make_stop_decision(
                "stop_exercise",
                "O volume planeado foi cumprido e não há motivo forte para adicionar trabalho extra.",
                "Exercício cumprido",
                "Fecha este exercício e preserva recuperação para o resto do treino.",
            ),
            context,
            previous_sets,
            planned_sets,
            readiness_score,
            fatigue_score,
            recovery_score,
            target_min_reps,
            target_max_reps,
            target_rir,
            ["Volume planeado cumprido", "Progressão não deve passar à frente da recuperação"],
            guardrails,
        )

    return with_decision_metadata(
        {
            "recommended_weight": weight,
            "target_reps": target_reps,
            "recommended_rest_seconds": 120,
            "next_set_type": "WORKING",
            "exercise_status": "continue",
            "action": "maintain_weight",
            "add_set": context["working_set_count"] < planned_sets,
            "stop_exercise": False,
            "do_backoff_set": False,
            "backoff_weight": None,
            "reason": "A série ficou dentro da faixa alvo sem motivo forte para subir ou baixar.",
            "guidance_title": "Mantém a carga",
            "guidance_message": "Repete com a mesma carga e tenta manter reps, RIR e técnica estáveis.",
        },
        context,
        previous_sets,
        planned_sets,
        readiness_score,
        fatigue_score,
        recovery_score,
        target_min_reps,
        target_max_reps,
        target_rir,
        ["Resultado dentro da faixa alvo", "Sem sinal forte para progressão ou redução"],
        guardrails,
    )
