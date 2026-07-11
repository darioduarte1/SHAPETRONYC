// =============================================================================
// useExerciseHistory.js
// -----------------------------------------------------------------------------
// Hook responsável pelo histórico e logs atuais de cada exercício.
// É usado pelo App.jsx para carregar séries anteriores, séries da sessão atual,
// recomendações planeadas e calibração associada a um exercício aberto.
// Também mantém a quantidade de linhas visíveis na tabela de séries.
// =============================================================================
import { useState } from "react";
import * as progressionApi from "../api/progressionApi";

export default function useExerciseHistory({ profileId, getActiveSessionByWorkout }) {
  const [exerciseLogsById, setExerciseLogsById] = useState({});
  const [exerciseRowCounts, setExerciseRowCounts] = useState({});

  function getExerciseLogs(trainingExerciseId) {
    return exerciseLogsById[trainingExerciseId] || {
      previous_sets: [],
      current_sets: [],
      history_sets: [],
      previous_session: null,
      recommended_sets: [],
      calibration: null,
    };
  }

  async function loadExerciseHistory(exercise, sessionIdOverride = null) {
    const activeSessionByWorkout = getActiveSessionByWorkout();
    const sessionId = sessionIdOverride || activeSessionByWorkout[exercise.workout];

    if (!profileId || !sessionId) {
      return null;
    }

    const params = new URLSearchParams({
      profile_id: profileId,
      exercise_id: exercise.exercise,
      training_exercise_id: exercise.id,
      session_id: sessionId,
    });

    try {
      const data = await progressionApi.getExerciseHistory(params);

      setExerciseLogsById((currentLogs) => ({
        ...currentLogs,
        [exercise.id]: data,
      }));

      setExerciseRowCounts((currentCounts) => ({
        ...currentCounts,
        [exercise.id]: Math.max(
          currentCounts[exercise.id] || 0,
          exercise.sets + 1,
          data.previous_sets.length,
          data.current_sets.length,
          data.recommended_sets.length,
          1
        ),
      }));

      return data;
    } catch (error) {
      console.error(error.data || error);
      return null;
    }
  }

  return {
    exerciseLogsById,
    setExerciseLogsById,
    exerciseRowCounts,
    setExerciseRowCounts,
    getExerciseLogs,
    loadExerciseHistory,
  };
}
