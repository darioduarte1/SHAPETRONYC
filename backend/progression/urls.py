from django.urls import path
from .views import SetLogListCreateView

urlpatterns = [
    path("set-logs/", SetLogListCreateView.as_view(), name="set-log-list-create"),
]