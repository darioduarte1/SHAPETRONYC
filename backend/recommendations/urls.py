# =============================================================================
# urls.py
# -----------------------------------------------------------------------------
# Define as rotas HTTP da app recommendations.
# Liga endpoints de recomendações, coach e progressão às respetivas views.
# É incluído no mapa principal backend/config/urls.py.
# =============================================================================
from django.urls import path
from .views import NextSetRecommendationView

urlpatterns = [
    path("next-set/", NextSetRecommendationView.as_view(), name="next-set"),
]