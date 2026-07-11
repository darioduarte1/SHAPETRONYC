// =============================================================================
// useSetLogging.js
// -----------------------------------------------------------------------------
// Hook responsável por guardar e desfazer séries concluídas.
// É usado pelo App.jsx para criar logs no backend, pedir a próxima recomendação
// ao motor da IA e limpar séries seguintes quando o atleta corrige um erro.
// Mantém a lógica de persistência e recálculo afastada da renderização principal.
// =============================================================================
import * as progressionApi from "../api/progressionApi";
import * as recommendationsApi from "../api/recommendationsApi";
import {
  EFFORT_OPTIONS,
  TARGET_REPS,
  WARMUP_EFFORT,
} from "../utils/trainingConstants";

function serializeSetForCoach(setLog) {
  const setType = setLog.set_type || "WORKING";

  return {
    workout_session: setLog.workout_session,
    session_id: setLog.workout_session,
    set_number: Number(setLog.set_number),
    set_type: setType,
    weight_used: Number(setLog.weight_used),
    reps_completed: Number(setLog.reps_completed),
    rir: setType === "WARMUP" ? null : setLog.rir,
    reached_failure: setType === "WARMUP" ? false : Boolean(setLog.reached_failure),
    notes: setLog.notes || "",
    created_at: setLog.created_at,
  };
}

export default function useSetLogging({
  userId,
  profileId,
  setForms,
  sessionNotes,
  activeSessionByWorkout,
  exerciseLogsById,
  recommendations,
  restTimers,
  setExerciseLogsById,
  setExerciseRowCounts,
  setRecommendations,
  setRestTimers,
  setSetForms,
  setOpenCompletionMenuBySet,
  setOpenRestMenuBySet,
  setOpenSetTypeMenuBySet,
  getExerciseLogs,
  getExerciseRows,
  getExerciseRowCount,
  getSetFormKey,
  getPreviousSetForExerciseRow,
  getSetTypeForExerciseRow,
  getPlannedValuesForExerciseRow,
  getRestSecondsForRow,
  shouldForceFailureEffort,
  getRepsInputValue,
  buildUserCoachContext,
  buildExerciseCoachContext,
}) {
  async function saveSet(exercise, sourceSetNumber, displaySetNumber, effortOption) {
    const setFormKey = getSetFormKey(exercise.id, sourceSetNumber);
    const formData = setForms[setFormKey] || {};
    const sessionId = activeSessionByWorkout[exercise.workout];
    const rows = getExerciseRows(exercise);
    const previousSet = getPreviousSetForExerciseRow(exercise, rows, sourceSetNumber, displaySetNumber);
    const setType = getSetTypeForExerciseRow(exercise, sourceSetNumber, displaySetNumber);
    const plannedValues = getPlannedValuesForExerciseRow(exercise, rows, sourceSetNumber, displaySetNumber);
    const weightUsed = formData.weight_used ?? plannedValues.weight;
    const repsCompleted = formData.reps_completed ?? plannedValues.reps;
    const selectedEffortOption = setType === "WARMUP"
      ? WARMUP_EFFORT
      : shouldForceFailureEffort(setType, repsCompleted)
        ? EFFORT_OPTIONS[0]
        : effortOption || EFFORT_OPTIONS[2];
    const setRir = setType === "WARMUP" || selectedEffortOption.reachedFailure
      ? null
      : selectedEffortOption.rir;
    const reachedFailure = setType === "WARMUP" ? false : selectedEffortOption.reachedFailure;
    const restSeconds = getRestSecondsForRow(setFormKey);

    if (!sessionId) {
      alert("Primeiro tens de iniciar o treino com Start Workout.");
      return;
    }

    if (weightUsed === "" || repsCompleted === "") {
      alert("Preenche o peso e as reps antes de confirmar a série.");
      return;
    }

    let data;

    try {
      data = await progressionApi.createSetLog({
        user: userId,
        workout_session: sessionId,
        training_exercise: exercise.id,
        exercise: exercise.exercise,
        set_number: displaySetNumber,
        set_type: setType,
        planned_weight: previousSet?.weight_used ?? null,
        weight_used: Number(weightUsed),
        target_min_reps: exercise.target_min_reps || TARGET_REPS,
        target_max_reps: exercise.target_max_reps || TARGET_REPS,
        reps_completed: Number(repsCompleted),
        rir: setRir,
        reached_failure: reachedFailure,
        notes: formData.notes || "",
      });
    } catch (error) {
      console.error(error.data || error);
      alert("Erro ao guardar a série. Vê a consola.");
      return;
    }

    setExerciseLogsById((currentLogs) => {
      const currentExerciseLogs = currentLogs[exercise.id] || {
        previous_sets: [],
        current_sets: [],
        history_sets: [],
        previous_session: null,
        recommended_sets: [],
      };
      const otherCurrentSets = currentExerciseLogs.current_sets.filter(
        (setLog) => Number(setLog.set_number) !== displaySetNumber
      );

      return {
        ...currentLogs,
        [exercise.id]: {
          ...currentExerciseLogs,
          current_sets: [...otherCurrentSets, data].sort(
            (firstSet, secondSet) => Number(firstSet.set_number) - Number(secondSet.set_number)
          ),
        },
      };
    });

    setRestTimers({
      ...restTimers,
      [exercise.id]: restSeconds,
    });

    setOpenCompletionMenuBySet((currentMenus) => ({
      ...currentMenus,
      [setFormKey]: false,
    }));

    setOpenRestMenuBySet((currentMenus) => ({
      ...currentMenus,
      [setFormKey]: false,
    }));

    setOpenSetTypeMenuBySet((currentMenus) => ({
      ...currentMenus,
      [setFormKey]: false,
    }));

    const currentExerciseLogs = getExerciseLogs(exercise.id);
    const completedSetsForCoach = [
      ...currentExerciseLogs.current_sets.filter(
        (setLog) => Number(setLog.set_number) !== displaySetNumber
      ),
      data,
    ].sort((firstSet, secondSet) => Number(firstSet.set_number) - Number(secondSet.set_number));

    try {
      const recommendationData = await recommendationsApi.getNextSetRecommendation({
        weight: Number(weightUsed),
        reps: Number(repsCompleted),
        rir: setRir,
        is_failure: reachedFailure,
        notes: formData.notes || "",
        set_type: setType,
        set_number: displaySetNumber,
        total_sets: exercise.sets,
        profile_id: profileId,
        training_exercise_id: exercise.id,
        workout_session_id: sessionId,
        target_min_reps: exercise.target_min_reps || TARGET_REPS,
        target_max_reps: exercise.target_max_reps || TARGET_REPS,
        target_rir: exercise.target_rir || 2,
        user_context: buildUserCoachContext(),
        exercise_context: buildExerciseCoachContext(exercise),
        session_context: {
          workout_id: exercise.workout,
          session_id: sessionId,
          current_set_number: displaySetNumber,
          sets_completed_in_current_exercise: completedSetsForCoach.length,
          total_sets_completed_in_session: Object.values(exerciseLogsById).reduce(
            (totalSets, exerciseLogs) => totalSets + (exerciseLogs.current_sets?.length || 0),
            0
          ) + 1,
          session_notes: sessionNotes[exercise.workout] || "",
          current_exercise_notes: formData.notes || "",
        },
        current_sets: completedSetsForCoach.map(serializeSetForCoach),
        previous_sets: currentExerciseLogs.previous_sets.map(serializeSetForCoach),
        history_sets: currentExerciseLogs.history_sets.map(serializeSetForCoach),
      });

      setRecommendations({
        ...recommendations,
        [exercise.id]: recommendationData,
      });

      if (recommendationData.exercise_status !== "complete") {
        const nextSourceSetNumber = sourceSetNumber + 1;
        const nextSetFormKey = getSetFormKey(exercise.id, nextSourceSetNumber);
        const nextDisplaySetNumber = displaySetNumber + 1;
        const nextPlannedValues = getPlannedValuesForExerciseRow(
          exercise,
          rows,
          nextSourceSetNumber,
          nextDisplaySetNumber
        );

        if (recommendationData.next_set_type && recommendationData.next_set_type !== "COMPLETE") {
          setSetForms((currentSetForms) => {
            const existingNextWeight = currentSetForms[nextSetFormKey]?.weight_used;
            const existingNextReps = currentSetForms[nextSetFormKey]?.reps_completed;
            const nextWeightValue =
              existingNextWeight !== undefined && existingNextWeight !== ""
                ? existingNextWeight
                : nextPlannedValues.weight !== undefined && nextPlannedValues.weight !== ""
                  ? nextPlannedValues.weight
                  : recommendationData.recommended_weight === ""
                    ? existingNextWeight
                    : recommendationData.recommended_weight;
            const nextRepsValue =
              existingNextReps !== undefined && existingNextReps !== ""
                ? existingNextReps
                : nextPlannedValues.reps !== undefined && nextPlannedValues.reps !== ""
                  ? nextPlannedValues.reps
                  : recommendationData.target_reps === ""
                    ? existingNextReps
                    : getRepsInputValue(
                        recommendationData.target_reps,
                        exercise.target_max_reps || TARGET_REPS
                      );

            return {
              ...currentSetForms,
              [nextSetFormKey]: {
                ...currentSetForms[nextSetFormKey],
                set_type: recommendationData.next_set_type,
                set_type_source: "coach",
                weight_used: nextWeightValue,
                reps_completed: nextRepsValue,
              },
            };
          });
        }

        setExerciseRowCounts((currentCounts) => ({
          ...currentCounts,
          [exercise.id]: Math.max(
            currentCounts[exercise.id] || 0,
            getExerciseRowCount(exercise),
            nextSourceSetNumber
          ),
        }));
      }
    } catch (error) {
      console.error(error.data || error);
    }
  }

  async function undoSet(exercise, sourceSetNumber, displaySetNumber) {
    const rows = getExerciseRows(exercise);
    const currentExerciseLogs = getExerciseLogs(exercise.id);
    const currentSet = currentExerciseLogs.current_sets.find(
      (setLog) => Number(setLog.set_number) === displaySetNumber
    );
    const onlyUndoCurrentSet = currentSet?.set_type === "WARMUP";
    const setLogsToRemove = currentExerciseLogs.current_sets.filter(
      (setLog) => onlyUndoCurrentSet
        ? Number(setLog.set_number) === displaySetNumber
        : Number(setLog.set_number) >= displaySetNumber
    );

    if (!setLogsToRemove.length) {
      return;
    }

    try {
      await Promise.all(setLogsToRemove.map((setLog) => progressionApi.deleteSetLog(setLog.id)));
    } catch (error) {
      console.error(error.data || error);
      alert("Não consegui desfazer a série. Tenta novamente.");
      return;
    }

    setExerciseLogsById((currentLogs) => {
      const logsForExercise = currentLogs[exercise.id] || currentExerciseLogs;

      return {
        ...currentLogs,
        [exercise.id]: {
          ...logsForExercise,
          current_sets: logsForExercise.current_sets.filter(
            (setLog) => onlyUndoCurrentSet
              ? Number(setLog.set_number) !== displaySetNumber
              : Number(setLog.set_number) < displaySetNumber
          ),
        },
      };
    });

    setSetForms((currentSetForms) => {
      const nextSetForms = { ...currentSetForms };

      rows.forEach((row) => {
        if (
          onlyUndoCurrentSet
            ? row.displaySetNumber === displaySetNumber
            : row.displaySetNumber >= displaySetNumber
        ) {
          delete nextSetForms[getSetFormKey(exercise.id, row.sourceSetNumber)];
        }
      });

      if (currentSet) {
        nextSetForms[getSetFormKey(exercise.id, sourceSetNumber)] = {
          weight_used: currentSet.weight_used,
          reps_completed: currentSet.reps_completed,
          notes: currentSet.notes || "",
          set_type: currentSet.set_type,
          set_type_source: "manual",
        };
      }

      return nextSetForms;
    });

    if (!onlyUndoCurrentSet) {
      setRecommendations((currentRecommendations) => {
        const nextRecommendations = { ...currentRecommendations };
        delete nextRecommendations[exercise.id];
        return nextRecommendations;
      });
    }

    setRestTimers((currentTimers) => ({
      ...currentTimers,
      [exercise.id]: 0,
    }));

    setOpenCompletionMenuBySet((currentMenus) => {
      const nextMenus = { ...currentMenus };

      rows.forEach((row) => {
        if (
          onlyUndoCurrentSet
            ? row.displaySetNumber === displaySetNumber
            : row.displaySetNumber >= displaySetNumber
        ) {
          delete nextMenus[getSetFormKey(exercise.id, row.sourceSetNumber)];
        }
      });

      return nextMenus;
    });

    setOpenRestMenuBySet((currentMenus) => {
      const nextMenus = { ...currentMenus };

      rows.forEach((row) => {
        if (
          onlyUndoCurrentSet
            ? row.displaySetNumber === displaySetNumber
            : row.displaySetNumber >= displaySetNumber
        ) {
          delete nextMenus[getSetFormKey(exercise.id, row.sourceSetNumber)];
        }
      });

      return nextMenus;
    });

    setOpenSetTypeMenuBySet((currentMenus) => {
      const nextMenus = { ...currentMenus };

      rows.forEach((row) => {
        if (
          onlyUndoCurrentSet
            ? row.displaySetNumber === displaySetNumber
            : row.displaySetNumber >= displaySetNumber
        ) {
          delete nextMenus[getSetFormKey(exercise.id, row.sourceSetNumber)];
        }
      });

      return nextMenus;
    });
  }

  return {
    saveSet,
    undoSet,
  };
}
