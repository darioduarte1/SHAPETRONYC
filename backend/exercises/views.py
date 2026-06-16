from rest_framework import generics

from .models import Exercise
from .serializers import ExerciseSerializer


class ExerciseListCreateView(generics.ListCreateAPIView):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer