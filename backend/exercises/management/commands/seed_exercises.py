# =============================================================================
# seed_exercises.py
# -----------------------------------------------------------------------------
# Comando de gestão para popular o catálogo inicial de exercícios.
# É executado manualmente através do manage.py quando é preciso criar ou atualizar exercícios base da app.
# Centraliza nomes, grupos musculares, categorias, imagens e dados usados na geração dos programas.
# =============================================================================
from django.core.management.base import BaseCommand

from exercises.models import Exercise


EXERCISES = [
    # Chest
    ("Chest Press Machine", "Chest", "Machine", "HORIZONTAL_PUSH", "BEGINNER", True),
    ("Incline Chest Press", "Chest", "Machine", "HORIZONTAL_PUSH", "BEGINNER", True),
    ("Pec Deck", "Chest", "Machine", "ISOLATION", "BEGINNER", False),
    ("Cable Fly", "Chest", "Cable", "ISOLATION", "INTERMEDIATE", False),

    # Back
    ("Lat Pulldown", "Back", "Cable", "VERTICAL_PULL", "BEGINNER", True),
    ("Seated Row Machine", "Back", "Machine", "HORIZONTAL_PULL", "BEGINNER", True),
    ("Chest Supported Row", "Back", "Machine", "HORIZONTAL_PULL", "BEGINNER", True),
    ("Straight Arm Pulldown", "Back", "Cable", "ISOLATION", "INTERMEDIATE", False),

    # Shoulders
    ("Shoulder Press", "Shoulders", "Machine", "VERTICAL_PUSH", "BEGINNER", True),
    ("Lateral Raise Machine", "Shoulders", "Machine", "ISOLATION", "BEGINNER", False),
    ("Cable Lateral Raise", "Shoulders", "Cable", "ISOLATION", "INTERMEDIATE", False),
    ("Rear Delt Fly", "Shoulders", "Machine", "ISOLATION", "BEGINNER", False),

    # Biceps
    ("Biceps Curl Machine", "Biceps", "Machine", "ISOLATION", "BEGINNER", False),
    ("Dumbbell Curl", "Biceps", "Dumbbell", "ISOLATION", "BEGINNER", False),
    ("Hammer Curl", "Biceps", "Dumbbell", "ISOLATION", "BEGINNER", False),

    # Triceps
    ("Triceps Pushdown", "Triceps", "Cable", "ISOLATION", "BEGINNER", False),
    ("Overhead Triceps Extension", "Triceps", "Cable", "ISOLATION", "INTERMEDIATE", False),
    ("Dip Machine", "Triceps", "Machine", "HORIZONTAL_PUSH", "INTERMEDIATE", True),

    # Quads
    ("Leg Press", "Quads", "Machine", "SQUAT", "BEGINNER", True),
    ("Leg Extension", "Quads", "Machine", "ISOLATION", "BEGINNER", False),
    ("Hack Squat", "Quads", "Machine", "SQUAT", "INTERMEDIATE", True),

    # Hamstrings
    ("Seated Leg Curl", "Hamstrings", "Machine", "ISOLATION", "BEGINNER", False),
    ("Lying Leg Curl", "Hamstrings", "Machine", "ISOLATION", "BEGINNER", False),
    ("Romanian Deadlift", "Hamstrings", "Barbell", "HINGE", "INTERMEDIATE", True),

    # Glutes
    ("Hip Thrust Machine", "Glutes", "Machine", "HIP_THRUST", "BEGINNER", True),
    ("Glute Bridge", "Glutes", "Bodyweight", "HIP_THRUST", "BEGINNER", True),
    ("Cable Kickback", "Glutes", "Cable", "ISOLATION", "BEGINNER", False),

    # Calves
    ("Standing Calf Raise", "Calves", "Machine", "ISOLATION", "BEGINNER", False),
    ("Seated Calf Raise", "Calves", "Machine", "ISOLATION", "BEGINNER", False),

    # Core
    ("Crunch Machine", "Core", "Machine", "CORE", "BEGINNER", False),
    ("Plank", "Core", "Bodyweight", "CORE", "BEGINNER", False),
    ("Hanging Knee Raise", "Core", "Bodyweight", "CORE", "INTERMEDIATE", False),

    # Cardio
    ("Treadmill Incline Walk", "Cardio", "Machine", "CARDIO", "BEGINNER", False),
    ("Bike", "Cardio", "Machine", "CARDIO", "BEGINNER", False),
    ("Rowing Machine", "Cardio", "Machine", "CARDIO", "INTERMEDIATE", False),
]


class Command(BaseCommand):
    help = "Seed exercise database"

    def handle(self, *args, **kwargs):
        created = 0
        updated = 0

        for name, muscle_group, equipment, movement_pattern, difficulty, is_compound in EXERCISES:
            exercise, was_created = Exercise.objects.update_or_create(
                name=name,
                defaults={
                    "muscle_group": muscle_group,
                    "equipment": equipment,
                    "movement_pattern": movement_pattern,
                    "difficulty": difficulty,
                    "is_compound": is_compound,
                },
            )

            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Exercises seeded successfully. Created: {created}, Updated: {updated}"
            )
        )