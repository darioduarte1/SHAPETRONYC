// =============================================================================
// useCoachContext.js
// -----------------------------------------------------------------------------
// Hook responsável por montar o contexto enviado ao motor de recomendação.
// É usado pelo App.jsx e pelo fluxo de gravação de séries para transformar dados
// do atleta e do exercício num formato consistente para o coach/IA.
// Mantém fora do componente principal a tradução entre estado da interface e API.
// =============================================================================

export default function useCoachContext({ userId, form }) {
  function buildUserCoachContext() {
    return {
      user_id: userId,
      goal: form.goal,
      level: form.level,
      training_experience: form.training_experience,
      days_per_week: Number(form.days_per_week),
      body_weight: Number(form.weight_kg),
      age: Number(form.age),
      gender: form.gender,
    };
  }

  function buildExerciseCoachContext(exercise) {
    return {
      exercise_id: exercise.exercise,
      exercise_name: exercise.exercise_name,
      muscle_group: exercise.exercise_muscle_group,
      movement_pattern: exercise.exercise_movement_pattern,
      is_compound: Boolean(exercise.exercise_is_compound),
      equipment: exercise.exercise_equipment,
      target_min_reps: exercise.target_min_reps,
      target_max_reps: exercise.target_max_reps,
      target_rir: exercise.target_rir,
      planned_sets: exercise.sets,
      main_weight_options: exercise.exercise_main_weight_options || [],
      micro_weight_options: exercise.exercise_micro_weight_options || [],
    };
  }

  return {
    buildUserCoachContext,
    buildExerciseCoachContext,
  };
}
