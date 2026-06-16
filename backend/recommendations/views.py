from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import NextSetRecommendationSerializer
from .services.progression_engine import calculate_next_set


class NextSetRecommendationView(APIView):
    def post(self, request):
        serializer = NextSetRecommendationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data

        recommendation = calculate_next_set(
            weight=data["weight"],
            reps=data["reps"],
            rir=data.get("rir"),
            is_failure=data["is_failure"],
        )

        return Response(recommendation, status=status.HTTP_200_OK)