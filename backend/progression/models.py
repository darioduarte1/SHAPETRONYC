from django.db import models
from django.contrib.auth.models import User
from exercises.models import Exercise

class SetLog(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE
    )

    set_number = models.PositiveIntegerField()

    weight = models.FloatField()

    reps = models.PositiveIntegerField()

    rir = models.IntegerField(
        null=True,
        blank=True
    )

    is_failure = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )