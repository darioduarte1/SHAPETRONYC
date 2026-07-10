# =============================================================================
# progression_engine.py
# -----------------------------------------------------------------------------
# Motor de progressão geral da app.
# É usado para avaliar evolução do atleta e decidir ajustes de carga, volume ou margem.
# Serve como base de regras para recomendações de treino mais amplas.
# =============================================================================
from .training_coach_engine import calculate_training_coach_decision


def calculate_next_set(weight, reps, rir=None, is_failure=False):
    return calculate_training_coach_decision(
        weight=weight,
        reps=reps,
        rir=rir,
        is_failure=is_failure,
        set_type="WORKING",
    )
