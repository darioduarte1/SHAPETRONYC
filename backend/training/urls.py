from django.urls import path

from .views import (
    AdaptivePlanDecisionListView,
    AdaptivePlanView,
    ApplyAdaptivePlanRecommendationView,
    AthleteDashboardView,
    GenerateProgramView,
    TrainingProgramDetailView,
    StartWorkoutSessionView,
    FinishWorkoutSessionView,
    WorkoutSessionListView,
)

urlpatterns = [
    path("generate-program/", GenerateProgramView.as_view()),
    path("program/<int:profile_id>/", TrainingProgramDetailView.as_view()),
    path("dashboard/<int:profile_id>/", AthleteDashboardView.as_view()),
    path("adaptive-plan/<int:profile_id>/", AdaptivePlanView.as_view()),
    path("adaptive-plan/decisions/<int:profile_id>/", AdaptivePlanDecisionListView.as_view()),
    path("adaptive-plan/apply/", ApplyAdaptivePlanRecommendationView.as_view()),

    path("start-session/", StartWorkoutSessionView.as_view()),
    path("finish-session/", FinishWorkoutSessionView.as_view()),
    path("sessions/<int:profile_id>/", WorkoutSessionListView.as_view()),
]
