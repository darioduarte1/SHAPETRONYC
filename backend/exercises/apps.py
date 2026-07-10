# =============================================================================
# apps.py
# -----------------------------------------------------------------------------
# Declara a configuração da app Django exercises.
# É usado pelo Django para registar a app responsável pelo catálogo de exercícios e escalas de máquinas.
# Mantém o nome técnico da app e opções de inicialização.
# =============================================================================
from django.apps import AppConfig


class ExercisesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'exercises'
