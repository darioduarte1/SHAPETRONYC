from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import NextSetRecommendationSerializer
from .services.training_coach_engine import calculate_training_coach_decision


class NextSetRecommendationView(APIView):
    def post(self, request):
        serializer = NextSetRecommendationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        recommendation = calculate_training_coach_decision(
            weight=data["weight"],
            reps=data["reps"],
            rir=data.get("rir"),
            is_failure=data["is_failure"],
            notes=data.get("notes", ""),
            set_type=data["set_type"],
        )

        return Response(recommendation, status=status.HTTP_200_OK)
