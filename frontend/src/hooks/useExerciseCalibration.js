// =============================================================================
// useExerciseCalibration.js
// -----------------------------------------------------------------------------
// Hook responsável pelo treino experimental de calibração por exercício.
// É usado pelo App.jsx para gerir formulário, cores de resultado, bloqueios,
// gravação da série experimental e atualização do estado calibrado.
// Mantém a lógica de calibração inicial separada do ecrã principal.
// =============================================================================
import { useState } from "react";
import * as trainingApi from "../api/trainingApi";
import { DEFAULT_REST_SECONDS } from "../utils/trainingConstants";

export default function useExerciseCalibration({
  profileId,
  restTimers,
  setRestTimers,
  getExerciseLogs,
  setExerciseLogsById,
  loadExerciseHistory,
}) {
  const [calibrationFormsByExerciseId, setCalibrationFormsByExerciseId] = useState({});
  const [isSavingCalibrationByExerciseId, setIsSavingCalibrationByExerciseId] = useState({});
  const [completedCalibrationByExerciseId, setCompletedCalibrationByExerciseId] = useState({});

  function getCalibrationState(exercise) {
    return getExerciseLogs(exercise.id).calibration || {
      needs_calibration: true,
      scale_configured: Boolean((exercise.exercise_main_weight_options || []).length),
      estimated_working_weight: null,
      confidence: "baixa",
      calibration_sets: [],
      next_step: null,
      reason: "baseline_required",
      message: "Este exercício ainda precisa de calibração.",
    };
  }

  function getCalibrationColorMeta(colorOrReps) {
    const value = String(colorOrReps || "").toLowerCase();
    const reps = Number(colorOrReps);

    if (value === "red" || (Number.isFinite(reps) && reps > 0 && reps <= 8)) {
      return {
        key: "red",
        label: "Vermelho",
        text: "falha antes das 8 reps",
        color: "#fecaca",
        background: "rgba(127, 29, 29, 0.28)",
        border: "rgba(248, 113, 113, 0.45)",
      };
    }

    if (value === "orange" || (Number.isFinite(reps) && reps >= 9 && reps <= 12)) {
      return {
        key: "orange",
        label: "Laranja",
        text: "entre 9 e 12 reps",
        color: "#fed7aa",
        background: "rgba(154, 52, 18, 0.26)",
        border: "rgba(251, 146, 60, 0.45)",
      };
    }

    if (value === "yellow" || (Number.isFinite(reps) && reps >= 13 && reps <= 14)) {
      return {
        key: "yellow",
        label: "Amarelo",
        text: "entre 13 e 14 reps",
        color: "#fef08a",
        background: "rgba(113, 63, 18, 0.24)",
        border: "rgba(250, 204, 21, 0.45)",
      };
    }

    if (value === "green" || (Number.isFinite(reps) && reps >= 15)) {
      return {
        key: "green",
        label: "Verde",
        text: "acima de 15 reps",
        color: "#bbf7d0",
        background: "rgba(20, 83, 45, 0.25)",
        border: "rgba(74, 222, 128, 0.45)",
      };
    }

    return null;
  }

  function getCalibrationColorOptions() {
    return [
      getCalibrationColorMeta("red"),
      getCalibrationColorMeta("orange"),
      getCalibrationColorMeta("yellow"),
      getCalibrationColorMeta("green"),
    ];
  }

  function getCalibrationColorReps(color) {
    const repsByColor = {
      red: 7,
      orange: 11,
      yellow: 14,
      green: 16,
    };

    return repsByColor[color] || "";
  }

  function getCalibrationForm(exercise) {
    const calibrationState = getCalibrationState(exercise);

    return calibrationFormsByExerciseId[exercise.id] || {
      weight_used: calibrationState.next_step?.recommended_weight || calibrationState.estimated_working_weight || "",
      result_color: "",
      rir: 0,
      notes: "",
    };
  }

  function updateCalibrationForm(exercise, field, value) {
    setCalibrationFormsByExerciseId((currentForms) => ({
      ...currentForms,
      [exercise.id]: {
        ...getCalibrationForm(exercise),
        [field]: value,
      },
    }));
  }

  async function saveExerciseCalibration(exercise) {
    const formData = getCalibrationForm(exercise);
    const calibrationState = getCalibrationState(exercise);
    const calibrationRestSeconds = restTimers[exercise.id] || 0;

    if (!calibrationState.scale_configured) {
      alert("Preenche primeiro a escala da máquina antes de guardar séries experimentais.");
      return;
    }

    if (calibrationRestSeconds > 0) {
      return;
    }

    if (!formData.weight_used || !formData.result_color) {
      alert("Preenche o peso e escolhe a cor da série experimental.");
      return;
    }

    setIsSavingCalibrationByExerciseId((currentState) => ({
      ...currentState,
      [exercise.id]: true,
    }));

    try {
      const data = await trainingApi.saveExerciseCalibration({
        profile_id: profileId,
        training_exercise_id: exercise.id,
        weight_used: Number(formData.weight_used),
        result_color: formData.result_color,
        reps_completed: getCalibrationColorReps(formData.result_color),
        rir: 0,
        reached_failure: true,
        notes: formData.notes || "",
      });

      setExerciseLogsById((currentLogs) => ({
        ...currentLogs,
        [exercise.id]: {
          ...getExerciseLogs(exercise.id),
          calibration: data,
        },
      }));
      setCalibrationFormsByExerciseId((currentForms) => ({
        ...currentForms,
        [exercise.id]: {
          weight_used: data.next_step?.recommended_weight || data.estimated_working_weight || formData.weight_used,
          result_color: "",
          rir: 0,
          notes: "",
        },
      }));
      setRestTimers((currentTimers) => ({
        ...currentTimers,
        [exercise.id]: data.next_step?.action === "calibration_complete" ? 0 : DEFAULT_REST_SECONDS,
      }));

      if (data.next_step?.action === "calibration_complete" || !data.needs_calibration) {
        setCompletedCalibrationByExerciseId((currentState) => ({
          ...currentState,
          [exercise.id]: true,
        }));
      }

      await loadExerciseHistory(exercise);
    } catch (error) {
      console.error(error);
      alert("Não consegui contactar o servidor para guardar a calibração.");
    } finally {
      setIsSavingCalibrationByExerciseId((currentState) => ({
        ...currentState,
        [exercise.id]: false,
      }));
    }
  }

  return {
    calibrationFormsByExerciseId,
    setCalibrationFormsByExerciseId,
    isSavingCalibrationByExerciseId,
    setIsSavingCalibrationByExerciseId,
    completedCalibrationByExerciseId,
    setCompletedCalibrationByExerciseId,
    getCalibrationState,
    getCalibrationColorMeta,
    getCalibrationColorOptions,
    getCalibrationForm,
    updateCalibrationForm,
    saveExerciseCalibration,
  };
}
