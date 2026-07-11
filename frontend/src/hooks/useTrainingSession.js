// =============================================================================
// useTrainingSession.js
// -----------------------------------------------------------------------------
// Hook responsável pelo estado e ações da sessão de treino ativa.
// É usado pelo App.jsx para iniciar/terminar workouts, controlar o treino aberto,
// guardar notas da sessão e refrescar painéis globais após mudanças.
// Mantém a lógica de sessão separada da renderização da interface.
// =============================================================================
import { useState } from "react";
import * as trainingApi from "../api/trainingApi";

export default function useTrainingSession({
  profileId,
  loadProgramPanels,
  loadExerciseHistory,
  resetTrainingState,
  setLatestWorkoutProgression,
  setLatestAiCoach,
  setOpenExerciseById,
  setRestTimers,
  setSetForms,
  setCompletedCalibrationByExerciseId,
  setRemovedSetByKey,
  setOpenSetTypeMenuBySet,
  notifyError = () => {},
  notifySuccess = () => {},
}) {
  const [activeSessionByWorkout, setActiveSessionByWorkout] = useState({});
  const [sessionNotes, setSessionNotes] = useState({});
  const [openWorkoutId, setOpenWorkoutId] = useState(null);
  const [workoutStatusMessage, setWorkoutStatusMessage] = useState("");

  function getActiveWorkoutId() {
    return Object.keys(activeSessionByWorkout).find((workoutId) =>
      Boolean(activeSessionByWorkout[workoutId])
    );
  }

  function toggleWorkout(workoutId) {
    if (getActiveWorkoutId()) {
      return;
    }

    setOpenWorkoutId(openWorkoutId === workoutId ? null : workoutId);
  }

  async function startWorkoutSession(workout) {
    let data;

    try {
      data = await trainingApi.startWorkoutSession({
        profile_id: profileId,
        workout_id: workout.id,
      });
    } catch (error) {
      console.error(error.data || error);
      notifyError("Erro ao iniciar treino.");
      return;
    }

    setActiveSessionByWorkout({
      ...activeSessionByWorkout,
      [workout.id]: data.id,
    });
    setOpenWorkoutId(workout.id);
    setLatestWorkoutProgression(null);
    setLatestAiCoach(null);
    setWorkoutStatusMessage("");
    resetTrainingState();
    setSetForms({});
    setOpenSetTypeMenuBySet({});
    loadProgramPanels();

    workout.exercises.forEach((exercise) => {
      loadExerciseHistory(exercise, data.id);
    });
  }

  async function finishWorkoutSession(workout) {
    const sessionId = activeSessionByWorkout[workout.id];

    if (!sessionId) {
      notifyError("Não existe sessão ativa para este treino.");
      return;
    }

    let data;

    try {
      data = await trainingApi.finishWorkoutSession({
        session_id: sessionId,
        notes: sessionNotes[workout.id] || "",
      });
    } catch (error) {
      console.error(error.data || error);
      notifyError("Erro ao terminar treino.");
      return;
    }

    setActiveSessionByWorkout({
      ...activeSessionByWorkout,
      [workout.id]: null,
    });
    setOpenWorkoutId(null);
    setOpenExerciseById({});
    setRestTimers({});
    setSetForms({});
    setCompletedCalibrationByExerciseId({});
    setRemovedSetByKey({});
    setOpenSetTypeMenuBySet({});
    setLatestWorkoutProgression(data.next_workout_progression || null);
    setLatestAiCoach(data.ai_coach_summary || null);
    setWorkoutStatusMessage(`Treino terminado: ${data.workout_name}`);
    notifySuccess(`Treino terminado: ${data.workout_name}`);
    loadProgramPanels();
  }

  return {
    activeSessionByWorkout,
    setActiveSessionByWorkout,
    sessionNotes,
    setSessionNotes,
    openWorkoutId,
    setOpenWorkoutId,
    workoutStatusMessage,
    setWorkoutStatusMessage,
    getActiveWorkoutId,
    toggleWorkout,
    startWorkoutSession,
    finishWorkoutSession,
  };
}
