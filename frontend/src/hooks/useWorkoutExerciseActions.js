// =============================================================================
// useWorkoutExerciseActions.js
// -----------------------------------------------------------------------------
// Hook responsável por ações simples do treino e dos exercícios abertos.
// É usado pelo App.jsx para abrir exercícios, calcular estatísticas da sessão,
// adicionar/remover linhas manuais e escolher a imagem apresentada.
// Mantém pequenas ações de interface fora do componente principal.
// =============================================================================

export default function useWorkoutExerciseActions({
  openExerciseById,
  setOpenExerciseById,
  exerciseRowCounts,
  setExerciseRowCounts,
  removedSetByKey,
  setRemovedSetByKey,
  openRestMenuBySet,
  setOpenRestMenuBySet,
  openCompletionMenuBySet,
  setOpenCompletionMenuBySet,
  openSetTypeMenuBySet,
  setOpenSetTypeMenuBySet,
  setSetForms,
  getExerciseLogs,
  loadExerciseHistory,
  getExerciseRowCount,
  getCurrentSetForRow,
  getSetFormKey,
}) {
  function getWorkoutSessionStats(workout) {
    const workoutExercises = workout.exercises || [];
    const currentSets = workoutExercises.flatMap(
      (exercise) => getExerciseLogs(exercise.id).current_sets
    );
    const volume = currentSets.reduce(
      (total, setLog) => total + Number(setLog.weight_used) * Number(setLog.reps_completed),
      0
    );

    return {
      sets: currentSets.length,
      volume,
    };
  }

  async function toggleExercise(exercise) {
    const isOpening = !openExerciseById[exercise.id];

    setOpenExerciseById({
      ...openExerciseById,
      [exercise.id]: isOpening,
    });

    if (isOpening) {
      await loadExerciseHistory(exercise);
    }
  }

  function getExerciseImageUrl(exercise) {
    return exercise.exercise_image_url || "/exercise-screens/IMG_3620.PNG";
  }

  function addExerciseRow(exercise) {
    setExerciseRowCounts({
      ...exerciseRowCounts,
      [exercise.id]: getExerciseRowCount(exercise) + 1,
    });
  }

  function removeExerciseRow(exercise, sourceSetNumber, displaySetNumber) {
    const setFormKey = getSetFormKey(exercise.id, sourceSetNumber);

    if (getCurrentSetForRow(exercise.id, displaySetNumber)) {
      return;
    }

    setRemovedSetByKey({
      ...removedSetByKey,
      [setFormKey]: true,
    });

    setSetForms((currentSetForms) => {
      const nextSetForms = { ...currentSetForms };
      delete nextSetForms[setFormKey];
      return nextSetForms;
    });

    setOpenRestMenuBySet({
      ...openRestMenuBySet,
      [setFormKey]: false,
    });

    setOpenCompletionMenuBySet({
      ...openCompletionMenuBySet,
      [setFormKey]: false,
    });

    setOpenSetTypeMenuBySet({
      ...openSetTypeMenuBySet,
      [setFormKey]: false,
    });
  }

  return {
    getWorkoutSessionStats,
    toggleExercise,
    getExerciseImageUrl,
    addExerciseRow,
    removeExerciseRow,
  };
}
