from django.contrib.auth.models import User

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import UserProfile
from .serializers import UserProfileSerializer


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
