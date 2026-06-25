from rest_framework import serializers
from .models import Exercise


class ExerciseSerializer(serializers.ModelSerializer):
    def validate_main_weight_options(self, value):
        return self._validate_weight_options(value)

    def validate_micro_weight_options(self, value):
        return self._validate_weight_options(value)

    def _validate_weight_options(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Weight options must be a list.")

        cleaned_values = []

        for item in value:
            try:
                number = float(item)
            except (TypeError, ValueError):
                raise serializers.ValidationError("Each weight option must be numeric.")

            if number < 0:
                raise serializers.ValidationError("Weight options cannot be negative.")

            cleaned_values.append(round(number, 2))

        return sorted(set(cleaned_values))

    class Meta:
        model = Exercise
        fields = "__all__"
