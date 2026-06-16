from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.models import UserProfile

from .serializers import TrainingProgramSerializer
from .services.training_generator import generate_training_program
from .models import TrainingProgram


class GenerateProgramView(APIView):

    def post(self, request):

        profile_id = request.data.get("profile_id")

        profile = UserProfile.objects.get(id=profile_id)

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