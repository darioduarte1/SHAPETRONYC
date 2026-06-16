from rest_framework import generics
from .models import SetLog
from .serializers import SetLogSerializer


class SetLogListCreateView(generics.ListCreateAPIView):
    queryset = SetLog.objects.all().order_by("-created_at")
    serializer_class = SetLogSerializer