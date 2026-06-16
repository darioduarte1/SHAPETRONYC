from django.urls import path

from .views import ProgramTemplateListView

urlpatterns = [
    path("", ProgramTemplateListView.as_view(), name="program-template-list"),
]