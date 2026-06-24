from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserProfile
from training.models import TrainingWorkoutExercise, WorkoutSession
from .models import SetLog
from .serializers import SetLogSerializer
from .services.exercise_history_recommendation import (
    HISTORY_LIMIT,
    build_history_based_recommended_sets,
    group_sets_by_session,
    summarize_recent_sessions,
)


class SetLogListCreateView(generics.ListCreateAPIView):
    queryset = SetLog.objects.all().order_by("-created_at")
    serializer_class = SetLogSerializer


class ExerciseHistoryView(APIView):
    def get(self, request):
        profile_id = request.query_params.get("profile_id")
        exercise_id = request.query_params.get("exercise_id")
        session_id = request.query_params.get("session_id")
        training_exercise_id = request.query_params.get("training_exercise_id")

        if not profile_id or not exercise_id:
            return Response(
                {"error": "profile_id and exercise_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            profile = UserProfile.objects.get(id=profile_id)
        except (UserProfile.DoesNotExist, ValueError):
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        training_exercise = None
        current_session = None

        if session_id:
            try:
                current_session = WorkoutSession.objects.select_related("workout").get(
                    id=session_id,
                    user=profile.user,
                )
            except (WorkoutSession.DoesNotExist, ValueError):
                current_session = None

        if training_exercise_id:
            try:
                training_exercise = TrainingWorkoutExercise.objects.filter(
                    id=training_exercise_id,
                    exercise_id=exercise_id,
                ).first()
            except ValueError:
                training_exercise = None

        current_sets = SetLog.objects.filter(
            user=profile.user,
            exercise_id=exercise_id,
            workout_session_id=session_id,
        ).order_by("set_number", "created_at")

        recent_sessions = WorkoutSession.objects.filter(
            user=profile.user,
            status="COMPLETED",
            set_logs__exercise_id=exercise_id,
        )

        if current_session:
            recent_sessions = recent_sessions.filter(
                workout__name=current_session.workout.name,
            ).exclude(
                id=current_session.id,
            )

        recent_session_ids = list(
            recent_sessions.order_by(
                "-completed_at",
                "-started_at",
            ).values_list(
                "id",
                flat=True,
            ).distinct()[:HISTORY_LIMIT]
        )

        previous_session = WorkoutSession.objects.filter(
            id__in=recent_session_ids,
            user=profile.user,
        ).order_by(
            "-completed_at",
            "-started_at",
        ).first()

        previous_sets = SetLog.objects.none()

        if previous_session:
            previous_sets = SetLog.objects.filter(
                user=profile.user,
                exercise_id=exercise_id,
                workout_session=previous_session,
            ).order_by("set_number", "created_at")

        recent_set_logs = SetLog.objects.filter(
            user=profile.user,
            exercise_id=exercise_id,
            workout_session_id__in=recent_session_ids,
        ).select_related(
            "workout_session__workout",
        ).order_by(
            "-workout_session__completed_at",
            "-workout_session__started_at",
            "set_number",
            "created_at",
        )
        recent_session_sets = group_sets_by_session(recent_set_logs)
        planned_working_sets = training_exercise.sets if training_exercise else 1
        recommended_sets = build_history_based_recommended_sets(
            recent_session_sets,
            planned_working_sets,
        )
        max_rows = max(
            planned_working_sets + 1,
            current_sets.count(),
            len(recommended_sets),
            1,
        )

        return Response({
            "previous_session": {
                "id": previous_session.id,
                "workout_name": previous_session.workout.name,
                "completed_at": previous_session.completed_at,
            } if previous_session else None,
            "previous_sets": SetLogSerializer(previous_sets, many=True).data,
            "current_sets": SetLogSerializer(current_sets, many=True).data,
            "history_sets": SetLogSerializer(recent_set_logs, many=True).data,
            "recommended_sets": recommended_sets,
            "history_summary": summarize_recent_sessions(recent_session_sets),
            "history_scope": {
                "workout_name": current_session.workout.name if current_session else None,
                "session_limit": HISTORY_LIMIT,
                "sessions_found": len(recent_session_sets),
                "rows": max_rows,
            },
        })
