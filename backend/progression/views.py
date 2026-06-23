from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import UserProfile
from training.models import TrainingWorkoutExercise, WorkoutSession
from .models import SetLog
from .serializers import SetLogSerializer
from .services.exercise_history_recommendation import calculate_recommended_set


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

        previous_session_ids = SetLog.objects.filter(
            user=profile.user,
            exercise_id=exercise_id,
            workout_session__status="COMPLETED",
        ).exclude(
            workout_session_id=session_id
        ).values_list(
            "workout_session_id",
            flat=True,
        ).distinct()

        previous_session = WorkoutSession.objects.filter(
            id__in=previous_session_ids,
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

        previous_sets_by_number = {
            set_log.set_number: set_log
            for set_log in previous_sets
        }
        max_rows = max(
            training_exercise.sets if training_exercise else 0,
            len(previous_sets_by_number),
            current_sets.count(),
            1,
        )
        recommended_sets = [
            {
                "set_number": set_number,
                **calculate_recommended_set(
                    previous_sets_by_number.get(set_number),
                ),
            }
            for set_number in range(1, max_rows + 1)
        ]

        return Response({
            "previous_session": {
                "id": previous_session.id,
                "workout_name": previous_session.workout.name,
                "completed_at": previous_session.completed_at,
            } if previous_session else None,
            "previous_sets": SetLogSerializer(previous_sets, many=True).data,
            "current_sets": SetLogSerializer(current_sets, many=True).data,
            "recommended_sets": recommended_sets,
        })
