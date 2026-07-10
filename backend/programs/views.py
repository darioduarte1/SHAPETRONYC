# =============================================================================
# views.py
# -----------------------------------------------------------------------------
# Implementa os endpoints da app programs.
# Permite ao frontend gerar programas, consultar o plano do atleta e receber a estrutura de treinos.
# Coordena serializers e serviços de geração sem guardar lógica visual.
# =============================================================================
from rest_framework import generics

from .models import ProgramTemplate
from .serializers import ProgramTemplateSerializer


class ProgramTemplateListView(generics.ListAPIView):
    queryset = ProgramTemplate.objects.prefetch_related(
        "workouts__exercises__exercise"
    ).all()
    serializer_class = ProgramTemplateSerializer