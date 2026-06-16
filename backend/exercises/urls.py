from django.urls import path

from .views import ExerciseListCreateView

urlpatterns = [
    path(
        "",
        ExerciseListCreateView.as_view(),
        name="exercise-list"
    )
]