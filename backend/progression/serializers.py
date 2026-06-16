from rest_framework import serializers

from .models import SetLog


class SetLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SetLog
        fields = "__all__"