from django.urls import path
from .views import ExerciseHistoryView, SetLogListCreateView

urlpatterns = [
    path("set-logs/", SetLogListCreateView.as_view(), name="set-log-list-create"),
    path("exercise-history/", ExerciseHistoryView.as_view(), name="exercise-history"),
]
