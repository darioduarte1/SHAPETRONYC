from django.urls import path

from .views import (
    GenerateProgramView,
    TrainingProgramDetailView,
    StartWorkoutSessionView,
    FinishWorkoutSessionView,
    WorkoutSessionListView,
)

urlpatterns = [
    path("generate-program/", GenerateProgramView.as_view()),
    path("program/<int:profile_id>/", TrainingProgramDetailView.as_view()),

    path("start-session/", StartWorkoutSessionView.as_view()),
    path("finish-session/", FinishWorkoutSessionView.as_view()),
    path("sessions/<int:profile_id>/", WorkoutSessionListView.as_view()),
]