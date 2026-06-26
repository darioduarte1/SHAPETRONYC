from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import UserProfile
from .serializers import UserProfileSerializer
from progression.models import SetLog
from training.models import (
    AdaptivePlanDecision,
    AthleteTrainingMemory,
    ExerciseCalibration,
    TrainingBlock,
    TrainingProgram,
    UserExerciseWeightScale,
    WorkoutSession,
)


class UserProfileListCreateView(generics.ListCreateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer

    def create(self, request, *args, **kwargs):
        user_id = request.data.get("user")
        existing_profile = UserProfile.objects.filter(user_id=user_id).first() if user_id else None

        if existing_profile:
            serializer = self.get_serializer(existing_profile, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)

        return super().create(request, *args, **kwargs)


class CreateUserView(APIView):
    def post(self, request):
        username = request.data.get("username")

        if not username:
            return Response(
                {"error": "Username is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user, created = User.objects.get_or_create(username=username)

        return Response(
            {
                "id": user.id,
                "username": user.username,
                "created": created,
            },
            status=status.HTTP_201_CREATED
        )


class UserTrainingExportView(APIView):
    def get(self, request, profile_id):
        try:
            profile = UserProfile.objects.select_related("user").get(id=profile_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        user = profile.user
        programs = TrainingProgram.objects.filter(user=user).prefetch_related(
            "workouts__exercises__exercise",
        ).order_by("-created_at")
        sessions = WorkoutSession.objects.filter(user=user).select_related(
            "workout",
            "workout__program",
        ).order_by("-started_at")
        set_logs = SetLog.objects.filter(user=user).select_related(
            "exercise",
            "training_exercise",
            "workout_session",
            "workout_session__workout",
        ).order_by("-created_at")
        memories = AthleteTrainingMemory.objects.filter(user=user).select_related(
            "exercise",
        ).order_by("-updated_at")
        decisions = AdaptivePlanDecision.objects.filter(user=user).select_related(
            "exercise",
            "training_exercise",
        ).order_by("-created_at")
        blocks = TrainingBlock.objects.filter(user=user).select_related(
            "program",
        ).order_by("-start_date", "-created_at")
        calibrations = ExerciseCalibration.objects.filter(user=user).select_related(
            "exercise",
        ).order_by("-updated_at")
        weight_scales = {
            scale.exercise_id: scale
            for scale in UserExerciseWeightScale.objects.filter(user=user)
        }

        payload = {
            "exported_at": timezone.now(),
            "profile": {
                "id": profile.id,
                "user_id": user.id,
                "username": user.username,
                "gender": profile.gender,
                "age": profile.age,
                "height_cm": profile.height_cm,
                "weight_kg": profile.weight_kg,
                "goal": profile.goal,
                "level": profile.level,
                "training_experience": profile.training_experience,
                "days_per_week": profile.days_per_week,
                "created_at": profile.created_at,
                "updated_at": profile.updated_at,
            },
            "programs": [
                {
                    "id": program.id,
                    "name": program.name,
                    "goal": program.goal,
                    "level": program.level,
                    "days_per_week": program.days_per_week,
                    "is_active": program.is_active,
                    "created_at": program.created_at,
                    "workouts": [
                        {
                            "id": workout.id,
                            "name": workout.name,
                            "order": workout.order,
                            "exercises": [
                                {
                                    "id": training_exercise.id,
                                    "exercise_id": training_exercise.exercise_id,
                                    "name": training_exercise.exercise.name,
                                    "localized_name": training_exercise.exercise.localized_name,
                                    "muscle_group": training_exercise.exercise.muscle_group,
                                    "equipment": training_exercise.exercise.equipment,
                                    "movement_pattern": training_exercise.exercise.movement_pattern,
                                    "is_compound": training_exercise.exercise.is_compound,
                                    "main_weight_options": (
                                        weight_scales[training_exercise.exercise_id].main_weight_options
                                        if training_exercise.exercise_id in weight_scales else []
                                    ),
                                    "micro_weight_options": (
                                        weight_scales[training_exercise.exercise_id].micro_weight_options
                                        if training_exercise.exercise_id in weight_scales else []
                                    ),
                                    "sets": training_exercise.sets,
                                    "target_min_reps": training_exercise.target_min_reps,
                                    "target_max_reps": training_exercise.target_max_reps,
                                    "target_rir": training_exercise.target_rir,
                                    "order": training_exercise.order,
                                }
                                for training_exercise in workout.exercises.all()
                            ],
                        }
                        for workout in program.workouts.all()
                    ],
                }
                for program in programs
            ],
            "workout_sessions": [
                {
                    "id": session.id,
                    "program_id": session.workout.program_id,
                    "program_name": session.workout.program.name,
                    "workout_id": session.workout_id,
                    "workout_name": session.workout.name,
                    "status": session.status,
                    "started_at": session.started_at,
                    "completed_at": session.completed_at,
                    "notes": session.notes,
                }
                for session in sessions
            ],
            "set_logs": [
                {
                    "id": set_log.id,
                    "workout_session_id": set_log.workout_session_id,
                    "workout_name": set_log.workout_session.workout.name if set_log.workout_session_id else "",
                    "training_exercise_id": set_log.training_exercise_id,
                    "exercise_id": set_log.exercise_id,
                    "exercise_name": set_log.exercise.name,
                    "set_number": set_log.set_number,
                    "set_type": set_log.set_type,
                    "planned_weight": set_log.planned_weight,
                    "weight_used": set_log.weight_used,
                    "target_min_reps": set_log.target_min_reps,
                    "target_max_reps": set_log.target_max_reps,
                    "reps_completed": set_log.reps_completed,
                    "rir": set_log.rir,
                    "reached_failure": set_log.reached_failure,
                    "notes": set_log.notes,
                    "created_at": set_log.created_at,
                }
                for set_log in set_logs
            ],
            "training_memories": [
                {
                    "id": memory.id,
                    "exercise_id": memory.exercise_id,
                    "exercise_name": memory.exercise.name,
                    "memory_type": memory.memory_type,
                    "title": memory.title,
                    "summary": memory.summary,
                    "evidence": memory.evidence,
                    "confidence": memory.confidence,
                    "severity": memory.severity,
                    "last_seen_at": memory.last_seen_at,
                    "created_at": memory.created_at,
                    "updated_at": memory.updated_at,
                }
                for memory in memories
            ],
            "adaptive_plan_decisions": [
                {
                    "id": decision.id,
                    "training_exercise_id": decision.training_exercise_id,
                    "exercise_id": decision.exercise_id,
                    "workout_name": decision.workout_name,
                    "exercise_name": decision.exercise_name,
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
                for decision in decisions
            ],
            "training_blocks": [
                {
                    "id": block.id,
                    "program_id": block.program_id,
                    "program_name": block.program.name if block.program_id else "",
                    "name": block.name,
                    "status": block.status,
                    "phase": block.phase,
                    "start_date": block.start_date,
                    "end_date": block.end_date,
                    "planned_weeks": block.planned_weeks,
                    "summary": block.summary,
                    "created_at": block.created_at,
                    "updated_at": block.updated_at,
                }
                for block in blocks
            ],
            "exercise_calibrations": [
                {
                    "id": calibration.id,
                    "exercise_id": calibration.exercise_id,
                    "exercise_name": calibration.exercise.name,
                    "status": calibration.status,
                    "estimated_working_weight": calibration.estimated_working_weight,
                    "target_reps": calibration.target_reps,
                    "target_rir": calibration.target_rir,
                    "confidence": calibration.confidence,
                    "calibration_sets": calibration.calibration_sets,
                    "scale_snapshot": calibration.scale_snapshot,
                    "notes": calibration.notes,
                    "created_at": calibration.created_at,
                    "updated_at": calibration.updated_at,
                }
                for calibration in calibrations
            ],
        }

        filename = f"shapetronyc-{user.username}-training-export.json"
        response = JsonResponse(
            payload,
            encoder=DjangoJSONEncoder,
            json_dumps_params={"indent": 2, "ensure_ascii": False},
        )
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response
