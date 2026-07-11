# =============================================================================
# apps.py
# -----------------------------------------------------------------------------
# Declara a configuração da app Django accounts.
# É usado pelo Django para registar a app responsável por perfis de atleta e dados base de utilizador.
# Mantém o nome técnico da app e opções de inicialização.
# =============================================================================
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
