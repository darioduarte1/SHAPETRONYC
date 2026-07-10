# =============================================================================
# training_coach_engine.py
# -----------------------------------------------------------------------------
# Motor local de coaching durante o treino.
# É usado para gerar instruções imediatas série a série com base na execução atual.
# Aplica regras de falha, queda de performance, aquecimento e adaptação dentro da sessão.
# =============================================================================
import re

from exercises.services.weight_scale import (
    get_exercise_weight_scale,
    next_available_weight,
    snap_to_available_weight,
)


DEFAULT_TARGET_MIN_REPS = 10
DEFAULT_TARGET_MAX_REPS = 12
DEFAULT_TARGET_RIR = 2
WEIGHT_STEP = 2.5
HIGH_READINESS_SCORE = 70
MEDIUM_READINESS_SCORE = 50
MAX_EXTRA_PRODUCTIVE_SETS = 1
MIN_WORKING_SETS_BEFORE_STOP = 2
LARGE_MACHINE_JUMP_RATIO = 0.10
LOW_RISK_MOVEMENT_PATTERNS = {"isolation"}
LOW_RISK_EQUIPMENT_KEYWORDS = {"dumbbell", "halter", "cable", "polia"}
PRIMARY_PATTERNS = {"horizontal_push", "vertical_push", "horizontal_pull", "vertical_pull", "squat", "hinge"}
ACCESSORY_PATTERNS = {"isolation", "core"}
FINISHER_KEYWORDS = {"fly", "pushdown", "curl", "raise", "extension", "calf", "crunch"}
SAFE_ACCESSORY_KEYWORDS = {"pec deck", "lateral raise", "leg extension", "leg curl", "triceps", "biceps", "calf"}

ALLOWED_ACTIONS = {
    "increase_weight",
    "maintain_weight",
    "decrease_weight",
    "add_set",
    "maintain_or_small_backoff",
    "small_backoff",
    "stop_exercise",
    "do_backoff_set",
    "skip_backoff_set",
    "deload",
    "reduce_volume",
    "increase_volume",
    "flag_pain_or_risk",
    "suggest_exercise_replacement",
}

EXERCISE_STATES = {
    "CONTINUE",
    "ADJUST_LOAD",
    "BACKOFF",
    "FINAL_SET",
    "ADD_VOLUME",
    "END_EXERCISE",
    "SAFETY_STOP",
    "DELOAD_REQUIRED",
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

POSITIVE_FEEDBACK_KEYWORDS = [
    "fácil",
    "facil",
    "controlado",
    "podia fazer mais",
    "boa técnica",
    "boa tecnica",
    "leve",
    "energia boa",
    "senti bem",
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


def has_positive_feedback(notes):
    return notes_include(notes, POSITIVE_FEEDBACK_KEYWORDS)


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

    return reps is not None and reps < target_min_reps


def classify_failure(reps, is_failure, notes, target_min_reps, target_max_reps, context=None):
    if has_pain_or_risk(notes) or has_bad_technique(notes) or has_stop_request(notes):
        return "danger_failure"

    if not is_failure:
        if reps < target_min_reps:
            return "bad_failure"

        return "none"

    performance_drop = context.get("performance_drop_percent", 0) if context else 0

    if reps >= target_max_reps and performance_drop < 30:
        return "productive_failure"

    if reps >= target_min_reps and performance_drop < 30:
        return "acceptable_failure"

    return "bad_failure"


def failure_is_bad(failure_class):
    return failure_class in {"bad_failure", "danger_failure"}


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


def set_is_target_with_rir(set_log, minimum_rir, target_max_reps=DEFAULT_TARGET_MAX_REPS):
    reps = number_or_none(set_log.get("reps_completed"))
    rir = number_or_none(set_log.get("rir"))

    return (
        reps is not None
        and reps >= target_max_reps
        and rir is not None
        and rir >= minimum_rir
        and not bool(set_log.get("reached_failure"))
    )


def classify_set_validity(set_log):
    if set_log.get("set_type") == "WARMUP":
        return "warmup_set"

    notes = " ".join([
        str(set_log.get("notes", "")),
        str(set_log.get("session_notes", "")),
    ])
    reps = number_or_none(set_log.get("reps_completed")) or 0

    if has_pain_or_risk(notes) or has_bad_technique(notes) or has_stop_request(notes):
        return "invalid_safety_set"

    if reps <= 3 and not bool(set_log.get("reached_failure")):
        return "valid_weak_set" if has_positive_feedback(notes) else "invalid_safety_set"

    if reps < DEFAULT_TARGET_MIN_REPS:
        return "valid_weak_set"

    return "valid_productive_set"


def is_valid_working_set(set_log):
    return classify_set_validity(set_log) in {"valid_productive_set", "valid_weak_set"}


def summarize_working_sets(sets, target_min_reps, target_max_reps, target_rir):
    working_sets = [set_log for set_log in sets if is_working_set(set_log)]
    valid_working_sets = [set_log for set_log in working_sets if is_valid_working_set(set_log)]
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
        "valid_working_set_count": len(valid_working_sets),
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


def count_recent_failures_at_weight(history_sets, weight):
    target_weight = number_or_none(weight)

    if target_weight is None:
        return 0

    matching_sets = [
        set_log for set_log in history_sets[:60]
        if is_working_set(set_log)
        and number_or_none(set_log.get("weight_used")) == target_weight
    ]

    return len([
        set_log for set_log in matching_sets
        if (number_or_none(set_log.get("reps_completed")) or 0) < DEFAULT_TARGET_MIN_REPS
    ])


def best_current_working_reps(current_sets):
    reps_values = [
        number_or_none(set_log.get("reps_completed"))
        for set_log in current_sets
        if is_working_set(set_log)
    ]
    clean_values = [value for value in reps_values if value is not None]

    return max(clean_values) if clean_values else None


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
    valid_working_sets = [set_log for set_log in working_sets if is_valid_working_set(set_log)]
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
        "valid_working_set_count": len(valid_working_sets),
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
        "best_current_reps": best_current_working_reps(current_sets),
    }


def calculate_fatigue_score(reps, rir, is_failure, notes, context, target_min_reps, target_max_reps, target_rir, planned_sets):
    score = 20
    performance_drop = context["performance_drop_percent"]
    failure_class = classify_failure(reps, is_failure, notes, target_min_reps, target_max_reps, context)

    if reps < target_min_reps:
        score += 20

    if failure_class == "productive_failure":
        score += 8
    elif failure_class == "acceptable_failure":
        score += 12
    elif failure_class == "bad_failure":
        score += 20
    elif failure_class == "danger_failure":
        score += 40

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
    failure_class = classify_failure(reps, is_failure, notes, target_min_reps, target_max_reps, context)

    if reps >= target_max_reps:
        score += 15
    elif reps >= target_min_reps:
        score += 6
    else:
        score -= 24

    if failure_class == "productive_failure":
        score -= 8
    elif failure_class == "acceptable_failure":
        score -= 12
    elif failure_class == "bad_failure":
        score -= 22
    elif failure_class == "danger_failure":
        score -= 40

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


def confidence_score_from_label(confidence):
    return {
        "alta": 0.87,
        "média": 0.68,
        "baixa": 0.48,
    }.get(confidence, 0.5)


def classify_exercise_priority(exercise_context, session_context=None):
    explicit_priority = normalize_text(exercise_context.get("exercise_priority"))

    if explicit_priority in {"primary", "secondary", "accessory", "finisher"}:
        return explicit_priority.upper()

    movement_pattern = normalize_text(exercise_context.get("movement_pattern"))
    equipment = normalize_text(exercise_context.get("equipment"))
    exercise_name = normalize_text(exercise_context.get("exercise_name"))
    is_compound = bool(exercise_context.get("is_compound"))
    order = int_or_default(
        (session_context or {}).get("exercise_order_in_workout") or exercise_context.get("exercise_order_in_workout"),
        0,
    )

    if any(keyword in exercise_name for keyword in FINISHER_KEYWORDS) and not is_compound:
        return "FINISHER" if order >= 5 else "ACCESSORY"

    if is_compound and movement_pattern in PRIMARY_PATTERNS:
        return "PRIMARY" if order <= 2 or order == 0 else "SECONDARY"

    if movement_pattern in ACCESSORY_PATTERNS or any(keyword in equipment for keyword in ["cable", "polia", "machine", "máquina", "maquina"]):
        return "ACCESSORY"

    return "SECONDARY"


def classify_exercise_type(exercise_context):
    if exercise_context.get("exercise_type"):
        return str(exercise_context.get("exercise_type")).upper()

    if bool(exercise_context.get("is_compound")):
        return "COMPOUND"

    if is_low_risk_exercise(exercise_context):
        return "ISOLATION"

    return "MACHINE" if is_machine_or_stack_exercise(exercise_context) else "GENERAL"


def maximum_allowed_sets(exercise_priority, user_context, exercise_context):
    level = normalize_text(user_context.get("level"))
    goal = normalize_text(user_context.get("goal"))
    exercise_name = normalize_text(exercise_context.get("exercise_name"))
    is_specialization = "special" in goal or notes_include(user_context.get("goal", ""), ["prioridade", "especialização", "especializacao"])

    if exercise_priority == "PRIMARY":
        return 5 if level == "advanced" else 4

    if exercise_priority == "SECONDARY":
        return 5 if level == "advanced" else 4

    if exercise_priority == "ACCESSORY":
        if level in {"intermediate", "advanced"} and (
            is_specialization or any(keyword in exercise_name for keyword in SAFE_ACCESSORY_KEYWORDS)
        ):
            return 6
        return 5

    if exercise_priority == "FINISHER":
        return 5 if level in {"intermediate", "advanced"} else 4

    return 4


def calculate_global_fatigue_score(notes, context, session_context, exercise_context):
    total_sets = int_or_default(session_context.get("total_sets_completed_in_session"), 0)
    score = min(total_sets * 3, 45)
    score += int(context["history_analysis"]["failure_rate"] * 15)

    if bool(exercise_context.get("is_compound")):
        score += 8

    if has_strong_fatigue(notes) or notes_include(session_context.get("session_notes", ""), STRONG_FATIGUE_KEYWORDS):
        score += 25

    if has_pain_or_risk(notes) or has_bad_technique(notes):
        score += 35

    return clamp(score, 0, 100)


def calculate_stimulus_score(reps, rir, is_failure, notes, context, target_min_reps, target_max_reps, exercise_priority):
    if has_pain_or_risk(notes) or has_bad_technique(notes):
        return 0

    score = 35

    if reps >= target_max_reps:
        score += 25
    elif reps >= target_min_reps:
        score += 18
    elif reps >= max(1, target_min_reps * 0.7):
        score += 10
    else:
        score += 4

    if is_failure:
        score += 8 if reps >= target_min_reps else 4

    if rir is not None and 0 <= rir <= 3:
        score += 12
    elif rir is not None and rir >= 4:
        score += 4

    if exercise_priority in {"PRIMARY", "SECONDARY"}:
        score += 5

    if context["performance_drop_percent"] >= 25:
        score -= 15

    return clamp(score, 0, 100)


def calculate_fatigue_cost(fatigue_score, global_fatigue_score, is_failure, context):
    cost = round(fatigue_score * 0.65 + global_fatigue_score * 0.35)

    if is_failure:
        cost += 8

    if context["performance_drop_percent"] >= 25:
        cost += 10

    return clamp(cost, 0, 100)


def next_set_still_worthwhile(stimulus_score, fatigue_cost, exercise_priority, valid_working_sets, minimum_valid_sets):
    if valid_working_sets < minimum_valid_sets:
        return True

    threshold = 8 if exercise_priority in {"PRIMARY", "SECONDARY"} else 16

    return (stimulus_score - fatigue_cost) >= threshold


def derive_exercise_state(decision, valid_working_sets, minimum_valid_sets, maximum_sets, stimulus_score, fatigue_cost):
    if decision.get("action") == "flag_pain_or_risk":
        return "SAFETY_STOP"

    if decision.get("exercise_status") == "complete" or decision.get("stop_exercise"):
        return "END_EXERCISE"

    if valid_working_sets >= maximum_sets:
        return "END_EXERCISE"

    if decision.get("do_backoff_set") or decision.get("next_set_type") == "DROP":
        return "BACKOFF"

    if decision.get("action") in {"decrease_weight", "increase_weight", "maintain_or_small_backoff", "small_backoff"}:
        return "ADJUST_LOAD"

    if valid_working_sets >= minimum_valid_sets and decision.get("add_set"):
        return "ADD_VOLUME" if (stimulus_score - fatigue_cost) >= 0 else "FINAL_SET"

    if valid_working_sets == minimum_valid_sets - 1:
        return "FINAL_SET"

    return "CONTINUE"


def public_context(context, previous_sets, planned_sets):
    return {
        "completed_set_count": context["completed_set_count"],
        "working_set_count": context["working_set_count"],
        "valid_working_sets": context.get("valid_working_set_count", context["working_set_count"]),
        "planned_sets": planned_sets,
        "minimum_valid_sets": context.get("minimum_valid_sets", planned_sets),
        "maximum_allowed_sets": context.get("maximum_allowed_sets", planned_sets + MAX_EXTRA_PRODUCTIVE_SETS),
        "exercise_priority": context.get("exercise_priority"),
        "exercise_type": context.get("exercise_type"),
        "failure_class": context.get("failure_class", "none"),
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

    confidence = confidence_from_scores(readiness_score, fatigue_score, recovery_score)
    valid_working_sets = context.get("valid_working_set_count", context["working_set_count"])
    minimum_valid_sets = context.get("minimum_valid_sets", planned_sets)
    maximum_sets = context.get("maximum_allowed_sets", planned_sets + MAX_EXTRA_PRODUCTIVE_SETS)
    stimulus_score = decision.get("stimulus_score", context.get("stimulus_score", readiness_score))
    global_fatigue_score = decision.get("global_fatigue_score", context.get("global_fatigue_score", 0))
    fatigue_cost = decision.get("fatigue_cost", context.get("fatigue_cost", fatigue_score))
    exercise_state = decision.get("exercise_state") or derive_exercise_state(
        {
            **decision,
            "add_set": add_set,
            "stop_exercise": stop_exercise,
            "do_backoff_set": do_backoff_set,
            "action": action,
        },
        valid_working_sets,
        minimum_valid_sets,
        maximum_sets,
        stimulus_score,
        fatigue_cost,
    )

    return {
        **decision,
        "exercise_state": exercise_state if exercise_state in EXERCISE_STATES else "CONTINUE",
        "action": action,
        "target_reps": decision.get("target_reps", target_max_reps),
        "target_reps_label": target_reps_label(target_min_reps, target_max_reps),
        "target_rir": decision.get("target_rir", target_rir),
        "add_set": add_set,
        "stop_exercise": stop_exercise,
        "do_backoff_set": do_backoff_set,
        "backoff_weight": decision.get("backoff_weight"),
        "confidence": confidence,
        "confidence_score": confidence_score_from_label(confidence),
        "readiness_score": readiness_score,
        "fatigue_score": fatigue_score,
        "local_fatigue_score": fatigue_score,
        "global_fatigue_score": global_fatigue_score,
        "stimulus_score": stimulus_score,
        "fatigue_cost": fatigue_cost,
        "recovery_score": recovery_score,
        "valid_working_sets": valid_working_sets,
        "minimum_valid_sets": minimum_valid_sets,
        "maximum_allowed_sets": maximum_sets,
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


def reps_zone(reps, target_min_reps, target_max_reps):
    if reps <= max(1, round(target_min_reps * 0.4)):
        return "extremely_low"

    if reps <= max(1, round(target_min_reps * 0.6)):
        return "very_low"

    if reps <= max(1, round(target_min_reps * 0.8)):
        return "low"

    if reps < target_min_reps:
        return "slightly_low"

    if reps <= target_max_reps:
        return "in_range"

    if reps <= target_max_reps + 2:
        return "above_range"

    if reps <= target_max_reps + 4:
        return "well_above_range"

    return "too_light"


def load_adjustment_ratio(reps, rir, is_failure, target_min_reps, target_max_reps):
    zone = reps_zone(reps, target_min_reps, target_max_reps)

    if zone == "extremely_low":
        return -0.30

    if zone == "very_low":
        return -0.22

    if zone == "low":
        return -0.12

    if zone == "slightly_low":
        return -0.08 if is_failure or rir in (None, 0) else 0

    if zone == "in_range":
        if reps >= target_max_reps and is_failure:
            return -0.06

        if reps >= target_max_reps and rir is not None and rir >= 2:
            return 0.04

        if reps == target_min_reps and (is_failure or rir == 0):
            return -0.05

        if reps >= target_max_reps - 1 and rir is not None and rir >= 3:
            return 0.03

        return 0

    if zone == "above_range":
        return 0.06

    if zone == "well_above_range":
        return 0.09

    return 0.12


def adjusted_working_weight(weight, reps, rir, is_failure, target_min_reps, target_max_reps, exercise_context):
    ratio = load_adjustment_ratio(reps, rir, is_failure, target_min_reps, target_max_reps)
    direction = "nearest"

    if ratio < 0:
        direction = "down"
    elif ratio > 0:
        direction = "up"

    return snap_to_available_weight(weight * (1 + ratio), exercise_context, direction)


def adjust_recommended_weight(weight, exercise_context, direction="nearest"):
    return snap_to_available_weight(weight, exercise_context, direction)


def increased_working_weight(weight, step, exercise_context):
    if get_exercise_weight_scale(exercise_context)["configured"]:
        return next_available_weight(weight, exercise_context)

    return round_recommended_weight(weight + step)


def is_machine_or_stack_exercise(exercise_context):
    equipment = normalize_text(exercise_context.get("equipment"))

    return any(keyword in equipment for keyword in ["machine", "máquina", "maquina", "cable", "polia"])


def next_weight_available(weight, exercise_context):
    scale = get_exercise_weight_scale(exercise_context)

    if scale["configured"]:
        return next_available_weight(weight, exercise_context) > weight

    return False


def weight_scale_missing(exercise_context):
    return not get_exercise_weight_scale(exercise_context)["configured"]


def next_weight_jump_ratio(weight, exercise_context):
    next_weight = next_available_weight(weight, exercise_context)

    if not weight or next_weight <= weight:
        return 0

    return (next_weight - weight) / weight


def is_low_risk_exercise(exercise_context):
    movement_pattern = normalize_text(exercise_context.get("movement_pattern"))
    equipment = normalize_text(exercise_context.get("equipment"))

    if movement_pattern in LOW_RISK_MOVEMENT_PATTERNS:
        return True

    return any(keyword in equipment for keyword in LOW_RISK_EQUIPMENT_KEYWORDS)


def current_working_sets_at_target(context, minimum_rir, target_max_reps):
    working_sets = [set_log for set_log in context["all_current_sets"] if is_working_set(set_log)]

    if not working_sets:
        return False

    return all(
        set_is_target_with_rir(set_log, minimum_rir, target_max_reps)
        for set_log in working_sets
    )


def can_increase_working_weight(weight, reps, rir, is_failure, notes, context, history_sets, exercise_context, target_max_reps):
    if reps < target_max_reps or rir is None or rir < 3:
        return False

    if is_failure or has_negative_feedback(notes):
        return False

    if context["performance_drop_percent"] >= 15:
        return False

    if context["history_signal"] == "regressing" or context["history_analysis"]["trend"] == "regression":
        return False

    if not next_weight_available(weight, exercise_context):
        return False

    if next_weight_jump_ratio(weight, exercise_context) > LARGE_MACHINE_JUMP_RATIO and rir < 4:
        return False

    next_weight = next_available_weight(weight, exercise_context)
    recent_failures_at_next_weight = count_recent_failures_at_weight(history_sets, next_weight)

    if recent_failures_at_next_weight and (rir < 4 or context["history_analysis"]["trend"] != "positive"):
        return False

    return True


def should_request_weight_scale_before_increase(reps, rir, is_failure, notes, context, exercise_context, target_max_reps):
    return (
        reps >= target_max_reps
        and rir is not None
        and rir >= 3
        and not is_failure
        and not has_negative_feedback(notes)
        and context["performance_drop_percent"] < 15
        and context["history_signal"] != "regressing"
        and context["history_analysis"]["trend"] != "regression"
        and weight_scale_missing(exercise_context)
    )


def should_decrease_working_weight(reps, rir, is_failure, context, target_min_reps, failure_class):
    return (
        reps < target_min_reps
        or failure_is_bad(failure_class)
        or (rir is not None and rir <= 0)
        or context["performance_drop_percent"] >= 25
    )


def should_stop_after_bad_set(context, planned_sets, reps, rir, is_failure, target_min_reps, failure_class):
    minimum_valid_sets = context.get("minimum_valid_sets", planned_sets)

    if context.get("valid_working_set_count", context["working_set_count"]) < minimum_valid_sets:
        return False

    rir_zero_count = len([
        set_log
        for set_log in context["all_current_sets"]
        if is_working_set(set_log) and number_or_none(set_log.get("rir")) == 0
    ])

    if context["consecutive_working_misses"] >= 2:
        return True

    if rir_zero_count >= 2:
        return True

    if context["performance_drop_percent"] >= 25:
        return True

    if failure_is_bad(failure_class) and context["working_set_count"] >= max(1, planned_sets - 1):
        return True

    return reps < target_min_reps and context["working_set_count"] >= planned_sets


def can_add_extra_set(context, planned_sets, exercise_context, target_max_reps):
    working_sets = [set_log for set_log in context["all_current_sets"] if is_working_set(set_log)]
    working_count = len(working_sets)
    valid_working_sets = context.get("valid_working_set_count", working_count)
    history = context["history_analysis"]
    maximum_sets = context.get("maximum_allowed_sets", planned_sets + MAX_EXTRA_PRODUCTIVE_SETS)
    exercise_priority = context.get("exercise_priority", "SECONDARY")

    if valid_working_sets < planned_sets:
        return True

    if working_count >= maximum_sets:
        return False

    if context.get("global_fatigue_score", 0) > 80 or context.get("fatigue_cost", 0) > context.get("stimulus_score", 0):
        return False

    if history["trend"] == "regression" or history["failure_rate"] > 0.2:
        return False

    if context["current_summary"]["missed_set_count"] or context["failure_class"] in {"bad_failure", "danger_failure"}:
        return False

    if working_count == planned_sets and planned_sets >= 3:
        first_sets = working_sets[:2]
        last_planned_set = working_sets[planned_sets - 1]

        return (
            exercise_priority in {"PRIMARY", "SECONDARY", "ACCESSORY"}
            and all(set_is_target_with_rir(set_log, 2, target_max_reps) for set_log in first_sets)
            and set_is_target_with_rir(last_planned_set, 2, target_max_reps)
        )

    if working_count >= 4:
        rir_values = [
            number_or_none(set_log.get("rir"))
            for set_log in working_sets
            if number_or_none(set_log.get("rir")) is not None
        ]

        return (
            exercise_priority in {"ACCESSORY", "FINISHER"}
            and is_low_risk_exercise(exercise_context)
            and len(rir_values) == working_count
            and average(rir_values) >= 3
            and current_working_sets_at_target(context, 2, target_max_reps)
        )

    return False


def next_warmup_weight(current_weight, first_working_weight, exercise_context):
    if not first_working_weight:
        return current_weight

    target = first_working_weight * 0.75

    if current_weight >= target:
        return current_weight

    return snap_to_available_weight(
        min(target, current_weight + WEIGHT_STEP * 2),
        exercise_context,
    )


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
    valid_working_sets = context.get("valid_working_set_count", working_count)
    current_summary = context["current_summary"]
    planned_sets = planned_sets or 3
    minimum_valid_sets = context.get("minimum_valid_sets", planned_sets)
    max_productive_sets = context.get("maximum_allowed_sets", planned_sets + MAX_EXTRA_PRODUCTIVE_SETS)
    latest_working_set = context["last_two_working_sets"][-1] if context["last_two_working_sets"] else None
    latest_set_recovered = latest_working_set is not None and set_has_reserve(latest_working_set)

    if working_count == 0:
        return False

    if valid_working_sets < minimum_valid_sets:
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


def safety_guardrails(notes, reps, is_failure, target_min_reps, target_max_reps, fatigue_score, context):
    failure_class = classify_failure(reps, is_failure, notes, target_min_reps, target_max_reps, context)

    return {
        "has_pain_or_risk": has_pain_or_risk(notes),
        "has_bad_technique": has_bad_technique(notes),
        "has_stop_request": has_stop_request(notes),
        "has_no_increase_request": has_no_increase_request(notes),
        "failure_class": failure_class,
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
            or failure_class == "danger_failure"
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
    minimum_valid_sets = int_or_default(exercise_context.get("minimum_valid_sets"), min(planned_sets, 3))
    exercise_priority = classify_exercise_priority(exercise_context, session_context)
    exercise_type = classify_exercise_type(exercise_context)
    max_sets = int_or_default(
        exercise_context.get("maximum_allowed_sets"),
        maximum_allowed_sets(exercise_priority, user_context, exercise_context),
    )

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
    failure_class = classify_failure(reps, is_failure, notes, target_min_reps, target_max_reps, context)
    context["failure_class"] = failure_class
    context["minimum_valid_sets"] = minimum_valid_sets
    context["maximum_allowed_sets"] = max_sets
    context["exercise_priority"] = exercise_priority
    context["exercise_type"] = exercise_type
    fatigue_score = calculate_fatigue_score(
        scoring_reps,
        rir,
        is_failure,
        notes,
        context,
        target_min_reps,
        target_max_reps,
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
    global_fatigue_score = calculate_global_fatigue_score(notes, context, session_context, exercise_context)
    stimulus_score = calculate_stimulus_score(
        scoring_reps,
        rir,
        is_failure,
        notes,
        context,
        target_min_reps,
        target_max_reps,
        exercise_priority,
    )
    fatigue_cost = calculate_fatigue_cost(fatigue_score, global_fatigue_score, is_failure, context)
    context["global_fatigue_score"] = global_fatigue_score
    context["stimulus_score"] = stimulus_score
    context["fatigue_cost"] = fatigue_cost
    guardrails = safety_guardrails(notes, scoring_reps, is_failure, target_min_reps, target_max_reps, fatigue_score, context)

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
            recommended_weight = next_warmup_weight(weight, first_working_weight, exercise_context)

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
                "recommended_weight": snap_to_available_weight(first_working_weight, exercise_context),
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

    if should_stop_after_bad_set(context, planned_sets, reps, rir, is_failure, target_min_reps, failure_class):
        return with_decision_metadata(
            make_stop_decision(
                "stop_exercise",
                "A falha, queda de reps ou acumulação de RIR 0 indica que continuar neste exercício já não compensa.",
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

    if failure_class in {"productive_failure", "acceptable_failure"} and context["working_set_count"] < planned_sets:
        recommended_weight = adjusted_working_weight(
            weight,
            reps,
            rir,
            is_failure,
            target_min_reps,
            target_max_reps,
            exercise_context,
        )
        target_reps_after_failure = target_reps
        action = "maintain_or_small_backoff" if recommended_weight < weight else "maintain_weight"
        reason = (
            "A falha ocorreu no topo da faixa de reps. A carga está desafiante, mas ainda existe volume útil sem subir peso."
            if failure_class == "productive_failure"
            else "A falha aconteceu dentro da faixa alvo. Continua com cautela, sem aumentar carga."
        )

        return with_decision_metadata(
            {
                "recommended_weight": recommended_weight,
                "target_reps": target_reps_after_failure,
                "recommended_rest_seconds": 150,
                "next_set_type": "WORKING",
                "exercise_status": "continue",
                "action": action,
                "add_set": True,
                "stop_exercise": False,
                "do_backoff_set": recommended_weight < weight,
                "backoff_weight": recommended_weight if recommended_weight < weight else None,
                "reason": reason,
                "guidance_title": "Pequeno ajuste de carga" if recommended_weight < weight else "Mantém a carga",
                "guidance_message": "Falhar não significa parar. Não subas peso; ajusta a carga para garantir uma próxima série útil com técnica limpa.",
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
            [
                f"Falha classificada como {failure_class}",
                "Falha não ocorreu abaixo do mínimo de reps",
                "Progressão de carga bloqueada, mas exercício pode continuar",
            ],
            guardrails,
        )

    if should_decrease_working_weight(reps, rir, is_failure, context, target_min_reps, failure_class):
        recommended_weight = adjusted_working_weight(
            weight,
            reps,
            rir,
            is_failure,
            target_min_reps,
            target_max_reps,
            exercise_context,
        )

        if (
            bool(exercise_context.get("is_compound"))
            and reps >= max(1, target_min_reps - 1)
            and not has_strong_fatigue(notes)
            and context["working_set_count"] < planned_sets
        ):
            recommended_backoff_weight = recommended_weight

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

        return with_decision_metadata(
            {
                "recommended_weight": recommended_weight,
                "target_reps": target_reps,
                "recommended_rest_seconds": 180 if is_failure or fatigue_score >= 75 else 150,
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

    if (
        reps >= target_max_reps
        and rir is not None
        and 1 <= rir <= 2
        and not is_failure
        and context["working_set_count"] < planned_sets
    ):
        return with_decision_metadata(
            {
                "recommended_weight": weight,
                "target_reps": target_reps,
                "recommended_rest_seconds": 120,
                "next_set_type": "WORKING",
                "exercise_status": "continue",
                "action": "maintain_weight",
                "add_set": True,
                "stop_exercise": False,
                "do_backoff_set": False,
                "backoff_weight": None,
                "reason": "Chegaste às reps alvo, mas o RIR ficou na zona de trabalho normal. A carga deve ser consolidada.",
                "guidance_title": "Mantém a carga",
                "guidance_message": "Repete a carga e procura manter 12 reps com técnica limpa.",
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
            ["12 reps atingidas", "RIR 1-2 pede consolidação, não subida"],
            guardrails,
        )

    if should_request_weight_scale_before_increase(
        reps,
        rir,
        is_failure,
        notes,
        context,
        exercise_context,
        target_max_reps,
    ):
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
                "reason": "A performance sugere que pode existir margem para subir, mas a escala de pesos deste exercício ainda não está registada.",
                "guidance_title": "Regista a escala da máquina",
                "guidance_message": "Abre o menu Escala deste exercício e adiciona as placas e bolachas disponíveis. Depois a IA consegue decidir se há subida real possível.",
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
            ["12 reps com RIR >= 3", "Subida bloqueada até existir escala de pesos registada"],
            guardrails,
        )

    if can_increase_working_weight(
        weight,
        reps,
        rir,
        is_failure,
        notes,
        context,
        history_sets,
        exercise_context,
        target_max_reps,
    ):
        step = calculate_increase_step(weight, exercise_context)
        next_working_set_allowed = context["working_set_count"] < planned_sets

        if next_working_set_allowed:
            return with_decision_metadata(
                {
                    "recommended_weight": increased_working_weight(weight, step, exercise_context),
                    "target_reps": target_reps,
                    "recommended_rest_seconds": 120,
                    "next_set_type": "WORKING",
                    "exercise_status": "continue",
                    "action": "increase_weight",
                    "add_set": False,
                    "stop_exercise": False,
                    "do_backoff_set": False,
                    "backoff_weight": None,
                    "reason": "Atingiste 12 reps com RIR alto, sem falha, sem queda relevante e com próximo peso disponível.",
                    "guidance_title": "Sobe a carga",
                    "guidance_message": "Usa o próximo peso disponível desta máquina e confirma se continuas dentro das 12 reps com controlo.",
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
                ["12 reps atingidas", "RIR >= 3", "Próximo peso disponível respeitado", "Histórico não bloqueia subida"],
                guardrails,
            )

    if context["working_set_count"] >= planned_sets and can_add_extra_set(
        context,
        planned_sets,
        exercise_context,
        target_max_reps,
    ):
        return with_decision_metadata(
            {
                "recommended_weight": weight,
                "target_reps": target_reps,
                "recommended_rest_seconds": 120,
                "next_set_type": "WORKING",
                "exercise_status": "continue",
                "action": "add_set",
                "add_set": True,
                "stop_exercise": False,
                "do_backoff_set": False,
                "backoff_weight": None,
                "reason": "O volume planeado foi cumprido, mas as séries mostram margem real e o histórico não aponta excesso de fadiga.",
                "guidance_title": "Podes fazer mais uma série",
                "guidance_message": "Mantém a mesma carga. Esta série extra serve para volume de qualidade, não para testar carga.",
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
            ["Séries planeadas sólidas", "RIR alto suficiente", "Histórico permite uma série extra"],
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
