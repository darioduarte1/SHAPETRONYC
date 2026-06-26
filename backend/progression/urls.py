from django.urls import path
from .views import ExerciseHistoryView, SetLogDetailView, SetLogListCreateView

urlpatterns = [
    path("set-logs/", SetLogListCreateView.as_view(), name="set-log-list-create"),
    path("set-logs/<int:pk>/", SetLogDetailView.as_view(), name="set-log-detail"),
    path("exercise-history/", ExerciseHistoryView.as_view(), name="exercise-history"),
]
