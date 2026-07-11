# =============================================================================
# serializers.py
# -----------------------------------------------------------------------------
# Transforma modelos da app accounts em dados JSON e valida dados recebidos pela API.
# É usado pelas views de criação, consulta e login de atletas.
# Garante que o frontend envia e recebe perfis no formato esperado.
# =============================================================================
from rest_framework import serializers
from .models import UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "username",
            "gender",
            "age",
            "height_cm",
            "weight_kg",
            "goal",
            "level",
            "training_experience",
            "days_per_week",
            "created_at",
            "updated_at",
        ]