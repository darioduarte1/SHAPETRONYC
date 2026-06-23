def round_recommended_weight(weight):
    return round(float(weight) * 2) / 2


def calculate_recommended_set(previous_set, target_reps=12):
    if not previous_set:
        return {
            "recommended_weight": "",
            "recommended_reps": "",
            "reason": "No previous set found.",
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
                "reason": "Previous set missed 12 reps near failure, so reduce the load.",
            }

        return {
            "recommended_weight": round_recommended_weight(previous_weight),
            "recommended_reps": target_reps,
            "reason": "Previous set missed 12 reps, so keep the load and build reps.",
        }

    if effective_rir >= 2:
        return {
            "recommended_weight": round_recommended_weight(previous_weight + 2.5),
            "recommended_reps": target_reps,
            "reason": "Previous set reached 12 reps with reserve, so progress the load.",
        }

    return {
        "recommended_weight": round_recommended_weight(previous_weight),
        "recommended_reps": target_reps,
        "reason": "Previous set reached 12 reps close to failure, so keep the load.",
    }
