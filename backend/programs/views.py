from rest_framework import generics

from .models import ProgramTemplate
from .serializers import ProgramTemplateSerializer


class ProgramTemplateListView(generics.ListAPIView):
    queryset = ProgramTemplate.objects.prefetch_related(
        "workouts__exercises__exercise"
    ).all()
    serializer_class = ProgramTemplateSerializer