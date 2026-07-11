# =============================================================================
# urls.py
# -----------------------------------------------------------------------------
# Define as rotas HTTP da app exercises.
# Liga endpoints do catálogo, detalhes e escala de pesos às respetivas views.
# É incluído no mapa principal backend/config/urls.py.
# =============================================================================
from django.urls import path

from .views import ExerciseDetailView, ExerciseListCreateView

urlpatterns = [
    path(
        "",
        ExerciseListCreateView.as_view(),
        name="exercise-list"
    ),
    path(
        "<int:pk>/",
        ExerciseDetailView.as_view(),
        name="exercise-detail",
    ),
]
