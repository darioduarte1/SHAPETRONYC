def generate_program_structure(goal, level, days_per_week):
    if goal == "HYPERTROPHY":
        return generate_hypertrophy_program(level, days_per_week)

    if goal == "STRENGTH":
        return generate_strength_program(level, days_per_week)

    if goal == "FAT_LOSS":
        return generate_fat_loss_program(level, days_per_week)

    if goal == "RECOMPOSITION":
        return generate_recomposition_program(level, days_per_week)

    return generate_general_fitness_program(level, days_per_week)


def generate_hypertrophy_program(level, days_per_week):
    if days_per_week == 2:
        workouts = ["Full Body A", "Full Body B"]
    elif days_per_week == 3:
        workouts = ["Full Body A", "Full Body B", "Full Body C"]
    elif days_per_week == 4:
        workouts = ["Upper A", "Lower A", "Upper B", "Lower B"]
    elif days_per_week == 5:
        workouts = ["Push", "Pull", "Legs", "Upper", "Lower"]
    elif days_per_week == 6:
        workouts = ["Push A", "Pull A", "Legs A", "Push B", "Pull B", "Legs B"]
    else:
        workouts = ["Push A", "Pull A", "Legs A", "Push B", "Pull B", "Legs B", "Cardio + Core"]

    return {
        "goal": "HYPERTROPHY",
        "level": level,
        "days_per_week": days_per_week,
        "workouts": workouts,
        "notes": get_level_notes(level),
    }


def generate_strength_program(level, days_per_week):
    if days_per_week <= 3:
        workouts = ["Full Body Strength A", "Full Body Strength B", "Full Body Strength C"][:days_per_week]
    elif days_per_week == 4:
        workouts = ["Upper Strength A", "Lower Strength A", "Upper Strength B", "Lower Strength B"]
    else:
        workouts = ["Push Strength", "Pull Strength", "Legs Strength", "Upper Accessories", "Lower Accessories"][:days_per_week]

    return {
        "goal": "STRENGTH",
        "level": level,
        "days_per_week": days_per_week,
        "workouts": workouts,
        "notes": get_level_notes(level),
    }


def generate_fat_loss_program(level, days_per_week):
    base = ["Full Body A", "Full Body B", "Full Body C", "Cardio + Core", "Upper", "Lower", "Zone 2 Cardio"]
    return {
        "goal": "FAT_LOSS",
        "level": level,
        "days_per_week": days_per_week,
        "workouts": base[:days_per_week],
        "notes": get_level_notes(level),
    }


def generate_recomposition_program(level, days_per_week):
    base = ["Upper", "Lower", "Full Body", "Cardio + Core", "Push", "Pull", "Legs"]
    return {
        "goal": "RECOMPOSITION",
        "level": level,
        "days_per_week": days_per_week,
        "workouts": base[:days_per_week],
        "notes": get_level_notes(level),
    }


def generate_general_fitness_program(level, days_per_week):
    base = ["Full Body A", "Cardio + Core", "Full Body B", "Mobility", "Upper", "Lower", "Conditioning"]
    return {
        "goal": "GENERAL_FITNESS",
        "level": level,
        "days_per_week": days_per_week,
        "workouts": base[:days_per_week],
        "notes": get_level_notes(level),
    }


def get_level_notes(level):
    notes = {
        "BEGINNER": "Menos volume, foco em técnica, consistência e recuperação.",
        "INTERMEDIATE": "Volume moderado/alto, progressão mais exigente e maior frequência muscular.",
        "ADVANCED": "Mais volume, mais especialização e maior exigência de recuperação.",
    }

    return notes.get(level, "Nível não reconhecido.")