from django.db import models


class Exercise(models.Model):
    name = models.CharField(max_length=100)

    muscle_group = models.CharField(
        max_length=50
    )

    equipment = models.CharField(
        max_length=50
    )

    def __str__(self):
        return self.name