from .training_coach_engine import calculate_training_coach_decision


def calculate_next_set(weight, reps, rir=None, is_failure=False):
    return calculate_training_coach_decision(
        weight=weight,
        reps=reps,
        rir=rir,
        is_failure=is_failure,
        set_type="WORKING",
    )
