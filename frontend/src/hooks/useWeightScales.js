// =============================================================================
// useWeightScales.js
// -----------------------------------------------------------------------------
// Hook responsável pela escala de pesos de cada máquina/exercício.
// É usado pelo App.jsx para abrir o painel de escala, editar placas e bolachas,
// guardar a escala no backend e atualizar o programa com os pesos disponíveis.
// Garante que a lógica de pesos reais da máquina fica fora da UI principal.
// =============================================================================
import { useState } from "react";
import * as trainingApi from "../api/trainingApi";

export default function useWeightScales({
  profileId,
  activeSessionByWorkout,
  setProgram,
  loadExerciseHistory,
}) {
  const [openWeightScaleByExerciseId, setOpenWeightScaleByExerciseId] = useState({});
  const [weightScaleFormsByExerciseId, setWeightScaleFormsByExerciseId] = useState({});
  const [isSavingWeightScaleByExerciseId, setIsSavingWeightScaleByExerciseId] = useState({});

  function formatWeightOptions(options) {
    return (options || []).join(", ");
  }

  function parseWeightOptions(value) {
    return String(value || "")
      .split(",")
      .map((item) => item.trim().replace(",", "."))
      .filter(Boolean)
      .map(Number)
      .filter((item) => Number.isFinite(item) && item >= 0);
  }

  function buildMicroWeightRows(options) {
    if (!options?.length) {
      return [{ count: "", weight: "" }];
    }

    return options.map((option) => {
      if (typeof option === "number") {
        return {
          count: 1,
          weight: option,
        };
      }

      return {
        count: option.count ?? 1,
        weight: option.weight ?? "",
      };
    });
  }

  function serializeMicroWeightRows(rows) {
    return (rows || [])
      .map((row) => ({
        count: Number(row.count),
        weight: Number(String(row.weight || "").replace(",", ".")),
      }))
      .filter((row) =>
        Number.isFinite(row.count) &&
        Number.isFinite(row.weight) &&
        row.count > 0 &&
        row.weight > 0
      );
  }

  function buildWeightScaleForm(exercise) {
    return {
      main_weight_options: formatWeightOptions(exercise.exercise_main_weight_options),
      micro_weight_options: buildMicroWeightRows(exercise.exercise_micro_weight_options),
    };
  }

  function getWeightScaleForm(exercise) {
    return weightScaleFormsByExerciseId[exercise.id] || buildWeightScaleForm(exercise);
  }

  function toggleWeightScaleMenu(exercise) {
    const shouldOpen = !openWeightScaleByExerciseId[exercise.id];

    setOpenWeightScaleByExerciseId((currentState) => ({
      ...currentState,
      [exercise.id]: shouldOpen,
    }));

    if (shouldOpen && !weightScaleFormsByExerciseId[exercise.id]) {
      setWeightScaleFormsByExerciseId((currentForms) => ({
        ...currentForms,
        [exercise.id]: buildWeightScaleForm(exercise),
      }));
    }
  }

  function updateWeightScaleForm(exercise, field, value) {
    setWeightScaleFormsByExerciseId((currentForms) => ({
      ...currentForms,
      [exercise.id]: {
        ...getWeightScaleForm(exercise),
        [field]: value,
      },
    }));
  }

  function updateMicroWeightScaleRow(exercise, rowIndex, field, value) {
    const currentRows = getWeightScaleForm(exercise).micro_weight_options || [];
    const nextRows = currentRows.map((row, index) => (
      index === rowIndex ? { ...row, [field]: value } : row
    ));

    setWeightScaleFormsByExerciseId((currentForms) => ({
      ...currentForms,
      [exercise.id]: {
        ...getWeightScaleForm(exercise),
        micro_weight_options: nextRows,
      },
    }));
  }

  function addMicroWeightScaleRow(exercise) {
    setWeightScaleFormsByExerciseId((currentForms) => ({
      ...currentForms,
      [exercise.id]: {
        ...getWeightScaleForm(exercise),
        micro_weight_options: [
          ...(getWeightScaleForm(exercise).micro_weight_options || []),
          { count: "", weight: "" },
        ],
      },
    }));
  }

  function removeMicroWeightScaleRow(exercise, rowIndex) {
    const currentRows = getWeightScaleForm(exercise).micro_weight_options || [];
    const nextRows = currentRows.filter((_, index) => index !== rowIndex);

    setWeightScaleFormsByExerciseId((currentForms) => ({
      ...currentForms,
      [exercise.id]: {
        ...getWeightScaleForm(exercise),
        micro_weight_options: nextRows.length ? nextRows : [{ count: "", weight: "" }],
      },
    }));
  }

  function updateProgramExerciseScale(trainingExerciseId, data) {
    setProgram((currentProgram) => {
      if (!currentProgram) {
        return currentProgram;
      }

      return {
        ...currentProgram,
        workouts: currentProgram.workouts.map((workout) => ({
          ...workout,
          exercises: workout.exercises.map((exercise) => (
            exercise.id === trainingExerciseId
              ? {
                  ...exercise,
                  exercise_main_weight_options: data.main_weight_options,
                  exercise_micro_weight_options: data.micro_weight_options,
                }
              : exercise
          )),
        })),
      };
    });
  }

  async function saveWeightScale(exercise) {
    const formData = getWeightScaleForm(exercise);
    const payload = {
      main_weight_options: parseWeightOptions(formData.main_weight_options),
      micro_weight_options: serializeMicroWeightRows(formData.micro_weight_options),
    };

    setIsSavingWeightScaleByExerciseId((currentState) => ({
      ...currentState,
      [exercise.id]: true,
    }));

    try {
      const data = await trainingApi.saveExerciseWeightScale(profileId, exercise.id, payload);

      updateProgramExerciseScale(exercise.id, data);
      setWeightScaleFormsByExerciseId((currentForms) => ({
        ...currentForms,
        [exercise.id]: {
          main_weight_options: formatWeightOptions(data.main_weight_options),
          micro_weight_options: buildMicroWeightRows(data.micro_weight_options),
        },
      }));
      setOpenWeightScaleByExerciseId((currentState) => ({
        ...currentState,
        [exercise.id]: false,
      }));

      if (activeSessionByWorkout[exercise.workout]) {
        await loadExerciseHistory(exercise);
      }
    } catch (error) {
      console.error(error);
      alert("Não consegui contactar o servidor para guardar a escala de pesos.");
    } finally {
      setIsSavingWeightScaleByExerciseId((currentState) => ({
        ...currentState,
        [exercise.id]: false,
      }));
    }
  }

  return {
    openWeightScaleByExerciseId,
    setOpenWeightScaleByExerciseId,
    weightScaleFormsByExerciseId,
    setWeightScaleFormsByExerciseId,
    isSavingWeightScaleByExerciseId,
    setIsSavingWeightScaleByExerciseId,
    getWeightScaleForm,
    toggleWeightScaleMenu,
    updateWeightScaleForm,
    updateMicroWeightScaleRow,
    addMicroWeightScaleRow,
    removeMicroWeightScaleRow,
    saveWeightScale,
  };
}
