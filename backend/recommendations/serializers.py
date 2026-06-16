from rest_framework import serializers


class NextSetRecommendationSerializer(serializers.Serializer):
    weight = serializers.FloatField()
    reps = serializers.IntegerField()
    rir = serializers.IntegerField(required=False, allow_null=True)
    is_failure = serializers.BooleanField(default=False)