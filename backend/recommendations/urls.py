from django.urls import path
from .views import NextSetRecommendationView

urlpatterns = [
    path("next-set/", NextSetRecommendationView.as_view(), name="next-set"),
]