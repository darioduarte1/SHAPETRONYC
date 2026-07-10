# =============================================================================
# apps.py
# -----------------------------------------------------------------------------
# Declara a configuração da app Django training.
# É usado pelo Django para registar a app responsável por sessões, memória, calibração, blocos e feedback.
# Mantém o nome técnico da app e opções de inicialização.
# =============================================================================
from django.apps import AppConfig


class TrainingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'training'
