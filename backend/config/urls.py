from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/exercises/',include('exercises.urls')),
    path("api/progression/", include("progression.urls")),
    path("api/recommendations/", include("recommendations.urls")),
    path("api/programs/", include("programs.urls")), 
    path("api/accounts/", include("accounts.urls")),
    path("api/training/", include("training.urls")),
]