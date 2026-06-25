from django.db import transaction

from training.models import AdaptivePlanDecision, TrainingWorkoutExercise
from training.services.adaptive_plan import build_adaptive_plan


VALID_DECISION_STATUSES = {"APPLIED", "DEFERRED", "IGNORED"}
DECISION_LIMIT = 8


def serialize_adaptive_plan_decision(decision):
    return {
        "id": decision.id,
        "training_exercise": decision.training_exercise_id,
        "exercise": decision.exercise_id,
        "exercise_name": decision.exercise_name,
        "workout_name": decision.workout_name,
        "action": decision.action,
        "status": decision.status,
        "current_sets": decision.current_sets,
        "recommended_sets": decision.recommended_sets,
        "current_target_rir": decision.current_target_rir,
        "recommended_target_rir": decision.recommended_target_rir,
        "load_adjustment": decision.load_adjustment,
        "message": decision.message,
        "evidence": decision.evidence,
        "created_at": decision.created_at,
    }


def list_adaptive_plan_decisions(profile, limit=DECISION_LIMIT):
    decisions = AdaptivePlanDecision.objects.filter(
        user=profile.user,
    ).select_related(
        "exercise",
        "training_exercise",
    ).order_by("-created_at")[:limit]

    return [serialize_adaptive_plan_decision(decision) for decision in decisions]


def find_recommendation(profile, training_exercise_id):
    adaptive_plan = build_adaptive_plan(profile)

    for recommendation in adaptive_plan["recommendations"]:
        if recommendation["training_exercise"] == training_exercise_id:
            return recommendation

    return None


def create_decision_from_recommendation(profile, recommendation, decision_status):
    if decision_status not in VALID_DECISION_STATUSES:
        raise ValueError("Invalid adaptive decision status")

    training_exercise = TrainingWorkoutExercise.objects.select_for_update().select_related(
        "exercise",
        "workout",
        "workout__program",
    ).get(
        id=recommendation["training_exercise"],
        workout__program__user=profile.user,
        workout__program__is_active=True,
    )

    if decision_status == "APPLIED":
        training_exercise.sets = recommendation["recommended_sets"]
        training_exercise.target_rir = recommendation["recommended_target_rir"]
        training_exercise.save(update_fields=["sets", "target_rir"])

    decision = AdaptivePlanDecision.objects.create(
        user=profile.user,
        training_exercise=training_exercise,
        exercise=training_exercise.exercise,
        workout_name=recommendation["workout_name"],
        exercise_name=recommendation["exercise_name"],
        action=recommendation["action"],
        status=decision_status,
        current_sets=recommendation["current_sets"],
        recommended_sets=recommendation["recommended_sets"],
        current_target_rir=recommendation["current_target_rir"],
        recommended_target_rir=recommendation["recommended_target_rir"],
        load_adjustment=recommendation["load_adjustment"],
        message=recommendation["message"],
        evidence=recommendation["evidence"],
    )

    return decision, training_exercise


def apply_adaptive_plan_recommendation(profile, training_exercise_id, decision_status="APPLIED"):
    recommendation = find_recommendation(profile, training_exercise_id)

    if not recommendation:
        raise TrainingWorkoutExercise.DoesNotExist

    if recommendation["action"] == "maintain_plan" and decision_status == "APPLIED":
        raise ValueError("Maintain plan recommendations do not need to be applied")

    with transaction.atomic():
        decision, training_exercise = create_decision_from_recommendation(
            profile,
            recommendation,
            decision_status,
        )

    return {
        "decision": serialize_adaptive_plan_decision(decision),
        "updated_exercise": {
            "id": training_exercise.id,
            "sets": training_exercise.sets,
            "target_rir": training_exercise.target_rir,
            "load_adjustment": decision.load_adjustment,
        },
    }
