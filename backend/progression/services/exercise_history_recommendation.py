def round_recommended_weight(weight):
    return round(float(weight) * 2) / 2


def calculate_recommended_set(previous_set, target_min_reps, target_max_reps):
    if not previous_set:
        return {
            "recommended_weight": "",
            "recommended_reps": "",
            "reason": "No previous set found.",
        }

    previous_weight = float(previous_set.weight_used)
    previous_reps = int(previous_set.reps_completed)
    effective_rir = previous_set.rir if previous_set.rir is not None else 2
    reached_top_of_range = previous_reps >= target_max_reps
    below_range = previous_reps < target_min_reps

    if previous_set.reached_failure or effective_rir <= 1:
        return {
            "recommended_weight": round_recommended_weight(
                max(0, previous_weight - 2.5) if below_range else previous_weight
            ),
            "recommended_reps": target_min_reps if below_range else min(previous_reps, target_max_reps),
            "reason": "Previous set was very close to failure, so start conservatively.",
        }

    if effective_rir <= 3:
        return {
            "recommended_weight": round_recommended_weight(
                previous_weight + 2.5 if reached_top_of_range else previous_weight
            ),
            "recommended_reps": target_min_reps if reached_top_of_range else min(previous_reps + 1, target_max_reps),
            "reason": "Previous set was inside the target effort range.",
        }

    return {
        "recommended_weight": round_recommended_weight(previous_weight + 2.5),
        "recommended_reps": target_max_reps,
        "reason": "Previous set had plenty of reserve, so progress the load.",
    }
