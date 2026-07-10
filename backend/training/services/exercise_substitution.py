# =============================================================================
# exercise_substitution.py
# -----------------------------------------------------------------------------
# Serviço que encontra substituições de exercício.
# É usado quando o atleta troca um exercício dentro do treino por outro compatível.
# Considera grupo muscular, equipamento e estrutura do programa para manter o plano coerente.
# =============================================================================
from exercises.models import Exercise
from exercises.serializers import ExerciseSerializer
from training.models import TrainingWorkoutExercise


def get_substitution_options(training_exercise):
    current_exercise = training_exercise.exercise
    alternatives = Exercise.objects.filter(
        muscle_group=current_exercise.muscle_group,
    ).exclude(
        id=current_exercise.id,
    ).order_by(
        "name",
    )

    return ExerciseSerializer(alternatives, many=True).data


def replace_training_exercise(training_exercise, replacement_exercise_id):
    current_exercise = training_exercise.exercise
    replacement = Exercise.objects.get(id=replacement_exercise_id)

    if replacement.muscle_group != current_exercise.muscle_group:
        raise ValueError("Replacement exercise must use the same muscle group")

    training_exercise.exercise = replacement
    training_exercise.save(update_fields=["exercise"])

    return TrainingWorkoutExercise.objects.select_related("exercise").get(id=training_exercise.id)
