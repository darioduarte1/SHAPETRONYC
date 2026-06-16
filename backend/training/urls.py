from django.urls import path

from .views import (
    GenerateProgramView,
    TrainingProgramDetailView,
)

urlpatterns = [
    path("generate-program/", GenerateProgramView.as_view()),
    path("program/<int:profile_id>/", TrainingProgramDetailView.as_view()),
]