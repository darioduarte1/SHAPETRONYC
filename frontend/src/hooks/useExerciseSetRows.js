// =============================================================================
// useExerciseSetRows.js
// -----------------------------------------------------------------------------
// Hook responsável por calcular as linhas visíveis da tabela de séries.
// É usado pelo App.jsx, ExerciseCard e ExerciseSetTable para decidir que linhas
// existem, que tipo de série cada linha representa, que valores planeados devem
// aparecer e como formatar referências de treino anterior.
// Centraliza as regras de aquecimento, working sets, dropsets e esforço.
// =============================================================================
import {
  EFFORT_OPTIONS,
  SET_TYPES,
  TARGET_REPS,
} from "../utils/trainingConstants";

export default function useExerciseSetRows({
  exerciseRowCounts,
  setForms,
  removedSetByKey,
  getExerciseLogs,
}) {
  function getSetFormKey(trainingExerciseId, setNumber) {
    return `${trainingExerciseId}-${setNumber}`;
  }

  function getSetTypeMeta(setType) {
    return SET_TYPES.find((type) => type.value === setType) || SET_TYPES[1];
  }

  function getEffortMetaFromSet(setLog) {
    if (!setLog || setLog.set_type === "WARMUP") {
      return null;
    }

    if (setLog.reached_failure) {
      return EFFORT_OPTIONS[0];
    }

    if (setLog.rir === null || setLog.rir === undefined) {
      return null;
    }

    if (setLog.rir <= 1) {
      return EFFORT_OPTIONS[1];
    }

    if (setLog.rir <= 3) {
      return EFFORT_OPTIONS[2];
    }

    return EFFORT_OPTIONS[3];
  }

  function getCurrentSetForRow(trainingExerciseId, setNumber) {
    return getExerciseLogs(trainingExerciseId).current_sets.find(
      (setLog) => Number(setLog.set_number) === setNumber
    );
  }

  function normalizeSetType(setType) {
    return setType || "WORKING";
  }

  function getPreviousSetByTypePosition(trainingExerciseId, setType, typePosition) {
    return getExerciseLogs(trainingExerciseId).previous_sets.filter(
      (setLog) => normalizeSetType(setLog.set_type) === setType
    )[typePosition - 1] || null;
  }

  function getPreviousSetAtDisplayPosition(trainingExerciseId, displaySetNumber) {
    return getExerciseLogs(trainingExerciseId).previous_sets.find(
      (setLog) => Number(setLog.set_number) === displaySetNumber
    ) || null;
  }

  function getRecommendedSetRecordForRow(trainingExerciseId, setNumber, setType = null) {
    return getExerciseLogs(trainingExerciseId).recommended_sets.find(
      (setRecommendation) =>
        Number(setRecommendation.set_number) === setNumber &&
        (!setType || setRecommendation.set_type === setType)
    );
  }

  function getRecommendedSetForRow(trainingExerciseId, setNumber, setType = null) {
    const recommendedSet = getRecommendedSetRecordForRow(trainingExerciseId, setNumber, setType);

    return {
      weight: recommendedSet?.recommended_weight ?? "",
      reps: recommendedSet?.recommended_reps ?? "",
      reason: recommendedSet?.reason ?? "",
      source: recommendedSet?.source ?? "",
      confidence: recommendedSet?.confidence ?? "",
      decisionBasis: recommendedSet?.decision_basis ?? [],
    };
  }

  function getExerciseRowCount(exercise) {
    const logs = getExerciseLogs(exercise.id);
    const recommendedWarmupCount = logs.recommended_sets.filter(
      (setRecommendation) => setRecommendation.set_type === "WARMUP"
    ).length;
    const plannedRows = exercise.sets + Math.max(1, recommendedWarmupCount);

    return Math.max(
      exerciseRowCounts[exercise.id] || 0,
      plannedRows,
      logs.previous_sets.length,
      logs.current_sets.length,
      logs.recommended_sets.length,
      1
    );
  }

  function getExerciseRows(exercise) {
    const rowCount = getExerciseRowCount(exercise);
    const visibleSourceRows = Array.from({ length: rowCount }, (_, index) => index + 1).filter((sourceSetNumber) => {
      const setFormKey = getSetFormKey(exercise.id, sourceSetNumber);

      return !removedSetByKey[setFormKey];
    });

    return visibleSourceRows.map((sourceSetNumber, index) => ({
      sourceSetNumber,
      displaySetNumber: index + 1,
    }));
  }

  function getSetTypeForExerciseRow(exercise, sourceSetNumber, displaySetNumber) {
    const setFormKey = getSetFormKey(exercise.id, sourceSetNumber);
    const rowForm = setForms[setFormKey] || {};
    const currentSet = getCurrentSetForRow(exercise.id, displaySetNumber);
    const previousSetAtPosition = getPreviousSetAtDisplayPosition(exercise.id, displaySetNumber);
    const recommendedSet = getRecommendedSetRecordForRow(exercise.id, sourceSetNumber);
    const hasCurrentSets = getExerciseLogs(exercise.id).current_sets.length > 0;

    if (!currentSet && !rowForm.set_type && !hasCurrentSets && sourceSetNumber === 1) {
      return "WARMUP";
    }

    return (
      currentSet?.set_type ||
      (rowForm.set_type_source === "manual" ? rowForm.set_type : null) ||
      previousSetAtPosition?.set_type ||
      recommendedSet?.set_type ||
      rowForm.set_type ||
      "WORKING"
    );
  }

  function getSetTypePositionForExerciseRow(exercise, rows, sourceSetNumber, displaySetNumber) {
    const rowSetType = getSetTypeForExerciseRow(exercise, sourceSetNumber, displaySetNumber);
    const currentRowIndex = rows.findIndex((row) => row.sourceSetNumber === sourceSetNumber);

    return rows.slice(0, currentRowIndex + 1).filter(
      (row) => getSetTypeForExerciseRow(exercise, row.sourceSetNumber, row.displaySetNumber) === rowSetType
    ).length;
  }

  function getPreviousSetForExerciseRow(exercise, rows, sourceSetNumber, displaySetNumber) {
    const rowSetType = getSetTypeForExerciseRow(exercise, sourceSetNumber, displaySetNumber);
    const typePosition = getSetTypePositionForExerciseRow(exercise, rows, sourceSetNumber, displaySetNumber);

    return getPreviousSetByTypePosition(exercise.id, rowSetType, typePosition);
  }

  function getWarmupReferenceSet(exercise, rows, sourceSetNumber, displaySetNumber) {
    const typePosition = getSetTypePositionForExerciseRow(exercise, rows, sourceSetNumber, displaySetNumber);

    return getPreviousSetByTypePosition(exercise.id, "WARMUP", typePosition);
  }

  function getVisibleSetLabel(exercise, rows, sourceSetNumber, displaySetNumber) {
    const rowSetType = getSetTypeForExerciseRow(exercise, sourceSetNumber, displaySetNumber);
    const sameTypeRows = rows.filter((row) =>
      getSetTypeForExerciseRow(exercise, row.sourceSetNumber, row.displaySetNumber) === rowSetType
    );
    const sameTypeIndex = sameTypeRows.findIndex((row) => row.sourceSetNumber === sourceSetNumber) + 1;

    if (rowSetType === "WARMUP") {
      return sameTypeRows.length > 1 ? `W${sameTypeIndex}` : "W";
    }

    if (rowSetType === "DROP") {
      return sameTypeRows.length > 1 ? `D${sameTypeIndex}` : "D";
    }

    return String(sameTypeIndex);
  }

  function getPlannedValuesForExerciseRow(exercise, rows, sourceSetNumber, displaySetNumber) {
    const rowSetType = getSetTypeForExerciseRow(exercise, sourceSetNumber, displaySetNumber);

    if (rowSetType === "WARMUP") {
      const warmupReferenceSet = getWarmupReferenceSet(exercise, rows, sourceSetNumber, displaySetNumber);
      const recommendedWarmup = getRecommendedSetForRow(exercise.id, sourceSetNumber, "WARMUP");

      return {
        weight: recommendedWarmup.weight || warmupReferenceSet?.weight_used || "",
        reps: recommendedWarmup.reps || warmupReferenceSet?.reps_completed || "",
        reason: recommendedWarmup.reason,
        source: recommendedWarmup.source,
        confidence: recommendedWarmup.confidence,
        decisionBasis: recommendedWarmup.decisionBasis,
      };
    }

    return getRecommendedSetForRow(exercise.id, sourceSetNumber, "WORKING");
  }

  function shouldForceFailureEffort(setType, repsCompleted) {
    return setType === "WORKING" && Number(repsCompleted) < TARGET_REPS;
  }

  function getEffortOptionsForSet(setType, repsCompleted) {
    if (setType === "WARMUP") {
      return [];
    }

    return shouldForceFailureEffort(setType, repsCompleted) ? [EFFORT_OPTIONS[0]] : EFFORT_OPTIONS;
  }

  function formatPreviousSet(setLog) {
    if (!setLog) {
      return "-";
    }

    const effortMeta = getEffortMetaFromSet(setLog);
    const effortLabel = effortMeta ? ` ${effortMeta.label}` : "";

    return `${setLog.weight_used}kg x ${setLog.reps_completed}${effortLabel}`;
  }

  function getRepsInputValue(repsValue, fallbackReps) {
    if (typeof repsValue === "number") {
      return repsValue;
    }

    const match = String(repsValue || "").match(/\d+/g);

    if (!match?.length) {
      return fallbackReps;
    }

    return Number(match[match.length - 1]);
  }

  function getExerciseTargetLabel(exercise) {
    return `${exercise.target_max_reps || TARGET_REPS}`;
  }

  return {
    getSetFormKey,
    getSetTypeMeta,
    getEffortMetaFromSet,
    getCurrentSetForRow,
    getPreviousSetForExerciseRow,
    getRecommendedSetForRow,
    getExerciseRowCount,
    getExerciseRows,
    getSetTypeForExerciseRow,
    getWarmupReferenceSet,
    getVisibleSetLabel,
    getPlannedValuesForExerciseRow,
    shouldForceFailureEffort,
    getEffortOptionsForSet,
    formatPreviousSet,
    getRepsInputValue,
    getExerciseTargetLabel,
  };
}
