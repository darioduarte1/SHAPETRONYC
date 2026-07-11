# =============================================================================
# adaptive_plan.py
# -----------------------------------------------------------------------------
# Serviço que constrói o plano adaptativo do atleta.
# É usado para detetar exercícios que precisam de ajuste de carga, volume, RIR ou recuperação.
# Transforma histórico e estado atual em recomendações acionáveis no painel adaptativo.
# =============================================================================
from training.models import TrainingProgram
from training.services.athlete_dashboard import build_athlete_dashboard


WEIGHT_STEP = 2.5


def memory_by_exercise_and_type(memories):
    indexed_memories = {}

    for memory in memories:
        indexed_memories.setdefault(memory["exercise_id"], {})[memory["memory_type"]] = memory

    return indexed_memories


def exercise_ids(items):
    return {item["exercise_id"] for item in items}


def build_recommendation(training_exercise, memories_by_type, progressing_exercises, watchlist_exercises):
    exercise = training_exercise.exercise
    base_recommendation = {
        "training_exercise": training_exercise.id,
        "exercise": exercise.id,
        "exercise_name": exercise.name,
        "current_sets": training_exercise.sets,
        "current_target_rir": training_exercise.target_rir,
        "recommended_sets": training_exercise.sets,
        "recommended_target_rir": training_exercise.target_rir,
        "load_adjustment": 0,
        "priority": "low",
        "confidence": "baixa",
        "evidence": [],
    }

    if "WATCHLIST" in memories_by_type or exercise.id in watchlist_exercises:
        memory = memories_by_type.get("WATCHLIST")

        return {
            **base_recommendation,
            "action": "protect_recovery",
            "title": "Protege recuperação",
            "message": "Mantém ou baixa a carga, reduz uma série se a técnica quebrar e procura mais margem antes de voltar a subir.",
            "recommended_sets": max(1, training_exercise.sets - 1),
            "recommended_target_rir": max(training_exercise.target_rir, 3),
            "load_adjustment": -WEIGHT_STEP,
            "priority": "high",
            "confidence": memory["confidence"] if memory else "média",
            "evidence": memory["evidence"] if memory else ["Exercício aparece na watchlist do dashboard"],
        }

    if "EFFORT_PATTERN" in memories_by_type:
        memory = memories_by_type["EFFORT_PATTERN"]

        return {
            **base_recommendation,
            "action": "increase_margin",
            "title": "Aumenta margem",
            "message": "Mantém a carga e procura terminar com mais reserva antes de progredir.",
            "recommended_target_rir": max(training_exercise.target_rir, 3),
            "priority": "medium",
            "confidence": memory["confidence"],
            "evidence": memory["evidence"],
        }

    if "PROGRESSION" in memories_by_type or exercise.id in progressing_exercises:
        memory = memories_by_type.get("PROGRESSION")

        return {
            **base_recommendation,
            "action": "progress_load",
            "title": "Progressão controlada",
            "message": "O histórico permite tentar subir um passo de carga mantendo o volume planeado.",
            "load_adjustment": WEIGHT_STEP,
            "priority": "medium",
            "confidence": memory["confidence"] if memory else "média",
            "evidence": memory["evidence"] if memory else ["Exercício aparece como progressão no dashboard"],
        }

    return {
        **base_recommendation,
        "action": "maintain_plan",
        "title": "Mantém plano",
        "message": "Sem memória suficiente para alterar este exercício. Mantém o plano e recolhe mais dados.",
        "evidence": ["Sem sinais persistentes para este exercício"],
    }


def build_adaptive_plan(profile):
    program = TrainingProgram.objects.filter(
        user=profile.user,
        is_active=True,
    ).prefetch_related(
        "workouts__exercises__exercise",
    ).first()

    if not program:
        return {
            "profile_id": profile.id,
            "program": None,
            "program_name": "",
            "recommendations": [],
            "summary": {
                "exercise_count": 0,
                "action_counts": {},
                "high_priority_count": 0,
            },
        }

    dashboard = build_athlete_dashboard(profile)
    memories_by_exercise = memory_by_exercise_and_type(dashboard.get("training_memories", []))
    progressing_exercises = exercise_ids(dashboard.get("top_progressing_exercises", []))
    watchlist_exercises = exercise_ids(dashboard.get("watchlist_exercises", []))
    recommendations = []

    for workout in program.workouts.all():
        for training_exercise in workout.exercises.all():
            recommendations.append(
                {
                    "workout": workout.id,
                    "workout_name": workout.name,
                    **build_recommendation(
                        training_exercise,
                        memories_by_exercise.get(training_exercise.exercise_id, {}),
                        progressing_exercises,
                        watchlist_exercises,
                    ),
                }
            )

    action_counts = {}

    for recommendation in recommendations:
        action = recommendation["action"]
        action_counts[action] = action_counts.get(action, 0) + 1

    return {
        "profile_id": profile.id,
        "program": program.id,
        "program_name": program.name,
        "recommendations": recommendations,
        "summary": {
            "exercise_count": len(recommendations),
            "action_counts": action_counts,
            "high_priority_count": len([
                recommendation
                for recommendation in recommendations
                if recommendation["priority"] == "high"
            ]),
        },
    }
