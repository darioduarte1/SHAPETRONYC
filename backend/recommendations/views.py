from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.models import UserProfile
from training.models import TrainingWorkoutExercise

from .serializers import NextSetRecommendationSerializer
from .services.ai_training_decision_engine import generate_ai_training_decision
from .services.training_coach_engine import calculate_training_coach_decision


def build_user_context(profile_id, provided_context):
    context = dict(provided_context or {})

    if not profile_id:
        return context

    try:
        profile = UserProfile.objects.get(id=profile_id)
    except (UserProfile.DoesNotExist, ValueError):
        return context

    context.update({
        "user_id": profile.user_id,
        "goal": profile.goal,
        "level": profile.level,
        "training_experience": profile.training_experience,
        "days_per_week": profile.days_per_week,
        "body_weight": profile.weight_kg,
        "age": profile.age,
        "gender": profile.gender,
    })

    return context


def build_exercise_context(training_exercise_id, provided_context):
    context = dict(provided_context or {})

    if not training_exercise_id:
        return context

    try:
        training_exercise = TrainingWorkoutExercise.objects.select_related(
            "exercise",
            "workout",
        ).get(id=training_exercise_id)
    except (TrainingWorkoutExercise.DoesNotExist, ValueError):
        return context

    exercise = training_exercise.exercise
    context.update({
        "exercise_id": exercise.id,
        "exercise_name": exercise.name,
        "muscle_group": exercise.muscle_group,
        "movement_pattern": exercise.movement_pattern,
        "is_compound": exercise.is_compound,
        "equipment": exercise.equipment,
        "target_min_reps": training_exercise.target_min_reps,
        "target_max_reps": training_exercise.target_max_reps,
        "target_rir": training_exercise.target_rir,
        "planned_sets": training_exercise.sets,
        "workout_id": training_exercise.workout_id,
        "workout_name": training_exercise.workout.name,
    })

    return context


class NextSetRecommendationView(APIView):
    def post(self, request):
        serializer = NextSetRecommendationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user_context = build_user_context(data.get("profile_id"), data.get("user_context", {}))
        exercise_context = build_exercise_context(
            data.get("training_exercise_id"),
            data.get("exercise_context", {}),
        )
        session_context = {
            **data.get("session_context", {}),
            "workout_session_id": data.get("workout_session_id"),
            "current_set_number": data.get("set_number"),
            "planned_sets": data.get("total_sets") or exercise_context.get("planned_sets"),
        }
        target_min_reps = (
            data.get("target_min_reps")
            or exercise_context.get("target_min_reps")
            or 10
        )
        target_max_reps = (
            data.get("target_max_reps")
            or exercise_context.get("target_max_reps")
            or 12
        )
        target_rir = data.get("target_rir") or exercise_context.get("target_rir") or 2

        local_recommendation = calculate_training_coach_decision(
            weight=data["weight"],
            reps=data["reps"],
            rir=data.get("rir"),
            is_failure=data["is_failure"],
            notes=data.get("notes", ""),
            set_type=data["set_type"],
            set_number=data.get("set_number"),
            total_sets=data.get("total_sets"),
            current_sets=data.get("current_sets", []),
            previous_sets=data.get("previous_sets", []),
            history_sets=data.get("history_sets", []),
            target_min_reps=target_min_reps,
            target_max_reps=target_max_reps,
            target_rir=target_rir,
            exercise_context=exercise_context,
            user_context=user_context,
            session_context=session_context,
        )
        request_context = {
            "weight": data["weight"],
            "reps": data["reps"],
            "rir": data.get("rir"),
            "is_failure": data["is_failure"],
            "notes": data.get("notes", ""),
            "set_type": data["set_type"],
            "set_number": data.get("set_number"),
            "total_sets": data.get("total_sets") or exercise_context.get("planned_sets"),
            "target_min_reps": target_min_reps,
            "target_max_reps": target_max_reps,
            "target_rir": target_rir,
            "user_context": user_context,
            "exercise_context": exercise_context,
            "session_context": session_context,
            "current_sets": data.get("current_sets", []),
            "previous_sets": data.get("previous_sets", []),
            "history_sets": data.get("history_sets", []),
        }
        recommendation = generate_ai_training_decision(local_recommendation, request_context)

        return Response(recommendation, status=status.HTTP_200_OK)
