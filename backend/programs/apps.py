# =============================================================================
# apps.py
# -----------------------------------------------------------------------------
# Declara a configuração da app Django programs.
# É usado pelo Django para registar a app responsável por programas, workouts e exercícios planeados.
# Mantém o nome técnico da app e opções de inicialização.
# =============================================================================
from django.apps import AppConfig


class ProgramsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'programs'
