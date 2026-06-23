def calculate_next_set(weight, reps, rir=None, is_failure=False):
    target_reps = 12
    weight_step = 2.5

    if reps < target_reps:
        should_reduce_load = is_failure or (rir is not None and rir <= 1)

        if should_reduce_load:
            return {
                "recommended_weight": max(weight - weight_step, 0),
                "target_reps": target_reps,
                "reason": "Não chegaste às 12 reps com margem suficiente. Reduzimos a carga para voltares ao alvo."
            }

        return {
            "recommended_weight": weight,
            "target_reps": target_reps,
            "reason": "Ainda não chegaste às 12 reps. Mantemos a carga para consolidares a série."
        }

    if rir is not None and rir >= 2:
        return {
            "recommended_weight": weight + weight_step,
            "target_reps": target_reps,
            "reason": "Fizeste 12 reps com margem. Aumentamos a carga na próxima série."
        }

    return {
        "recommended_weight": weight,
        "target_reps": target_reps,
        "reason": "Chegaste às 12 reps, mas sem margem clara. Mantemos a carga."
    }
