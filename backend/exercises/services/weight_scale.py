# =============================================================================
# weight_scale.py
# -----------------------------------------------------------------------------
# Serviço responsável por trabalhar com escalas de peso das máquinas.
# É usado para validar valores disponíveis e ajustar recomendações ao peso real mais próximo que a máquina permite.
# Evita que a app sugira cargas impossíveis ou arredondamentos fora da escala registada.
# =============================================================================
DEFAULT_WEIGHT_STEP = 2.5


def number_or_none(value):
    if value in ("", None):
        return None

    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def round_weight(weight):
    return round(float(max(weight, 0)), 2)


def round_default_weight(weight):
    return round(float(max(weight, 0)) * 2) / 2


def normalize_weight_options(values):
    if not isinstance(values, list):
        return []

    normalized_values = []

    for value in values:
        number = number_or_none(value)

        if number is None or number < 0:
            continue

        normalized_values.append(round_weight(number))

    return sorted(set(normalized_values))


def normalize_micro_weight_options(values):
    if not isinstance(values, list):
        return []

    normalized_values = []

    for value in values:
        if isinstance(value, dict):
            weight = number_or_none(value.get("weight"))
            count = number_or_none(value.get("count"))

            if weight is None or count is None or weight <= 0 or count <= 0:
                continue

            normalized_values.extend([round_weight(weight)] * int(count))
            continue

        number = number_or_none(value)

        if number is None or number <= 0:
            continue

        normalized_values.append(round_weight(number))

    return sorted(normalized_values)


def build_micro_weight_sums(micro_weights):
    sums = {0}

    for micro_weight in micro_weights:
        sums.update({round_weight(current_sum + micro_weight) for current_sum in sums})

    return sorted(sums)


def get_exercise_weight_scale(exercise_or_context):
    if not exercise_or_context:
        return {
            "main_weight_options": [],
            "micro_weight_options": [],
            "available_weights": [],
            "configured": False,
        }

    if isinstance(exercise_or_context, dict):
        main_options = exercise_or_context.get("main_weight_options", [])
        micro_options = exercise_or_context.get("micro_weight_options", [])
    else:
        main_options = getattr(exercise_or_context, "main_weight_options", [])
        micro_options = getattr(exercise_or_context, "micro_weight_options", [])

    main_weights = normalize_weight_options(main_options)
    micro_weights = normalize_micro_weight_options(micro_options)
    micro_weight_sums = build_micro_weight_sums(micro_weights)
    available_weights = []

    for main_weight in main_weights:
        for micro_weight_sum in micro_weight_sums:
            available_weights.append(round_weight(main_weight + micro_weight_sum))

    available_weights = sorted(set(available_weights))

    return {
        "main_weight_options": main_weights,
        "micro_weight_options": micro_weights,
        "micro_weight_sums": [weight_sum for weight_sum in micro_weight_sums if weight_sum > 0],
        "available_weights": available_weights,
        "configured": bool(available_weights),
    }


def snap_to_available_weight(target_weight, exercise_or_context=None, direction="nearest"):
    target = number_or_none(target_weight)

    if target is None:
        return target_weight

    scale = get_exercise_weight_scale(exercise_or_context)
    available_weights = scale["available_weights"]

    if not available_weights:
        return round_default_weight(target)

    if direction == "up":
        candidates = [weight for weight in available_weights if weight > target]
        return candidates[0] if candidates else available_weights[-1]

    if direction == "down":
        candidates = [weight for weight in available_weights if weight < target]
        return candidates[-1] if candidates else available_weights[0]

    return min(
        available_weights,
        key=lambda weight: (abs(weight - target), weight),
    )


def next_available_weight(current_weight, exercise_or_context=None):
    current = number_or_none(current_weight)

    if current is None:
        return current_weight

    scale = get_exercise_weight_scale(exercise_or_context)

    if not scale["available_weights"]:
        return round_default_weight(current + DEFAULT_WEIGHT_STEP)

    return snap_to_available_weight(current, exercise_or_context, "up")


def previous_available_weight(current_weight, exercise_or_context=None):
    current = number_or_none(current_weight)

    if current is None:
        return current_weight

    scale = get_exercise_weight_scale(exercise_or_context)

    if not scale["available_weights"]:
        return round_default_weight(max(0, current - DEFAULT_WEIGHT_STEP))

    return snap_to_available_weight(current, exercise_or_context, "down")
