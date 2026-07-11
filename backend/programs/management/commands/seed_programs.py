# =============================================================================
# seed_programs.py
# -----------------------------------------------------------------------------
# Comando de gestão para criar programas base no sistema.
# É executado manualmente através do manage.py quando é necessário preparar templates ou exemplos de treino.
# Ajuda a iniciar a app com estruturas de programa reutilizáveis.
# =============================================================================
from django.core.management.base import BaseCommand

from exercises.models import Exercise
from programs.models import ProgramTemplate, WorkoutTemplate, WorkoutExerciseTemplate


class Command(BaseCommand):
    help = "Seed initial training programs"

    def handle(self, *args, **kwargs):
        chest_press, _ = Exercise.objects.get_or_create(
            name="Chest Press Machine",
            defaults={"muscle_group": "Chest", "equipment": "Machine"},
        )

        incline_press, _ = Exercise.objects.get_or_create(
            name="Incline Chest Press",
            defaults={"muscle_group": "Chest", "equipment": "Machine"},
        )

        shoulder_press, _ = Exercise.objects.get_or_create(
            name="Shoulder Press",
            defaults={"muscle_group": "Shoulders", "equipment": "Machine"},
        )

        program, _ = ProgramTemplate.objects.get_or_create(
            name="Hypertrophy Intermediate 5 Days",
            defaults={
                "goal": "HYPERTROPHY",
                "level": "INTERMEDIATE",
                "days_per_week": 5,
            },
        )

        push, _ = WorkoutTemplate.objects.get_or_create(
            program=program,
            name="Push",
            defaults={"order": 1},
        )

        WorkoutExerciseTemplate.objects.get_or_create(
            workout=push,
            exercise=chest_press,
            defaults={
                "order": 1,
                "sets": 3,
                "target_min_reps": 10,
                "target_max_reps": 12,
                "target_rir": 2,
            },
        )

        WorkoutExerciseTemplate.objects.get_or_create(
            workout=push,
            exercise=incline_press,
            defaults={
                "order": 2,
                "sets": 3,
                "target_min_reps": 10,
                "target_max_reps": 12,
                "target_rir": 2,
            },
        )

        WorkoutExerciseTemplate.objects.get_or_create(
            workout=push,
            exercise=shoulder_press,
            defaults={
                "order": 3,
                "sets": 3,
                "target_min_reps": 8,
                "target_max_reps": 10,
                "target_rir": 2,
            },
        )

        self.stdout.write(
            self.style.SUCCESS("Initial hypertrophy program created successfully.")
        )