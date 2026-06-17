from .progression_engine import calculate_next_set


NEGATIVE_FEEDBACK_KEYWORDS = [
    "cansado",
    "cansaço",
    "sem energia",
    "dormi mal",
    "dor",
    "dores",
    "desmotivado",
    "quero desistir",
    "não quero subir",
    "muito pesado",
]


def calculate_hybrid_next_set(weight, reps, rir=None, is_failure=False, notes=""):
    rule_recommendation = calculate_next_set(
        weight=weight,
        reps=reps,
        rir=rir,
        is_failure=is_failure,
    )

    normalized_notes = notes.lower().strip()

    has_negative_feedback = any(
        keyword in normalized_notes
        for keyword in NEGATIVE_FEEDBACK_KEYWORDS
    )

    if has_negative_feedback:
        return {
            "recommended_weight": weight,
            "target_reps": rule_recommendation["target_reps"],
            "action": "maintain",
            "reason": (
                "Apesar da performance permitir progressão, o feedback indica fadiga, desconforto ou baixa disponibilidade. "
                "Mantemos a carga para proteger performance e aderência ao treino."
            ),
            "source": "hybrid_ai_simulation",
        }

    return {
        **rule_recommendation,
        "action": "rule_based",
        "source": "rule_engine",
    }