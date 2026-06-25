from django.urls import path

from .views import CreateUserView, UserProfileListCreateView, UserTrainingExportView

urlpatterns = [
    path("profiles/", UserProfileListCreateView.as_view(), name="profile-list-create"),
    path("create-user/", CreateUserView.as_view(), name="create-user"),
    path("profiles/<int:profile_id>/export/", UserTrainingExportView.as_view(), name="profile-training-export"),
]
