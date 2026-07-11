# =============================================================================
# apps.py
# -----------------------------------------------------------------------------
# Declara a configuração da app Django recommendations.
# É usado pelo Django para registar os motores e endpoints de recomendação da app.
# Mantém o nome técnico da app e opções de inicialização.
# =============================================================================
from django.apps import AppConfig


class RecommendationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recommendations'
