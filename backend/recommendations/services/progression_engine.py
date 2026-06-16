def calculate_next_set(weight, reps, rir=None, is_failure=False):
    target_min_reps = 10
    target_max_reps = 12
    weight_step = 2.5

    if is_failure and reps < target_min_reps:
        return {
            "recommended_weight": max(weight - weight_step, 0),
            "target_reps": "10-12",
            "reason": "Falhaste antes do mínimo de reps. Reduzimos a carga."
        }

    if reps >= target_max_reps and rir is not None and rir >= 2:
        return {
            "recommended_weight": weight + weight_step,
            "target_reps": "10-12",
            "reason": "Fizeste o topo do range com margem. Aumentamos a carga."
        }

    if target_min_reps <= reps <= target_max_reps:
        return {
            "recommended_weight": weight,
            "target_reps": "10-12",
            "reason": "Ficaste dentro do range ideal. Mantemos a carga."
        }

    return {
        "recommended_weight": weight,
        "target_reps": "10-12",
        "reason": "Mantemos a carga para estabilizar performance."
    }