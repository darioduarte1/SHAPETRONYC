from rest_framework import serializers

from .models import SetLog


class SetLogSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        if attrs.get("set_type") == "WARMUP":
            attrs["rir"] = None
            attrs["reached_failure"] = False

        return attrs

    class Meta:
        model = SetLog
        fields = "__all__"
