# =============================================================================
# urls.py
# -----------------------------------------------------------------------------
# Define as rotas HTTP da app programs.
# Liga endpoints de geração, consulta e atualização de programas às respetivas views.
# É incluído no mapa principal backend/config/urls.py.
# =============================================================================
from django.urls import path

from .views import ProgramTemplateListView

urlpatterns = [
    path("", ProgramTemplateListView.as_view(), name="program-template-list"),
]