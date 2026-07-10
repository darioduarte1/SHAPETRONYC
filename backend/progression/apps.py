# =============================================================================
# apps.py
# -----------------------------------------------------------------------------
# Declara a configuração da app Django progression.
# É usado pelo Django para registar a app responsável por séries executadas e histórico de performance.
# Mantém o nome técnico da app e opções de inicialização.
# =============================================================================
from django.apps import AppConfig


class ProgressionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'progression'
