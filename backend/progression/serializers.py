# =============================================================================
# serializers.py
# -----------------------------------------------------------------------------
# Transforma registos de progressão em JSON e valida séries enviadas pelo frontend.
# É usado quando o atleta marca séries como feitas, desfaz registos ou consulta histórico.
# Garante consistência entre inputs do treino e dados persistidos.
# =============================================================================
from rest_framework import serializers

from .models import SetLog
from training.services.exercise_calibration import get_exercise_calibration_state


class SetLogSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        set_type = attrs.get("set_type") or getattr(self.instance, "set_type", "WORKING")

        if set_type == "WARMUP":
            attrs["rir"] = None
            attrs["reached_failure"] = False
            return attrs

        training_exercise = attrs.get("training_exercise") or getattr(self.instance, "training_exercise", None)
        user = attrs.get("user") or getattr(self.instance, "user", None)
        exercise = attrs.get("exercise") or getattr(self.instance, "exercise", None)

        if training_exercise and user and exercise:
            calibration_state = get_exercise_calibration_state(user, exercise)

            if calibration_state["needs_calibration"]:
                raise serializers.ValidationError({
                    "calibration": "Este exercício precisa de calibração inicial antes de aceitar séries normais.",
                    "reason": calibration_state["reason"],
                })

        return attrs

    class Meta:
        model = SetLog
        fields = "__all__"
