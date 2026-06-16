from django.urls import path

from .views import UserProfileListCreateView, CreateUserView

urlpatterns = [
    path("profiles/", UserProfileListCreateView.as_view(), name="profile-list-create"),
    path("create-user/", CreateUserView.as_view(), name="create-user"),
]