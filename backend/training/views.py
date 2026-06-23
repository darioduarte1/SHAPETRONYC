from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.models import UserProfile
from progression.models import SetLog
from recommendations.services.workout_progression_engine import calculate_workout_progression

from .serializers import TrainingProgramSerializer, WorkoutSessionSerializer
from .services.training_generator import generate_training_program
from .models import TrainingProgram, TrainingWorkout, WorkoutSession


class GenerateProgramView(APIView):

    def post(self, request):
        profile_id = request.data.get("profile_id")

        if not profile_id:
            return Response(
                {"error": "profile_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            profile = UserProfile.objects.get(id=profile_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        program = generate_training_program(profile)

        serializer = TrainingProgramSerializer(program)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class TrainingProgramDetailView(APIView):

    def get(self, request, profile_id):
        profile = UserProfile.objects.get(id=profile_id)

        program = TrainingProgram.objects.filter(
            user=profile.user,
            is_active=True
        ).first()

        if not program:
            return Response(
                {"error": "No active program found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = TrainingProgramSerializer(program)

        return Response(serializer.data)


class StartWorkoutSessionView(APIView):

    def post(self, request):
        profile_id = request.data.get("profile_id")
        workout_id = request.data.get("workout_id")

        if not profile_id or not workout_id:
            return Response(
                {"error": "profile_id and workout_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile = UserProfile.objects.get(id=profile_id)
        workout = TrainingWorkout.objects.get(id=workout_id)

        session = WorkoutSession.objects.create(
            user=profile.user,
            workout=workout,
            status="IN_PROGRESS",
        )

        serializer = WorkoutSessionSerializer(session)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FinishWorkoutSessionView(APIView):

    def post(self, request):
        session_id = request.data.get("session_id")
        notes = request.data.get("notes", "")

        if not session_id:
            return Response(
                {"error": "session_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        session = WorkoutSession.objects.get(id=session_id)
        session.status = "COMPLETED"
        session.completed_at = timezone.now()
        session.notes = notes
        session.save()

        serializer = WorkoutSessionSerializer(session)
        set_logs = SetLog.objects.filter(
            user=session.user,
            workout_session=session,
        ).select_related(
            "training_exercise__exercise",
        ).order_by(
            "training_exercise__order",
            "set_number",
            "created_at",
        )
        progression = calculate_workout_progression(session.workout, set_logs)

        return Response(
            {
                **serializer.data,
                "next_workout_progression": progression,
            },
            status=status.HTTP_200_OK,
        )


class WorkoutSessionListView(APIView):

    def get(self, request, profile_id):
        profile = UserProfile.objects.get(id=profile_id)

        sessions = WorkoutSession.objects.filter(
            user=profile.user
        ).order_by("-started_at")

        serializer = WorkoutSessionSerializer(sessions, many=True)

        return Response(serializer.data)
