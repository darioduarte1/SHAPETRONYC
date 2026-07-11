# =============================================================================
# views.py
# -----------------------------------------------------------------------------
# Implementa os endpoints da app exercises.
# Fornece exercícios ao frontend e permite consultar ou guardar informação relacionada com escalas.
# Serve de camada HTTP entre o catálogo de exercícios e a interface da app.
# =============================================================================
from rest_framework import generics

from .models import Exercise
from .serializers import ExerciseSerializer


class ExerciseListCreateView(generics.ListCreateAPIView):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer


class ExerciseDetailView(generics.RetrieveUpdateAPIView):
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializer
