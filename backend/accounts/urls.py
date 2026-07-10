# =============================================================================
# urls.py
# -----------------------------------------------------------------------------
# Define as rotas HTTP da app accounts.
# Liga URLs de perfis e autenticação simples às views correspondentes.
# É incluído no mapa principal backend/config/urls.py.
# =============================================================================
from django.urls import path

from .views import (
    CreateUserView,
    DeleteExperimentalUsersView,
    UserProfileListCreateView,
    UserTrainingExportView,
)

urlpatterns = [
    path("profiles/", UserProfileListCreateView.as_view(), name="profile-list-create"),
    path("create-user/", CreateUserView.as_view(), name="create-user"),
    path("experimental/delete-users/", DeleteExperimentalUsersView.as_view(), name="experimental-delete-users"),
    path("profiles/<int:profile_id>/export/", UserTrainingExportView.as_view(), name="profile-training-export"),
]
