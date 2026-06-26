from exercises.services.weight_scale import (
    next_available_weight,
    number_or_none,
    snap_to_available_weight,
)
from progression.models import SetLog
from accounts.models import UserProfile
from training.models import ExerciseCalibration
from training.services.user_exercise_weight_scale import get_user_exercise_weight_scale


TARGET_REPS = 12
TARGET_RIR = 2
CALIBRATION_SET_TARGET = 3
CALIBRATION_COLOR_REPS = {
    "red": 7,
    "orange": 11,
    "yellow": 14,
    "green": 16,
}


def has_reliable_working_history(user, exercise):
    return SetLog.objects.filter(
        user=user,
        exercise=exercise,
        set_type="WORKING",
        reps_completed__gte=TARGET_REPS,
        reached_failure=False,
        rir__isnull=False,
    ).exists()


def normalize_calibration_set(set_data):
    weight = number_or_none(set_data.get("weight_used"))
    result_color = normalize_calibration_color(set_data.get("result_color"))
    reps = number_or_none(set_data.get("reps_completed"))
    rir = number_or_none(set_data.get("rir"))

    if result_color and reps is None:
        reps = CALIBRATION_COLOR_REPS[result_color]

    if weight is None or reps is None:
        return None

    result_color = result_color or calibration_color_from_reps(int(reps))

    return {
        "weight_used": weight,
        "reps_completed": int(reps),
        "rir": int(rir) if rir is not None else None,
        "reached_failure": bool(set_data.get("reached_failure", True)),
        "result_color": result_color,
        "notes": str(set_data.get("notes", ""))[:240],
    }


def normalize_calibration_color(value):
    color = str(value or "").lower()

    return color if color in CALIBRATION_COLOR_REPS else None


def calibration_color_from_reps(reps):
    if reps <= 8:
        return "red"

    if reps <= 12:
        return "orange"

    if reps <= 14:
        return "yellow"

    return "green"


def estimate_12rm_from_failure_set(weight, reps):
    if not weight or not reps:
        return None

    estimated_1rm = float(weight) * (1 + (int(reps) / 30))

    return estimated_1rm / (1 + (TARGET_REPS / 30))


def estimate_initial_weight(user, exercise, scale_context):
    try:
        profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        profile = None

    body_weight = float(profile.weight_kg) if profile else 70
    level = profile.level if profile else "BEGINNER"
    gender = profile.gender if profile else ""
    pattern = str(getattr(exercise, "movement_pattern", "") or "")
    equipment = str(getattr(exercise, "equipment", "") or "").lower()
    is_compound = bool(getattr(exercise, "is_compound", False))

    pattern_multipliers = {
        "SQUAT": 0.85,
        "HINGE": 0.65,
        "HIP_THRUST": 0.75,
        "HORIZONTAL_PUSH": 0.38,
        "VERTICAL_PUSH": 0.28,
        "HORIZONTAL_PULL": 0.42,
        "VERTICAL_PULL": 0.42,
        "LUNGE": 0.35,
        "ISOLATION": 0.18,
        "CORE": 0.16,
        "CARDIO": 0.1,
    }
    level_multipliers = {
        "BEGINNER": 0.85,
        "INTERMEDIATE": 1.0,
        "ADVANCED": 1.15,
    }

    multiplier = pattern_multipliers.get(pattern, 0.25)

    if "leg press" in getattr(exercise, "name", "").lower():
        multiplier = 1.0
    elif "machine" in equipment and is_compound:
        multiplier *= 1.08

    if gender == "FEMALE":
        multiplier *= 0.75

    estimated_weight = body_weight * multiplier * level_multipliers.get(level, 0.85)

    return snap_to_available_weight(estimated_weight, scale_context)


def estimate_working_weight(calibration_sets, scale_context):
    useful_estimates = [
        estimate_12rm_from_failure_set(
            set_data.get("weight_used"),
            set_data.get("reps_completed"),
        )
        for set_data in calibration_sets
        if set_data.get("weight_used") and set_data.get("reps_completed")
    ]
    useful_estimates = [estimate for estimate in useful_estimates if estimate is not None]

    if not useful_estimates:
        return None

    recent_estimates = useful_estimates[-2:] if len(useful_estimates) >= 2 else useful_estimates
    estimated_weight = sum(recent_estimates) / len(recent_estimates)

    return snap_to_available_weight(estimated_weight, scale_context)


def confidence_from_calibration(calibration_sets, scale_configured):
    if not scale_configured:
        return "baixa"

    if len(calibration_sets) >= 3:
        return "alta"

    if len(calibration_sets) >= 2:
        return "média"

    return "baixa"


def build_next_calibration_step(calibration_sets, scale, user=None, exercise=None):
    completed_sets = len(calibration_sets)
    remaining_sets = max(CALIBRATION_SET_TARGET - completed_sets, 0)

    if not scale["configured"]:
        return {
            "recommended_weight": None,
            "recommended_reps": "falha técnica",
            "target_rir": 0,
            "set_number": completed_sets + 1,
            "remaining_sets": CALIBRATION_SET_TARGET,
            "action": "fill_scale",
            "message": "Preenche a escala da máquina antes de escolher a próxima carga experimental.",
        }

    if not calibration_sets:
        return {
            "recommended_weight": estimate_initial_weight(user, exercise, scale) if user and exercise else scale["available_weights"][0],
            "recommended_reps": "falha técnica",
            "target_rir": 0,
            "set_number": 1,
            "remaining_sets": CALIBRATION_SET_TARGET,
            "action": "initial_failure_test",
            "message": "Faz o máximo possível com técnica limpa. Queremos descobrir a carga que falha perto da rep 12.",
        }

    last_set = calibration_sets[-1]
    last_weight = last_set["weight_used"]
    last_reps = last_set.get("reps_completed", 0)
    last_estimated_12rm = estimate_12rm_from_failure_set(last_weight, last_reps)

    if remaining_sets <= 0:
        final_weight = estimate_working_weight(calibration_sets, scale)

        return {
            "recommended_weight": final_weight,
            "recommended_reps": TARGET_REPS,
            "target_rir": TARGET_RIR,
            "set_number": CALIBRATION_SET_TARGET,
            "remaining_sets": 0,
            "action": "calibration_complete",
            "message": "Calibração completa. Este é o peso padrão estimado para falhar perto da rep 12.",
        }

    next_weight = snap_to_available_weight(last_estimated_12rm, scale) if last_estimated_12rm else last_weight
    color = calibration_color_from_reps(last_reps)
    action_by_color = {
        "red": "reduce_after_early_failure",
        "orange": "confirm_near_target",
        "yellow": "slight_increase",
        "green": "increase_after_high_reps",
    }
    message_by_color = {
        "red": "Falhou cedo demais. A próxima série baixa para aproximar a falha da rep 12.",
        "orange": "Já estamos perto da zona alvo. A próxima série confirma o peso padrão.",
        "yellow": "Ficou ligeiramente leve. A próxima série sobe de forma controlada.",
        "green": "Ficou leve demais. A próxima série sobe para procurar a falha perto da rep 12.",
    }

    return {
        "recommended_weight": next_weight,
        "recommended_reps": "falha técnica",
        "target_rir": 0,
        "set_number": completed_sets + 1,
        "remaining_sets": remaining_sets,
        "previous_result_color": color,
        "action": action_by_color[color],
        "message": message_by_color[color],
    }


def serialize_calibration(calibration, user, exercise):
    scale = get_user_exercise_weight_scale(user, exercise)
    reliable_history = has_reliable_working_history(user, exercise)
    effective_status = calibration.status if calibration else "PENDING"
    estimated_weight = calibration.estimated_working_weight if calibration else None
    calibration_sets = calibration.calibration_sets if calibration else []

    has_full_calibration = len(calibration_sets) >= CALIBRATION_SET_TARGET

    if reliable_history:
        effective_status = "CALIBRATED"
    elif estimated_weight and scale["configured"] and has_full_calibration:
        effective_status = "CALIBRATED"
    elif estimated_weight:
        effective_status = "NEEDS_REVIEW"

    needs_calibration = effective_status != "CALIBRATED"
    reason = ""

    if needs_calibration and not scale["configured"]:
        reason = "scale_required"
    elif needs_calibration and not estimated_weight:
        reason = "baseline_required"
    elif needs_calibration and len(calibration_sets) < CALIBRATION_SET_TARGET:
        reason = "more_calibration_sets_required"

    return {
        "id": calibration.id if calibration else None,
        "status": effective_status,
        "needs_calibration": needs_calibration,
        "reason": reason,
        "scale_configured": scale["configured"],
        "estimated_working_weight": estimated_weight,
        "target_reps": calibration.target_reps if calibration else TARGET_REPS,
        "target_rir": calibration.target_rir if calibration else TARGET_RIR,
        "protocol": {
            "target_sets": CALIBRATION_SET_TARGET,
            "goal": "Encontrar a carga que leva à falha técnica perto da rep 12.",
            "color_scale": {
                "red": "falha antes das 8 reps",
                "orange": "entre 9 e 12 reps",
                "yellow": "entre 13 e 14 reps",
                "green": "acima de 15 reps",
            },
        },
        "confidence": calibration.confidence if calibration else "baixa",
        "calibration_sets": calibration_sets,
        "set_count": len(calibration_sets),
        "scale": scale,
        "next_step": build_next_calibration_step(calibration_sets, scale, user, exercise),
        "message": (
            "Preenche a escala e faz uma calibração rápida antes de treinar este exercício."
            if needs_calibration else
            "Exercício calibrado. A IA já pode usar uma carga inicial fiável."
        ),
    }


def get_exercise_calibration_state(user, exercise):
    calibration = ExerciseCalibration.objects.filter(user=user, exercise=exercise).first()

    return serialize_calibration(calibration, user, exercise)


def upsert_exercise_calibration(user, exercise, set_data, notes=""):
    calibration, _ = ExerciseCalibration.objects.get_or_create(user=user, exercise=exercise)
    normalized_set = normalize_calibration_set(set_data)

    if normalized_set:
        calibration_sets = [*calibration.calibration_sets, normalized_set]
    else:
        calibration_sets = calibration.calibration_sets

    scale = get_user_exercise_weight_scale(user, exercise)
    estimated_weight = estimate_working_weight(calibration_sets, scale)

    calibration.calibration_sets = calibration_sets
    calibration.estimated_working_weight = estimated_weight
    calibration.confidence = confidence_from_calibration(calibration_sets, scale["configured"])
    calibration.status = (
        "CALIBRATED"
        if estimated_weight and scale["configured"] and len(calibration_sets) >= CALIBRATION_SET_TARGET
        else "NEEDS_REVIEW"
    )
    calibration.scale_snapshot = scale
    calibration.notes = notes or calibration.notes
    calibration.save()

    return serialize_calibration(calibration, user, exercise)


def build_calibrated_recommended_sets(training_exercise, calibration_state):
    estimated_weight = calibration_state.get("estimated_working_weight")

    if not estimated_weight:
        return []

    scale_context = calibration_state.get("scale") or calibration_state.get("scale_snapshot") or {}
    warmup_weight = snap_to_available_weight(estimated_weight * 0.5, scale_context)
    working_weight = snap_to_available_weight(estimated_weight, scale_context)
    recommendations = [
        {
            "set_number": 1,
            "set_type": "WARMUP",
            "recommended_weight": warmup_weight,
            "recommended_reps": 8,
            "confidence": calibration_state.get("confidence", "baixa"),
            "source": "exercise_calibration",
            "reason": "Aquecimento calculado a partir da calibração inicial deste atleta.",
            "decision_basis": ["Peso de trabalho calibrado", "Aquecimento sem RIR"],
        }
    ]

    recommendations.append({
        "set_number": 2,
        "set_type": "WORKING",
        "recommended_weight": working_weight,
        "recommended_reps": training_exercise.target_max_reps,
        "confidence": calibration_state.get("confidence", "baixa"),
        "source": "exercise_calibration",
        "reason": "Primeira carga de trabalho baseada na calibração inicial.",
        "decision_basis": [
            "Peso de trabalho calibrado",
            "Escala da máquina preenchida",
            "As próximas séries serão calculadas com o desempenho de hoje",
        ],
    })

    return recommendations
