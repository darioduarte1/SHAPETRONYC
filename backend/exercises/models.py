from django.db import models


class Exercise(models.Model):
    MOVEMENT_PATTERN_CHOICES = [
        ("HORIZONTAL_PUSH", "Horizontal Push"),
        ("VERTICAL_PUSH", "Vertical Push"),
        ("HORIZONTAL_PULL", "Horizontal Pull"),
        ("VERTICAL_PULL", "Vertical Pull"),
        ("SQUAT", "Squat"),
        ("HINGE", "Hinge"),
        ("LUNGE", "Lunge"),
        ("HIP_THRUST", "Hip Thrust"),
        ("ISOLATION", "Isolation"),
        ("CORE", "Core"),
        ("CARDIO", "Cardio"),
    ]

    DIFFICULTY_CHOICES = [
        ("BEGINNER", "Beginner"),
        ("INTERMEDIATE", "Intermediate"),
        ("ADVANCED", "Advanced"),
    ]

    name = models.CharField(max_length=100)
    localized_name = models.CharField(max_length=120, blank=True)
    muscle_group = models.CharField(max_length=50)
    equipment = models.CharField(max_length=50)
    image_url = models.CharField(max_length=255, blank=True)
    main_weight_options = models.JSONField(default=list, blank=True)
    micro_weight_options = models.JSONField(default=list, blank=True)

    movement_pattern = models.CharField(
        max_length=50,
        choices=MOVEMENT_PATTERN_CHOICES,
        default="ISOLATION"
    )

    difficulty = models.CharField(
        max_length=30,
        choices=DIFFICULTY_CHOICES,
        default="BEGINNER"
    )

    is_compound = models.BooleanField(default=False)

    def __str__(self):
        return self.name
