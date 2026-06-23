from rest_framework import serializers


class NextSetRecommendationSerializer(serializers.Serializer):
    SET_TYPE_CHOICES = ("WARMUP", "WORKING", "DROP")

    weight = serializers.FloatField()
    reps = serializers.IntegerField()
    rir = serializers.IntegerField(required=False, allow_null=True)
    is_failure = serializers.BooleanField(default=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    set_type = serializers.ChoiceField(choices=SET_TYPE_CHOICES, default="WORKING")
