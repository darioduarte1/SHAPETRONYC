from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.models import UserProfile
from progression.models import SetLog
from recommendations.services.ai_coach_engine import generate_session_ai_coach_summary
from recommendations.services.workout_progression_engine import calculate_workout_progression

from .serializers import TrainingProgramSerializer, WorkoutSessionSerializer
from .services.adaptive_plan import build_adaptive_plan
from .services.adaptive_plan_decisions import (
    apply_adaptive_plan_recommendation,
    list_adaptive_plan_decisions,
)
from .services.athlete_dashboard import build_athlete_dashboard
from .services.training_memory import refresh_training_memory
from .services.training_generator import generate_training_program
from .services.training_blocks import build_training_block, list_training_blocks
from .services.exercise_substitution import get_substitution_options, replace_training_exercise
from .services.exercise_calibration import (
    get_exercise_calibration_state,
    upsert_exercise_calibration,
)
from .services.user_exercise_weight_scale import (
    get_user_exercise_weight_scale,
    serialize_user_exercise_weight_scale,
    upsert_user_exercise_weight_scale,
)
from .services.weekly_feedback import build_weekly_feedback
from .models import (
    ExerciseCalibration,
    TrainingProgram,
    TrainingWorkout,
    TrainingWorkoutExercise,
    WorkoutSession,
)
from exercises.models import Exercise


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
        workout_exercise_ids = session.workout.exercises.values_list("exercise_id", flat=True)
        calibrations = ExerciseCalibration.objects.filter(
            user=session.user,
            exercise_id__in=workout_exercise_ids,
        ).select_related("exercise")

        if session.started_at and session.completed_at:
            session_calibrations = calibrations.filter(
                updated_at__gte=session.started_at,
                updated_at__lte=session.completed_at,
            )
        else:
            session_calibrations = calibrations.none()

        if not set_logs.exists() and not session_calibrations.exists():
            session_calibrations = calibrations

        progression = calculate_workout_progression(session.workout, set_logs, session_calibrations)
        ai_coach_summary = generate_session_ai_coach_summary(
            session.workout,
            set_logs,
            progression,
            notes,
            session_calibrations,
        )
        try:
            profile = UserProfile.objects.get(user=session.user)
            refresh_training_memory(profile)
        except UserProfile.DoesNotExist:
            pass

        return Response(
            {
                **serializer.data,
                "next_workout_progression": progression,
                "ai_coach_summary": ai_coach_summary,
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


class AthleteDashboardView(APIView):

    def get(self, request, profile_id):
        try:
            profile = UserProfile.objects.get(id=profile_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(build_athlete_dashboard(profile))


class AdaptivePlanView(APIView):

    def get(self, request, profile_id):
        try:
            profile = UserProfile.objects.get(id=profile_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(build_adaptive_plan(profile))


class AdaptivePlanDecisionListView(APIView):

    def get(self, request, profile_id):
        try:
            profile = UserProfile.objects.get(id=profile_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            "profile_id": profile.id,
            "decisions": list_adaptive_plan_decisions(profile),
        })


class ApplyAdaptivePlanRecommendationView(APIView):

    def post(self, request):
        profile_id = request.data.get("profile_id")
        training_exercise_id = request.data.get("training_exercise_id")
        decision_status = request.data.get("status", "APPLIED")

        if not profile_id or not training_exercise_id:
            return Response(
                {"error": "profile_id and training_exercise_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            profile = UserProfile.objects.get(id=profile_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            result = apply_adaptive_plan_recommendation(
                profile,
                int(training_exercise_id),
                decision_status,
            )
        except (ValueError, TypeError) as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except TrainingWorkoutExercise.DoesNotExist:
            return Response(
                {"error": "Adaptive recommendation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(result, status=status.HTTP_200_OK)


class WeeklyFeedbackView(APIView):

    def get(self, request, profile_id):
        try:
            profile = UserProfile.objects.get(id=profile_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(build_weekly_feedback(profile))


class TrainingBlockView(APIView):

    def get(self, request, profile_id):
        try:
            profile = UserProfile.objects.get(id=profile_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            **build_training_block(profile),
            "history": list_training_blocks(profile),
        })


class ExerciseSubstitutionOptionsView(APIView):

    def get(self, request, training_exercise_id):
        try:
            training_exercise = TrainingWorkoutExercise.objects.select_related("exercise").get(
                id=training_exercise_id,
            )
        except TrainingWorkoutExercise.DoesNotExist:
            return Response(
                {"error": "Training exercise not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            "training_exercise": training_exercise.id,
            "exercise": training_exercise.exercise_id,
            "muscle_group": training_exercise.exercise.muscle_group,
            "options": get_substitution_options(training_exercise),
        })


class ReplaceTrainingExerciseView(APIView):

    def post(self, request):
        training_exercise_id = request.data.get("training_exercise_id")
        replacement_exercise_id = request.data.get("replacement_exercise_id")

        if not training_exercise_id or not replacement_exercise_id:
            return Response(
                {"error": "training_exercise_id and replacement_exercise_id are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            training_exercise = TrainingWorkoutExercise.objects.select_related("exercise").get(
                id=training_exercise_id,
            )
            updated_training_exercise = replace_training_exercise(
                training_exercise,
                int(replacement_exercise_id),
            )
        except (ValueError, TypeError) as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except TrainingWorkoutExercise.DoesNotExist:
            return Response(
                {"error": "Training exercise not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exercise.DoesNotExist:
            return Response(
                {"error": "Replacement exercise not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(TrainingProgramSerializer(updated_training_exercise.workout.program).data)


class ExerciseCalibrationView(APIView):

    def get(self, request, profile_id, training_exercise_id):
        try:
            profile = UserProfile.objects.get(id=profile_id)
            training_exercise = TrainingWorkoutExercise.objects.select_related("exercise").get(
                id=training_exercise_id,
                workout__program__user=profile.user,
            )
        except (UserProfile.DoesNotExist, TrainingWorkoutExercise.DoesNotExist, ValueError):
            return Response(
                {"error": "Calibration target not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(get_exercise_calibration_state(profile.user, training_exercise.exercise))


class ExerciseWeightScaleView(APIView):

    def get(self, request, profile_id, training_exercise_id):
        try:
            profile = UserProfile.objects.get(id=profile_id)
            training_exercise = TrainingWorkoutExercise.objects.select_related("exercise").get(
                id=training_exercise_id,
                workout__program__user=profile.user,
            )
        except (UserProfile.DoesNotExist, TrainingWorkoutExercise.DoesNotExist, ValueError):
            return Response(
                {"error": "Weight scale target not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(serialize_user_exercise_weight_scale(profile.user, training_exercise.exercise))

    def patch(self, request, profile_id, training_exercise_id):
        try:
            profile = UserProfile.objects.get(id=profile_id)
            training_exercise = TrainingWorkoutExercise.objects.select_related("exercise").get(
                id=training_exercise_id,
                workout__program__user=profile.user,
            )
        except (UserProfile.DoesNotExist, TrainingWorkoutExercise.DoesNotExist, ValueError):
            return Response(
                {"error": "Weight scale target not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        scale = upsert_user_exercise_weight_scale(
            profile.user,
            training_exercise.exercise,
            request.data.get("main_weight_options", []),
            request.data.get("micro_weight_options", []),
        )

        return Response(scale, status=status.HTTP_200_OK)


class SaveExerciseCalibrationView(APIView):

    def post(self, request):
        profile_id = request.data.get("profile_id")
        training_exercise_id = request.data.get("training_exercise_id")

        try:
            profile = UserProfile.objects.get(id=profile_id)
            training_exercise = TrainingWorkoutExercise.objects.select_related("exercise").get(
                id=training_exercise_id,
                workout__program__user=profile.user,
            )
        except (UserProfile.DoesNotExist, TrainingWorkoutExercise.DoesNotExist, ValueError):
            return Response(
                {"error": "Calibration target not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        scale = get_user_exercise_weight_scale(profile.user, training_exercise.exercise)

        if not scale["configured"]:
            return Response(
                {
                    "error": "A escala da máquina é obrigatória antes da calibração experimental.",
                    "reason": "scale_required",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        calibration = upsert_exercise_calibration(
            profile.user,
            training_exercise.exercise,
            {
                "weight_used": request.data.get("weight_used"),
                "result_color": request.data.get("result_color"),
                "reps_completed": request.data.get("reps_completed"),
                "rir": request.data.get("rir"),
                "reached_failure": request.data.get("reached_failure", False),
                "notes": request.data.get("notes", ""),
            },
            notes=request.data.get("notes", ""),
        )

        return Response(calibration, status=status.HTTP_200_OK)
