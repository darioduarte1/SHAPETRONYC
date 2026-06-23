from .training_coach_engine import calculate_training_coach_decision


def calculate_hybrid_next_set(weight, reps, rir=None, is_failure=False, notes=""):
    return calculate_training_coach_decision(
        weight=weight,
        reps=reps,
        rir=rir,
        is_failure=is_failure,
        notes=notes,
        set_type="WORKING",
    )
