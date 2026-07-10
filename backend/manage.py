#!/usr/bin/env python
# =============================================================================
# manage.py
# -----------------------------------------------------------------------------
# Ponto de entrada de linha de comandos do backend Django.
# É usado para arrancar o servidor local, executar migrations, correr testes e aceder a todos os comandos de gestão do projeto.
# Este ficheiro não contém regras de negócio; encaminha os comandos para a configuração Django definida em config.settings.
# =============================================================================
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
