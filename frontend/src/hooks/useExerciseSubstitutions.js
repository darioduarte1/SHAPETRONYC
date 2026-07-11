// =============================================================================
// useExerciseSubstitutions.js
// -----------------------------------------------------------------------------
// Hook responsável pela troca de exercícios no frontend.
// É usado pelo App.jsx para carregar alternativas, abrir/fechar o painel de
// substituição e substituir o exercício no programa ativo.
// Também limpa estado antigo do exercício trocado para evitar dados misturados.
// =============================================================================
import { useState } from "react";
import * as trainingApi from "../api/trainingApi";

export default function useExerciseSubstitutions({
  setProgram,
  setRecommendations,
  setExerciseLogsById,
  setOpenExerciseById,
  loadProgramPanels,
}) {
  const [substitutionOptionsByExerciseId, setSubstitutionOptionsByExerciseId] = useState({});
  const [openSubstitutionByExerciseId, setOpenSubstitutionByExerciseId] = useState({});
  const [isReplacingExerciseById, setIsReplacingExerciseById] = useState({});

  async function loadExerciseSubstitutions(exercise) {
    if (substitutionOptionsByExerciseId[exercise.id]) {
      return substitutionOptionsByExerciseId[exercise.id];
    }

    try {
      const data = await trainingApi.getExerciseSubstitutions(exercise.id);

      setSubstitutionOptionsByExerciseId((currentOptions) => ({
        ...currentOptions,
        [exercise.id]: data,
      }));

      return data;
    } catch (error) {
      console.error(error.data || error);
      alert("Não consegui carregar alternativas para este exercício.");
      return null;
    }
  }

  async function toggleExerciseSubstitutions(exercise) {
    const shouldOpen = !openSubstitutionByExerciseId[exercise.id];

    setOpenSubstitutionByExerciseId((currentState) => ({
      ...currentState,
      [exercise.id]: shouldOpen,
    }));

    if (shouldOpen) {
      await loadExerciseSubstitutions(exercise);
    }
  }

  async function replaceExercise(exercise, replacementExerciseId) {
    setIsReplacingExerciseById((currentState) => ({
      ...currentState,
      [exercise.id]: true,
    }));

    try {
      const data = await trainingApi.replaceTrainingExercise({
        training_exercise_id: exercise.id,
        replacement_exercise_id: replacementExerciseId,
      });

      setProgram(data);
      setRecommendations((currentRecommendations) => {
        const nextRecommendations = { ...currentRecommendations };
        delete nextRecommendations[exercise.id];
        return nextRecommendations;
      });
      setExerciseLogsById((currentLogs) => {
        const nextLogs = { ...currentLogs };
        delete nextLogs[exercise.id];
        return nextLogs;
      });
      setSubstitutionOptionsByExerciseId((currentOptions) => {
        const nextOptions = { ...currentOptions };
        delete nextOptions[exercise.id];
        return nextOptions;
      });
      setOpenSubstitutionByExerciseId((currentState) => ({
        ...currentState,
        [exercise.id]: false,
      }));
      setOpenExerciseById((currentState) => ({
        ...currentState,
        [exercise.id]: false,
      }));
      await loadProgramPanels();
    } catch (error) {
      console.error(error);
      alert("Não consegui contactar o servidor para trocar o exercício.");
    } finally {
      setIsReplacingExerciseById((currentState) => ({
        ...currentState,
        [exercise.id]: false,
      }));
    }
  }

  return {
    substitutionOptionsByExerciseId,
    setSubstitutionOptionsByExerciseId,
    openSubstitutionByExerciseId,
    setOpenSubstitutionByExerciseId,
    isReplacingExerciseById,
    setIsReplacingExerciseById,
    loadExerciseSubstitutions,
    toggleExerciseSubstitutions,
    replaceExercise,
  };
}
