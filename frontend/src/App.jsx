import { useEffect, useState } from "react";
import AiCoachSummaryPanel from "./components/AiCoachSummaryPanel";
import AthleteDashboardPanel from "./components/AthleteDashboardPanel";
import ExerciseCalibrationPanel from "./components/ExerciseCalibrationPanel";
import ExerciseSetTable from "./components/ExerciseSetTable";
import ExerciseWeightScalePanel from "./components/ExerciseWeightScalePanel";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const DEFAULT_REST_SECONDS = 120;
const TARGET_REPS = 12;

const SET_TYPES = [
  { value: "WARMUP", label: "Aquecimento", shortLabel: "W", color: "#eab308" },
  { value: "WORKING", label: "Normal", shortLabel: "N", color: "#f8fafc" },
  { value: "DROP", label: "Drop", shortLabel: "D", color: "#ef4444" },
];

const EFFORT_OPTIONS = [
  { value: "FAILURE", label: "FALHA", color: "#ef4444", reachedFailure: true, rir: null },
  { value: "RIR_0_1", label: "RIR 0/1", color: "#f97316", reachedFailure: false, rir: 1 },
  { value: "RIR_2_3", label: "RIR 2/3", color: "#eab308", reachedFailure: false, rir: 2 },
  { value: "RIR_4_PLUS", label: "RIR 4+", color: "#22c55e", reachedFailure: false, rir: 4 },
];
const WARMUP_EFFORT = { value: "WARMUP_DONE", label: "Feita", reachedFailure: false, rir: null };

function App() {
  const [step, setStep] = useState(1);
  const [profileId, setProfileId] = useState(null);
  const [userId, setUserId] = useState(null);
  const [program, setProgram] = useState(null);
  const [programError, setProgramError] = useState("");
  const [isGeneratingProgram, setIsGeneratingProgram] = useState(false);
  const [setForms, setSetForms] = useState({});
  const [recommendations, setRecommendations] = useState({});
  const [activeSessionByWorkout, setActiveSessionByWorkout] = useState({});
  const [sessionNotes, setSessionNotes] = useState({});
  const [openExerciseById, setOpenExerciseById] = useState({});
  const [openWorkoutId, setOpenWorkoutId] = useState(null);
  const [exerciseLogsById, setExerciseLogsById] = useState({});
  const [substitutionOptionsByExerciseId, setSubstitutionOptionsByExerciseId] = useState({});
  const [openSubstitutionByExerciseId, setOpenSubstitutionByExerciseId] = useState({});
  const [isReplacingExerciseById, setIsReplacingExerciseById] = useState({});
  const [openWeightScaleByExerciseId, setOpenWeightScaleByExerciseId] = useState({});
  const [weightScaleFormsByExerciseId, setWeightScaleFormsByExerciseId] = useState({});
  const [isSavingWeightScaleByExerciseId, setIsSavingWeightScaleByExerciseId] = useState({});
  const [calibrationFormsByExerciseId, setCalibrationFormsByExerciseId] = useState({});
  const [isSavingCalibrationByExerciseId, setIsSavingCalibrationByExerciseId] = useState({});
  const [completedCalibrationByExerciseId, setCompletedCalibrationByExerciseId] = useState({});
  const [exerciseRowCounts, setExerciseRowCounts] = useState({});
  const [restTimers, setRestTimers] = useState({});
  const [openCompletionMenuBySet, setOpenCompletionMenuBySet] = useState({});
  const [openRestMenuBySet, setOpenRestMenuBySet] = useState({});
  const [openSetTypeMenuBySet, setOpenSetTypeMenuBySet] = useState({});
  const [removedSetByKey, setRemovedSetByKey] = useState({});
  const [latestWorkoutProgression, setLatestWorkoutProgression] = useState(null);
  const [latestAiCoach, setLatestAiCoach] = useState(null);
  const [athleteDashboard, setAthleteDashboard] = useState(null);
  const [adaptivePlan, setAdaptivePlan] = useState(null);
  const [adaptiveDecisions, setAdaptiveDecisions] = useState([]);
  const [weeklyFeedback, setWeeklyFeedback] = useState(null);
  const [trainingBlock, setTrainingBlock] = useState(null);
  const [applyingAdaptiveById, setApplyingAdaptiveById] = useState({});
  const [loginUsername, setLoginUsername] = useState("");
  const [loginError, setLoginError] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isDeletingExperimentalUsers, setIsDeletingExperimentalUsers] = useState(false);
  const [deleteUsersMessage, setDeleteUsersMessage] = useState("");

  const [form, setForm] = useState({
    username: "",
    gender: "MALE",
    age: 34,
    height_cm: 172,
    weight_kg: 72,
    goal: "HYPERTROPHY",
    level: "INTERMEDIATE",
    training_experience: "ONE_TO_THREE",
    days_per_week: 5,
  });
  const levelGuidance = {
    BEGINNER: {
      label: "Beginner",
      text: "Menos volume, foco em técnica e consistência.",
    },
    INTERMEDIATE: {
      label: "Intermediate",
      text: "Mais volume, maior frequência e progressão mais desafiante.",
    },
    ADVANCED: {
      label: "Advanced",
      text: "Mais especialização, maior fadiga e mais atenção à recuperação.",
    },
  };
  const goalLabels = {
    HYPERTROPHY: "Gain muscle",
    STRENGTH: "Gain strength",
    FAT_LOSS: "Lose fat",
    RECOMPOSITION: "Recomposition",
    GENERAL_FITNESS: "General fitness",
  };

  useEffect(() => {
    const hasRunningTimer = Object.values(restTimers).some((seconds) => seconds > 0);

    if (!hasRunningTimer) {
      return;
    }

    const timerId = window.setInterval(() => {
      setRestTimers((currentTimers) =>
        Object.fromEntries(
          Object.entries(currentTimers).map(([exerciseId, seconds]) => [
            exerciseId,
            Math.max(0, seconds - 1),
          ])
        )
      );
    }, 1000);

    return () => window.clearInterval(timerId);
  }, [restTimers]);

  function getActiveWorkoutId() {
    return Object.keys(activeSessionByWorkout).find((workoutId) =>
      Boolean(activeSessionByWorkout[workoutId])
    );
  }

  function getSetFormKey(trainingExerciseId, setNumber) {
    return `${trainingExerciseId}-${setNumber}`;
  }

  function getSetTypeMeta(setType) {
    return SET_TYPES.find((type) => type.value === setType) || SET_TYPES[1];
  }

  function getEffortMetaFromSet(setLog) {
    if (!setLog) {
      return null;
    }

    if (setLog.set_type === "WARMUP") {
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

  function exerciseNeedsCalibration(exercise) {
    return Boolean(getCalibrationState(exercise).needs_calibration);
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

  function formatTimer(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    return `${minutes}min ${String(seconds).padStart(2, "0")}s`;
  }

  function getRestSecondsForRow(setFormKey) {
    return Number(setForms[setFormKey]?.rest_seconds || DEFAULT_REST_SECONDS);
  }

  function formatPreviousSet(setLog) {
    if (!setLog) {
      return "-";
    }

    const effortMeta = getEffortMetaFromSet(setLog);
    const effortLabel = effortMeta ? ` ${effortMeta.label}` : "";

    return `${setLog.weight_used}kg x ${setLog.reps_completed}${effortLabel}`;
  }

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

  function getNextExerciseRow(exercise, rows) {
    return rows.find((row) => !getCurrentSetForRow(exercise.id, row.displaySetNumber));
  }

  function getGuidanceForExercise(exercise, rows, restSeconds) {
    if (restSeconds > 0) {
      return {
        eyebrow: "Descanso",
        title: "Aguarda antes da próxima série",
        message: "Respira, recupera a técnica e prepara a próxima execução.",
        isResting: true,
      };
    }

    const latestRecommendation = recommendations[exercise.id];

    if (latestRecommendation?.exercise_status === "complete") {
      return {
        eyebrow: "Exercício concluído",
        title: latestRecommendation.guidance_title || "Passa para o próximo exercício",
        message: latestRecommendation.guidance_message || "O coach decidiu que continuar agora acrescenta mais fadiga do que benefício.",
        reason: latestRecommendation.reason,
        isResting: false,
        source: latestRecommendation.source,
        confidence: latestRecommendation.confidence,
        llmStatus: latestRecommendation.llm_status,
        guardrailApplied: latestRecommendation.guardrail_applied,
        guardrailReason: latestRecommendation.guardrail_reason,
        decisionBasis: latestRecommendation.decision_basis || [],
      };
    }

    const nextRow = getNextExerciseRow(exercise, rows);

    if (!nextRow) {
      return {
        eyebrow: "Exercício concluído",
        title: "Todas as séries deste exercício estão registadas",
        message: "Segue para o próximo exercício quando te sentires pronto.",
        isResting: false,
      };
    }

    const rowSetType = getSetTypeForExerciseRow(exercise, nextRow.sourceSetNumber, nextRow.displaySetNumber);
    const visibleSetLabel = getVisibleSetLabel(exercise, rows, nextRow.sourceSetNumber, nextRow.displaySetNumber);
    const plannedValues = getPlannedValuesForExerciseRow(
      exercise,
      rows,
      nextRow.sourceSetNumber,
      nextRow.displaySetNumber
    );
    const warmupReferenceSet = getWarmupReferenceSet(
      exercise,
      rows,
      nextRow.sourceSetNumber,
      nextRow.displaySetNumber
    );
    const recommendedWeight = plannedValues.weight || latestRecommendation?.recommended_weight;
    const recommendedReps = plannedValues.reps || latestRecommendation?.target_reps;
    const targetLabel = getExerciseTargetLabel(exercise);
    const hasLoadTarget = recommendedWeight !== "" && recommendedWeight !== undefined && recommendedReps;
    const loadCue = hasLoadTarget
      ? `Aponta para ${recommendedWeight}kg x ${targetLabel} reps.`
      : `Trabalha com o objectivo de chegar às ${targetLabel} reps.`;
    const warmupCue = plannedValues.weight && plannedValues.reps
        ? `Aquecimento recomendado: ${plannedValues.weight}kg x ${plannedValues.reps} reps.`
      : warmupReferenceSet
        ? `Mantém a referência anterior de ${warmupReferenceSet.weight_used}kg x ${warmupReferenceSet.reps_completed} reps.`
      : `Sobe a carga gradualmente até sentires o movimento pronto.`;
    const coachTitle = latestRecommendation?.guidance_title;
    const coachMessage = latestRecommendation?.guidance_message;
    const reason = latestRecommendation?.reason || plannedValues.reason || "";
    const coachMetadata = {
      source: latestRecommendation?.source || plannedValues.source,
      confidence: latestRecommendation?.confidence || plannedValues.confidence,
      llmStatus: latestRecommendation?.llm_status,
      guardrailApplied: latestRecommendation?.guardrail_applied,
      guardrailReason: latestRecommendation?.guardrail_reason,
      decisionBasis: latestRecommendation?.decision_basis || plannedValues.decisionBasis || [],
    };

    if (rowSetType === "WARMUP") {
      return {
        eyebrow: "Próximo passo",
        title: `Faz a série ${visibleSetLabel} de aquecimento`,
        message: `Usa uma carga controlada para preparar o movimento. ${warmupCue}`,
        reason: "",
        isResting: false,
        ...coachMetadata,
      };
    }

    if (rowSetType === "DROP") {
      return {
        eyebrow: "Próximo passo",
        title: coachTitle ? `Série ${visibleSetLabel}: ${coachTitle}` : `Faz a série ${visibleSetLabel} em drop`,
        message: coachMessage ? `${coachMessage} ${loadCue}` : `Reduz a carga e mantém a execução limpa até ao alvo. ${loadCue}`,
        reason,
        isResting: false,
        ...coachMetadata,
      };
    }

    return {
      eyebrow: "Próximo passo",
      title: coachTitle ? `Série ${visibleSetLabel}: ${coachTitle}` : `Faz a série ${visibleSetLabel}`,
      message: coachMessage ? `${coachMessage} ${loadCue}` : `Mantém o controlo e respeita o esforço planeado. ${loadCue}`,
      reason,
      isResting: false,
      ...coachMetadata,
    };
  }

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

  function formatNumber(value, digits = 1) {
    return Number(value || 0).toFixed(digits);
  }

  function formatDashboardDate(dateValue) {
    if (!dateValue) {
      return "-";
    }

    return new Date(dateValue).toLocaleDateString("pt-PT", {
      day: "2-digit",
      month: "short",
    });
  }

  function getDashboardMaxWeeklyVolume(dashboard) {
    return Math.max(
      ...((dashboard?.weekly_volume || []).map((week) => Number(week.volume) || 0)),
      1
    );
  }

  function getAdaptiveActionLabel(action) {
    const labels = {
      protect_recovery: "Proteger recuperação",
      increase_margin: "Aumentar margem",
      progress_load: "Progredir carga",
      maintain_plan: "Manter plano",
    };

    return labels[action] || "Ajuste";
  }

  function getAdaptiveActionColor(action) {
    const colors = {
      protect_recovery: "#fbbf24",
      increase_margin: "#38bdf8",
      progress_load: "#86efac",
      maintain_plan: "#94a3b8",
    };

    return colors[action] || "#94a3b8";
  }

  function getAdaptiveDecisionStatusLabel(status) {
    const labels = {
      APPLIED: "Aplicada",
      DEFERRED: "Adiada",
      IGNORED: "Ignorada",
    };

    return labels[status] || status;
  }

  function getWeeklyFeedbackStatusColor(status) {
    const colors = {
      deload_recommended: "#fbbf24",
      monitor: "#38bdf8",
      progressing: "#86efac",
    };

    return colors[status] || "#94a3b8";
  }

  function getWeeklyFeedbackStatusLabel(status) {
    const labels = {
      deload_recommended: "Deload recomendado",
      monitor: "Monitorizar",
      progressing: "Progressão saudável",
    };

    return labels[status] || "Feedback semanal";
  }

  function getTrainingBlockPhaseLabel(phase) {
    const labels = {
      BUILD: "Build",
      DELOAD: "Deload",
      RETURN: "Retorno",
    };

    return labels[phase] || "Bloco";
  }

  function getTrainingBlockPhaseColor(phase) {
    const colors = {
      BUILD: "#86efac",
      DELOAD: "#fbbf24",
      RETURN: "#38bdf8",
    };

    return colors[phase] || "#94a3b8";
  }

  function getProgressionActionLabel(action) {
    const labels = {
      increase_load: "Subir carga",
      maintain_load: "Manter carga",
      reduce_volume: "Reduzir volume",
      adjust_target_rir: "Alterar RIR",
      maintain: "Manter plano",
    };

    return labels[action] || "Recomendação";
  }

  function formatProgressionTarget(recommendation) {
    const weightLabel = recommendation.recommended_weight === "" || recommendation.recommended_weight === null
      ? "carga do plano"
      : `${recommendation.recommended_weight}kg`;

    return `${weightLabel} | ${recommendation.recommended_sets} séries | ${recommendation.target_reps} reps | RIR ${recommendation.target_rir}`;
  }

  function getAiCoachSourceLabel(status) {
    const labels = {
      llm_enabled: "OpenAI",
      llm_error: "Fallback local",
      llm_disabled: "Fallback local",
    };

    return labels[status] || "Coach";
  }

  function getDecisionSourceLabel(source) {
    const labels = {
      hybrid_local_training_coach: "Coach híbrido local",
      hybrid_local_workout_progression: "Progressão híbrida local",
      openai_training_decision: "IA OpenAI série a série",
      ollama_training_decision: "IA Ollama local",
      last_15_workout_history: "Histórico últimos 15 treinos",
      warmup_from_first_working_set: "Aquecimento proporcional",
      warmup_ramp_from_first_working_set: "Aquecimento progressivo",
      training_coach_engine: "Motor local",
    };

    return labels[source] || "Motor local";
  }

  function getLlmStatusLabel(status) {
    const labels = {
      llm_enabled: "IA ativa",
      llm_error: "Fallback local",
      llm_disabled: "Regras locais",
    };

    return labels[status] || "";
  }

  function getConfidenceColor(confidence) {
    const colors = {
      alta: "#22c55e",
      média: "#eab308",
      baixa: "#f97316",
    };

    return colors[confidence] || "#94a3b8";
  }

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  function updateSetForm(setFormKey, field, value) {
    setSetForms({
      ...setForms,
      [setFormKey]: {
        ...setForms[setFormKey],
        [field]: value,
      },
    });
  }

  function formatWeightOptions(options) {
    return (options || []).join(", ");
  }

  function parseWeightOptions(value) {
    return String(value || "")
      .split(/[,;\n]/)
      .map((item) => item.trim().replace(",", "."))
      .filter(Boolean)
      .map(Number)
      .filter((number) => Number.isFinite(number) && number >= 0);
  }

  function parseDecimalInput(value) {
    return Number(String(value || "").replace(",", "."));
  }

  function buildMicroWeightRows(options) {
    const groupedWeights = new Map();

    (options || []).forEach((option) => {
      const weight = typeof option === "object" ? parseDecimalInput(option.weight) : parseDecimalInput(option);
      const count = typeof option === "object" ? parseDecimalInput(option.count || 1) : 1;

      if (!Number.isFinite(weight) || weight <= 0 || !Number.isFinite(count) || count <= 0) {
        return;
      }

      groupedWeights.set(weight, (groupedWeights.get(weight) || 0) + count);
    });

    const rows = Array.from(groupedWeights.entries()).map(([weight, count]) => ({
      weight,
      count,
    }));

    return rows.length ? rows : [{ count: "", weight: "" }];
  }

  function serializeMicroWeightRows(rows) {
    return (rows || [])
      .map((row) => ({
        count: parseDecimalInput(row.count),
        weight: parseDecimalInput(row.weight),
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

    setWeightScaleFormsByExerciseId((currentForms) => ({
      ...currentForms,
      [exercise.id]: {
        ...getWeightScaleForm(exercise),
        micro_weight_options: currentRows.map((row, index) => (
          index === rowIndex ? { ...row, [field]: value } : row
        )),
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
      const response = await fetch(`${API_BASE_URL}/api/training/exercise-weight-scale/${profileId}/${exercise.id}/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();

      if (!response.ok) {
        console.error(data);
        alert("Não consegui guardar a escala de pesos deste exercício.");
        return;
      }

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
      const response = await fetch(`${API_BASE_URL}/api/training/exercise-calibration/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile_id: profileId,
          training_exercise_id: exercise.id,
          weight_used: Number(formData.weight_used),
          result_color: formData.result_color,
          reps_completed: getCalibrationColorReps(formData.result_color),
          rir: 0,
          reached_failure: true,
          notes: formData.notes || "",
        }),
      });
      const data = await response.json();

      if (!response.ok) {
        console.error(data);
        alert("Não consegui guardar a calibração deste exercício.");
        return;
      }

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

  async function exportUserTrainingData() {
    if (!profileId) {
      alert("Não encontrei o perfil ativo para exportar.");
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/accounts/profiles/${profileId}/export/`);

      if (!response.ok) {
        const data = await response.json();
        console.error(data);
        alert("Não consegui exportar o histórico deste atleta.");
        return;
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");

      link.href = url;
      link.download = `shapetronyc-${form.username || "athlete"}-${timestamp}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(error);
      alert("Não consegui contactar o servidor para exportar o histórico.");
    }
  }

  async function loadAthleteDashboard(profileIdOverride = null) {
    const dashboardProfileId = profileIdOverride || profileId;

    if (!dashboardProfileId) {
      return null;
    }

    const response = await fetch(`${API_BASE_URL}/api/training/dashboard/${dashboardProfileId}/`);
    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      return null;
    }

    setAthleteDashboard(data);
    return data;
  }

  async function loadAdaptivePlan(profileIdOverride = null) {
    const adaptiveProfileId = profileIdOverride || profileId;

    if (!adaptiveProfileId) {
      return null;
    }

    const response = await fetch(`${API_BASE_URL}/api/training/adaptive-plan/${adaptiveProfileId}/`);
    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      return null;
    }

    setAdaptivePlan(data);
    return data;
  }

  async function loadAdaptiveDecisions(profileIdOverride = null) {
    const decisionsProfileId = profileIdOverride || profileId;

    if (!decisionsProfileId) {
      return [];
    }

    const response = await fetch(`${API_BASE_URL}/api/training/adaptive-plan/decisions/${decisionsProfileId}/`);
    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      return [];
    }

    setAdaptiveDecisions(data.decisions || []);
    return data.decisions || [];
  }

  async function loadWeeklyFeedback(profileIdOverride = null) {
    const feedbackProfileId = profileIdOverride || profileId;

    if (!feedbackProfileId) {
      return null;
    }

    const response = await fetch(`${API_BASE_URL}/api/training/weekly-feedback/${feedbackProfileId}/`);
    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      return null;
    }

    setWeeklyFeedback(data);
    return data;
  }

  async function loadTrainingBlock(profileIdOverride = null) {
    const blockProfileId = profileIdOverride || profileId;

    if (!blockProfileId) {
      return null;
    }

    const response = await fetch(`${API_BASE_URL}/api/training/training-blocks/${blockProfileId}/`);
    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      return null;
    }

    setTrainingBlock(data);
    return data;
  }

  async function loginExistingProfile(e) {
    e.preventDefault();

    const normalizedUsername = loginUsername.trim().toLowerCase();

    if (!normalizedUsername) {
      setLoginError("Escreve o username do atleta.");
      return;
    }

    setLoginError("");
    setProgramError("");
    setIsLoggingIn(true);

    try {
      const profilesResponse = await fetch(`${API_BASE_URL}/api/accounts/profiles/`);
      const profilesData = await profilesResponse.json();

      if (!profilesResponse.ok) {
        console.error(profilesData);
        setLoginError("Não consegui procurar atletas existentes.");
        return;
      }

      const profile = profilesData.find(
        (item) => item.username?.toLowerCase() === normalizedUsername
      );

      if (!profile) {
        setLoginError("Não encontrei nenhum atleta com esse username.");
        return;
      }

      setUserId(profile.user);
      setProfileId(profile.id);
      setForm({
        username: profile.username,
        gender: profile.gender,
        age: profile.age,
        height_cm: profile.height_cm,
        weight_kg: profile.weight_kg,
        goal: profile.goal,
        level: profile.level,
        training_experience: profile.training_experience,
        days_per_week: profile.days_per_week,
      });
      setLatestWorkoutProgression(null);
      setLatestAiCoach(null);
      setRecommendations({});
      setExerciseLogsById({});
      setExerciseRowCounts({});
      setSetForms({});
      setCompletedCalibrationByExerciseId({});
      setRemovedSetByKey({});
      setOpenSetTypeMenuBySet({});

      const programResponse = await fetch(`${API_BASE_URL}/api/training/program/${profile.id}/`);
      const programData = await programResponse.json();

      if (!programResponse.ok) {
        setProgram(null);
        setProgramError("Perfil encontrado. Ainda não existe programa ativo para este atleta.");
        setStep(3);
        return;
      }

      setProgram(programData);
      setOpenWorkoutId(null);
      loadAthleteDashboard(profile.id);
      loadAdaptivePlan(profile.id);
      loadAdaptiveDecisions(profile.id);
      loadWeeklyFeedback(profile.id);
      loadTrainingBlock(profile.id);
      setStep(4);
    } catch (error) {
      console.error(error);
      setLoginError("Não consegui contactar o servidor para entrar no perfil.");
    } finally {
      setIsLoggingIn(false);
    }
  }

  async function recordAdaptiveDecision(recommendation, decisionStatus) {
    if (!profileId) {
      alert("Não encontrei o perfil ativo.");
      return;
    }

    if (decisionStatus === "APPLIED") {
      const shouldApply = window.confirm(
        `Aplicar ajuste em ${recommendation.exercise_name}?\n\nSéries: ${recommendation.current_sets} → ${recommendation.recommended_sets}\nRIR: ${recommendation.current_target_rir} → ${recommendation.recommended_target_rir}\nCarga sugerida: ${recommendation.load_adjustment > 0 ? "+" : ""}${recommendation.load_adjustment}kg`
      );

      if (!shouldApply) {
        return;
      }
    }

    setApplyingAdaptiveById({
      ...applyingAdaptiveById,
      [recommendation.training_exercise]: true,
    });

    const response = await fetch(`${API_BASE_URL}/api/training/adaptive-plan/apply/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile_id: profileId,
        training_exercise_id: recommendation.training_exercise,
        status: decisionStatus,
      }),
    });
    const data = await response.json();

    setApplyingAdaptiveById((currentState) => ({
      ...currentState,
      [recommendation.training_exercise]: false,
    }));

    if (!response.ok) {
      console.error(data);
      alert("Não consegui gravar a decisão adaptativa.");
      return;
    }

    if (decisionStatus === "APPLIED") {
      setProgram((currentProgram) => {
        if (!currentProgram) {
          return currentProgram;
        }

        return {
          ...currentProgram,
          workouts: currentProgram.workouts.map((workout) => ({
            ...workout,
            exercises: workout.exercises.map((exercise) => (
              exercise.id === data.updated_exercise.id
                ? {
                    ...exercise,
                    sets: data.updated_exercise.sets,
                    target_rir: data.updated_exercise.target_rir,
                  }
                : exercise
            )),
          })),
        };
      });
    }

    await loadAdaptivePlan();
    await loadAdaptiveDecisions();
    await loadWeeklyFeedback();
    await loadTrainingBlock();
  }

  function toggleWorkout(workoutId) {
    if (getActiveWorkoutId()) {
      return;
    }

    setOpenWorkoutId(openWorkoutId === workoutId ? null : workoutId);
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

  async function loadExerciseSubstitutions(exercise) {
    if (substitutionOptionsByExerciseId[exercise.id]) {
      return substitutionOptionsByExerciseId[exercise.id];
    }

    const response = await fetch(`${API_BASE_URL}/api/training/exercise-substitutions/${exercise.id}/`);
    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      alert("Não consegui carregar alternativas para este exercício.");
      return null;
    }

    setSubstitutionOptionsByExerciseId((currentOptions) => ({
      ...currentOptions,
      [exercise.id]: data,
    }));

    return data;
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
      const response = await fetch(`${API_BASE_URL}/api/training/replace-exercise/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          training_exercise_id: exercise.id,
          replacement_exercise_id: replacementExerciseId,
        }),
      });
      const data = await response.json();

      if (!response.ok) {
        console.error(data);
        alert(data.error || "Não consegui trocar o exercício.");
        return;
      }

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
      await loadAdaptivePlan();
      await loadAdaptiveDecisions();
      await loadWeeklyFeedback();
      await loadTrainingBlock();
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

  async function loadExerciseHistory(exercise, sessionIdOverride = null) {
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

    const response = await fetch(`${API_BASE_URL}/api/progression/exercise-history/?${params}`);
    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      return null;
    }

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
  }

  async function createProfile(e) {
    e.preventDefault();
    setProgramError("");

    const userResponse = await fetch(`${API_BASE_URL}/api/accounts/create-user/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: form.username }),
    });

    const userData = await userResponse.json();

    if (!userResponse.ok) {
      console.error(userData);
      alert("Erro ao criar utilizador. Confirma os dados e tenta novamente.");
      return;
    }

    setUserId(userData.id);

    const profileResponse = await fetch(`${API_BASE_URL}/api/accounts/profiles/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user: userData.id,
        gender: form.gender,
        age: Number(form.age),
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        goal: form.goal,
        level: form.level,
        training_experience: form.training_experience,
        days_per_week: Number(form.days_per_week),
      }),
    });

    const profileData = await profileResponse.json();

    if (!profileResponse.ok) {
      console.error(profileData);
      alert("Erro ao criar perfil. Confirma os dados e tenta novamente.");
      return;
    }

    setProfileId(profileData.id);
    setStep(3);
  }

  async function generateProgram() {
    if (!profileId) {
      setProgramError("Não encontrei o perfil activo. Volta a criar o perfil antes de gerar o programa.");
      return;
    }

    setProgramError("");
    setIsGeneratingProgram(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/training/generate-program/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile_id: profileId }),
      });

      const data = await response.json();

      if (!response.ok) {
        console.error(data);
        setProgramError(data.error || "Não foi possível gerar o programa. Tenta novamente.");
        return;
      }

      if (!Array.isArray(data.workouts)) {
        console.error(data);
        setProgramError("A resposta do programa veio incompleta. Tenta novamente.");
        return;
      }

      setProgram(data);
      setOpenWorkoutId(null);
      setLatestWorkoutProgression(null);
      setLatestAiCoach(null);
      setRecommendations({});
      setExerciseLogsById({});
      setExerciseRowCounts({});
      setCalibrationFormsByExerciseId({});
      setCompletedCalibrationByExerciseId({});
      setRemovedSetByKey({});
      setOpenSetTypeMenuBySet({});
      loadAthleteDashboard(profileId);
      loadAdaptivePlan(profileId);
      loadAdaptiveDecisions(profileId);
      loadWeeklyFeedback(profileId);
      loadTrainingBlock(profileId);
      setStep(4);
    } catch (error) {
      console.error(error);
      setProgramError("Não consegui contactar o servidor para gerar o programa.");
    } finally {
      setIsGeneratingProgram(false);
    }
  }

  async function startWorkoutSession(workout) {
    const response = await fetch(`${API_BASE_URL}/api/training/start-session/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile_id: profileId,
        workout_id: workout.id,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      alert("Erro ao iniciar treino.");
      return;
    }

    setActiveSessionByWorkout({
      ...activeSessionByWorkout,
      [workout.id]: data.id,
    });
    setOpenWorkoutId(workout.id);
    setLatestWorkoutProgression(null);
    setLatestAiCoach(null);
    setRecommendations({});
    setExerciseLogsById({});
    setExerciseRowCounts({});
    setCalibrationFormsByExerciseId({});
    setCompletedCalibrationByExerciseId({});
    setSetForms({});
    setRemovedSetByKey({});
    setOpenSetTypeMenuBySet({});
    loadAthleteDashboard();
    loadAdaptivePlan();
    loadAdaptiveDecisions();
    loadWeeklyFeedback();
    loadTrainingBlock();

    workout.exercises.forEach((exercise) => {
      loadExerciseHistory(exercise, data.id);
    });
  }

  async function finishWorkoutSession(workout) {
    const sessionId = activeSessionByWorkout[workout.id];

    if (!sessionId) {
      alert("Não existe sessão ativa para este treino.");
      return;
    }

    const response = await fetch(`${API_BASE_URL}/api/training/finish-session/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        notes: sessionNotes[workout.id] || "",
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      alert("Erro ao terminar treino.");
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
    loadAthleteDashboard();
    loadAdaptivePlan();
    loadAdaptiveDecisions();
    loadWeeklyFeedback();
    loadTrainingBlock();

    alert(`Workout finished: ${data.workout_name}`);
  }

  function toggleCompletionMenu(setFormKey) {
    setOpenCompletionMenuBySet({
      ...openCompletionMenuBySet,
      [setFormKey]: !openCompletionMenuBySet[setFormKey],
    });
  }

  function toggleRestMenu(setFormKey) {
    setOpenRestMenuBySet({
      ...openRestMenuBySet,
      [setFormKey]: !openRestMenuBySet[setFormKey],
    });
  }

  function adjustRestTimer(exerciseId, secondsDelta) {
    setRestTimers((currentTimers) => ({
      ...currentTimers,
      [exerciseId]: Math.max(0, (currentTimers[exerciseId] || 0) + secondsDelta),
    }));
  }

  function toggleSetTypeMenu(setFormKey) {
    setOpenSetTypeMenuBySet({
      ...openSetTypeMenuBySet,
      [setFormKey]: !openSetTypeMenuBySet[setFormKey],
    });
  }

  function selectSetType(setFormKey, setType) {
    setSetForms((currentSetForms) => ({
      ...currentSetForms,
      [setFormKey]: {
        ...currentSetForms[setFormKey],
        set_type: setType,
        set_type_source: "manual",
      },
    }));
    setOpenSetTypeMenuBySet({
      ...openSetTypeMenuBySet,
      [setFormKey]: false,
    });
  }

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

    const response = await fetch(`${API_BASE_URL}/api/progression/set-logs/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
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
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(data);
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

    setOpenCompletionMenuBySet({
      ...openCompletionMenuBySet,
      [setFormKey]: false,
    });

    setOpenRestMenuBySet({
      ...openRestMenuBySet,
      [setFormKey]: false,
    });

    setOpenSetTypeMenuBySet({
      ...openSetTypeMenuBySet,
      [setFormKey]: false,
    });

    const currentExerciseLogs = getExerciseLogs(exercise.id);
    const completedSetsForCoach = [
      ...currentExerciseLogs.current_sets.filter(
        (setLog) => Number(setLog.set_number) !== displaySetNumber
      ),
      data,
    ].sort((firstSet, secondSet) => Number(firstSet.set_number) - Number(secondSet.set_number));

    const recommendationResponse = await fetch(`${API_BASE_URL}/api/recommendations/next-set/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
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
      }),
    });

    const recommendationData = await recommendationResponse.json();

    if (recommendationResponse.ok) {
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

    const deleteResponses = await Promise.all(
      setLogsToRemove.map((setLog) =>
        fetch(`${API_BASE_URL}/api/progression/set-logs/${setLog.id}/`, {
          method: "DELETE",
        })
      )
    );

    if (deleteResponses.some((response) => !response.ok)) {
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

  async function deleteExperimentalUsers() {
    const confirmed = window.confirm(
      "Isto vai apagar todos os atletas experimentais e os dados associados. A biblioteca de exercícios fica preservada. Queres continuar?"
    );

    if (!confirmed) {
      return;
    }

    setDeleteUsersMessage("");
    setLoginError("");
    setProgramError("");
    setIsDeletingExperimentalUsers(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/accounts/experimental/delete-users/`, {
        method: "DELETE",
      });
      const data = await response.json();

      if (!response.ok) {
        console.error(data);
        setDeleteUsersMessage("Não consegui apagar os atletas experimentais.");
        return;
      }

      setProfileId(null);
      setUserId(null);
      setProgram(null);
      setSetForms({});
      setRecommendations({});
      setActiveSessionByWorkout({});
      setSessionNotes({});
      setOpenExerciseById({});
      setOpenWorkoutId(null);
      setExerciseLogsById({});
      setSubstitutionOptionsByExerciseId({});
      setOpenSubstitutionByExerciseId({});
      setIsReplacingExerciseById({});
      setOpenWeightScaleByExerciseId({});
      setWeightScaleFormsByExerciseId({});
      setIsSavingWeightScaleByExerciseId({});
      setCalibrationFormsByExerciseId({});
      setIsSavingCalibrationByExerciseId({});
      setCompletedCalibrationByExerciseId({});
      setExerciseRowCounts({});
      setRestTimers({});
      setOpenCompletionMenuBySet({});
      setOpenRestMenuBySet({});
      setOpenSetTypeMenuBySet({});
      setRemovedSetByKey({});
      setLatestWorkoutProgression(null);
      setLatestAiCoach(null);
      setAthleteDashboard(null);
      setAdaptivePlan(null);
      setAdaptiveDecisions([]);
      setWeeklyFeedback(null);
      setTrainingBlock(null);
      setApplyingAdaptiveById({});
      setLoginUsername("");
      setStep(1);
      setDeleteUsersMessage(`${data.deleted_users} atleta(s) experimental(is) apagado(s).`);
    } catch (error) {
      console.error(error);
      setDeleteUsersMessage("Erro de ligação ao apagar atletas experimentais.");
    } finally {
      setIsDeletingExperimentalUsers(false);
    }
  }

  return (
    <div className={step === 1 ? "app-shell home-app-shell" : step === 2 ? "app-shell profile-app-shell" : "app-shell"}>
      <h1>SHAPETRONYC</h1>

      {step === 1 && (
        <div className="home-landing">
          <section className="home-hero-panel">
            <span className="profile-kicker">Adaptive training system</span>
            <h2>Adaptive training built around you</h2>
            <p>
              Create a new athlete profile or enter an existing one to continue training with
              history, memory, weekly feedback and adaptive planning.
            </p>
            <div className="home-signal-grid">
              <div>
                <strong>AI Coach</strong>
                <span>set-by-set guidance</span>
              </div>
              <div>
                <strong>Memory</strong>
                <span>patterns by exercise</span>
              </div>
              <div>
                <strong>Blocks</strong>
                <span>periodization review</span>
              </div>
            </div>
          </section>

          <section className="home-action-grid">
            <article className="home-action-card primary">
              <div>
                <span className="profile-kicker">New athlete</span>
                <h2>Create a new profile</h2>
                <p>
                  Start from baseline data and let SHAPETRONYC generate the first adaptive program.
                </p>
              </div>
              <button type="button" className="home-primary-button" onClick={() => setStep(2)}>
                Create new profile
              </button>
            </article>

            <form className="home-action-card" onSubmit={loginExistingProfile}>
              <div>
                <span className="profile-kicker">Existing athlete</span>
                <h2>Login</h2>
                <p>
                  Enter the athlete username to continue from the saved program, dashboard and
                  training history.
                </p>
              </div>
              <label className="profile-field">
                <span>Username</span>
                <input
                  value={loginUsername}
                  onChange={(event) => setLoginUsername(event.target.value)}
                  placeholder="e.g. beatriz"
                />
              </label>
              {loginError && <p className="home-error">{loginError}</p>}
              <button type="submit" className="home-secondary-button" disabled={isLoggingIn}>
                {isLoggingIn ? "Entering..." : "Enter profile"}
              </button>
            </form>
          </section>

          <section className="home-experimental-panel">
            <div>
              <span className="profile-kicker">Experimental</span>
              <h2>Limpar atletas de teste</h2>
              <p>
                Apaga os atletas criados durante testes e todos os dados associados: perfis,
                programas, sessões, séries, calibrações, memórias e escalas.
              </p>
            </div>
            <button
              type="button"
              className="home-danger-button"
              onClick={deleteExperimentalUsers}
              disabled={isDeletingExperimentalUsers}
            >
              {isDeletingExperimentalUsers ? "A apagar..." : "Apagar atletas experimentais"}
            </button>
            {deleteUsersMessage && <p className="home-delete-message">{deleteUsersMessage}</p>}
          </section>
        </div>
      )}

      {step === 2 && (
        <div className="profile-onboarding">
          <section className="profile-intro-panel">
            <div>
              <span className="profile-kicker">Athlete setup</span>
              <h2>Create Profile</h2>
              <p>
                Define the athlete baseline so the training plan starts with the right volume,
                frequency and progression speed.
              </p>
            </div>

            <div className="profile-preview-card">
              <span>Current setup</span>
              <strong>{goalLabels[form.goal]}</strong>
              <div className="profile-preview-grid">
                <div>
                  <span>Level</span>
                  <strong>{levelGuidance[form.level].label}</strong>
                </div>
                <div>
                  <span>Days</span>
                  <strong>{form.days_per_week}/week</strong>
                </div>
                <div>
                  <span>Body</span>
                  <strong>{form.weight_kg}kg</strong>
                </div>
                <div>
                  <span>Age</span>
                  <strong>{form.age}</strong>
                </div>
              </div>
            </div>
          </section>

          <form className="profile-form-card" onSubmit={createProfile}>
            <div className="profile-form-header">
              <div>
                <span className="profile-kicker">New athlete</span>
                <h2>Build the profile</h2>
              </div>
              <button type="submit" className="profile-submit-button">Create Profile</button>
            </div>

            <div className="profile-section">
              <h3>Identity</h3>
              <div className="profile-grid two">
                <label className="profile-field">
                  <span>Username</span>
                  <input
                    name="username"
                    value={form.username}
                    onChange={handleChange}
                    required
                    placeholder="e.g. beatriz"
                  />
                </label>

                <div className="profile-field">
                  <span>Gender</span>
                  <div className="profile-segmented">
                    {[
                      ["MALE", "Male"],
                      ["FEMALE", "Female"],
                    ].map(([value, label]) => (
                      <button
                        key={value}
                        type="button"
                        className={form.gender === value ? "active" : ""}
                        onClick={() => setForm({ ...form, gender: value })}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="profile-section">
              <h3>Body metrics</h3>
              <div className="profile-grid three">
                <label className="profile-field">
                  <span>Age</span>
                  <input name="age" type="number" value={form.age} onChange={handleChange} />
                </label>

                <label className="profile-field">
                  <span>Height</span>
                  <div className="profile-input-unit">
                    <input name="height_cm" type="number" value={form.height_cm} onChange={handleChange} />
                    <small>cm</small>
                  </div>
                </label>

                <label className="profile-field">
                  <span>Weight</span>
                  <div className="profile-input-unit">
                    <input name="weight_kg" type="number" value={form.weight_kg} onChange={handleChange} />
                    <small>kg</small>
                  </div>
                </label>
              </div>
            </div>

            <div className="profile-section">
              <h3>Training direction</h3>
              <div className="profile-grid two">
                <label className="profile-field">
                  <span>Goal</span>
                  <select name="goal" value={form.goal} onChange={handleChange}>
                    <option value="HYPERTROPHY">Gain muscle</option>
                    <option value="STRENGTH">Gain strength</option>
                    <option value="FAT_LOSS">Lose fat</option>
                    <option value="RECOMPOSITION">Recomposition</option>
                    <option value="GENERAL_FITNESS">General fitness</option>
                  </select>
                </label>

                <label className="profile-field">
                  <span>Level</span>
                  <select name="level" value={form.level} onChange={handleChange}>
                    <option value="BEGINNER">Beginner</option>
                    <option value="INTERMEDIATE">Intermediate</option>
                    <option value="ADVANCED">Advanced</option>
                  </select>
                </label>
              </div>

              <div className="profile-level-note">
                <strong>{levelGuidance[form.level].label}</strong>
                <span>{levelGuidance[form.level].text}</span>
              </div>
            </div>

            <div className="profile-section">
              <h3>Availability</h3>
              <div className="profile-grid two">
                <label className="profile-field">
                  <span>Training Experience</span>
                  <select name="training_experience" value={form.training_experience} onChange={handleChange}>
                    <option value="LESS_THAN_1">Less than 1 year</option>
                    <option value="ONE_TO_THREE">1-3 years</option>
                    <option value="THREE_TO_FIVE">3-5 years</option>
                    <option value="MORE_THAN_FIVE">More than 5 years</option>
                  </select>
                </label>

                <div className="profile-field">
                  <span>Days per week</span>
                  <div className="profile-day-picker">
                    {[2, 3, 4, 5, 6, 7].map((day) => (
                      <button
                        key={day}
                        type="button"
                        className={Number(form.days_per_week) === day ? "active" : ""}
                        onClick={() => setForm({ ...form, days_per_week: day })}
                      >
                        {day}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <button type="submit" className="profile-submit-button mobile">Create Profile</button>
          </form>
        </div>
      )}

      {step === 3 && (
        <div>
          <h2>Profile created</h2>
          <button onClick={generateProgram} disabled={isGeneratingProgram}>
            {isGeneratingProgram ? "Generating..." : "Generate My Program"}
          </button>
          {programError && <p style={{ color: "#ef4444", marginTop: "8px" }}>{programError}</p>}
        </div>
      )}

      {step === 4 && program && (
        <div>
          <div className="program-header-row">
            <h2>{program.name}</h2>
            <button
              type="button"
              className="export-user-button"
              onClick={exportUserTrainingData}
            >
              Exportar histórico
            </button>
          </div>

          <AthleteDashboardPanel
            dashboard={athleteDashboard}
            formatDate={formatDashboardDate}
            formatNumber={formatNumber}
            getConfidenceColor={getConfidenceColor}
            getMaxWeeklyVolume={getDashboardMaxWeeklyVolume}
          />

          {trainingBlock && (
            <section
              style={{
                marginTop: "16px",
                padding: "16px",
                border: "1px solid #334155",
                borderRadius: "8px",
                background: "rgba(15, 23, 42, 0.72)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: "12px",
                  alignItems: "flex-start",
                }}
              >
                <div>
                  <div
                    style={{
                      color: getTrainingBlockPhaseColor(trainingBlock.block?.phase),
                      fontSize: "12px",
                      fontWeight: "bold",
                      letterSpacing: "0",
                      textTransform: "uppercase",
                    }}
                  >
                    Bloco de treino
                  </div>
                  <h3 style={{ marginTop: "6px", marginBottom: 0 }}>
                    {trainingBlock.block?.name || "Sem bloco ativo"}
                  </h3>
                  <p style={{ margin: "8px 0 0", color: "#cbd5e1" }}>
                    {trainingBlock.summary?.phase_recommendation?.message || "Termina mais treinos para formar um bloco."}
                  </p>
                </div>
                <span
                  style={{
                    color: getTrainingBlockPhaseColor(trainingBlock.block?.phase),
                    fontSize: "12px",
                    fontWeight: "bold",
                    whiteSpace: "nowrap",
                  }}
                >
                  {getTrainingBlockPhaseLabel(trainingBlock.block?.phase)}
                </span>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
                  gap: "10px",
                  marginTop: "14px",
                }}
              >
                <div>
                  <strong>{trainingBlock.summary?.completed_sessions || 0}</strong>
                  <p style={{ margin: "3px 0 0", color: "#94a3b8", fontSize: "13px" }}>treinos no bloco</p>
                </div>
                <div>
                  <strong>{formatNumber(trainingBlock.summary?.total_volume || 0)} kg</strong>
                  <p style={{ margin: "3px 0 0", color: "#94a3b8", fontSize: "13px" }}>volume do bloco</p>
                </div>
                <div>
                  <strong>{trainingBlock.summary?.total_failures || 0}</strong>
                  <p style={{ margin: "3px 0 0", color: "#94a3b8", fontSize: "13px" }}>falhas no bloco</p>
                </div>
                <div>
                  <strong>{trainingBlock.summary?.average_rir ?? "-"}</strong>
                  <p style={{ margin: "3px 0 0", color: "#94a3b8", fontSize: "13px" }}>RIR médio</p>
                </div>
              </div>

              {trainingBlock.summary?.weekly_volume?.length > 0 && (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: `repeat(${trainingBlock.summary.weekly_volume.length}, minmax(44px, 1fr))`,
                    gap: "8px",
                    alignItems: "end",
                    height: "120px",
                    marginTop: "14px",
                  }}
                >
                  {trainingBlock.summary.weekly_volume.map((week) => {
                    const maxVolume = Math.max(
                      ...trainingBlock.summary.weekly_volume.map((item) => Number(item.volume) || 0),
                      1
                    );
                    const height = Math.max(8, (Number(week.volume) / maxVolume) * 82);

                    return (
                      <div key={week.week} style={{ display: "grid", gap: "6px", alignItems: "end" }}>
                        <div
                          title={`${week.week}: ${formatNumber(week.volume)} kg`}
                          style={{
                            height: `${height}px`,
                            borderRadius: "5px 5px 2px 2px",
                            background: getTrainingBlockPhaseColor(trainingBlock.block?.phase),
                          }}
                        />
                        <span style={{ color: "#94a3b8", fontSize: "11px", fontWeight: "bold" }}>
                          {week.week.split("-")[1]}
                        </span>
                      </div>
                    );
                  })}
                </div>
              )}

              <div
                style={{
                  marginTop: "14px",
                  padding: "12px",
                  border: "1px solid rgba(148, 163, 184, 0.18)",
                  borderRadius: "8px",
                  background: "rgba(15, 23, 42, 0.38)",
                }}
              >
                <strong>{trainingBlock.summary?.phase_recommendation?.title}</strong>
                <p style={{ margin: "6px 0 0", color: "#94a3b8", fontSize: "13px" }}>
                  {trainingBlock.summary?.phase_recommendation?.next_step}
                </p>
              </div>
            </section>
          )}

          {weeklyFeedback && (
            <section
              style={{
                marginTop: "16px",
                padding: "16px",
                border: "1px solid #334155",
                borderRadius: "8px",
                background: "rgba(30, 41, 59, 0.72)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: "12px",
                  alignItems: "flex-start",
                }}
              >
                <div>
                  <div
                    style={{
                      color: getWeeklyFeedbackStatusColor(weeklyFeedback.status),
                      fontSize: "12px",
                      fontWeight: "bold",
                      letterSpacing: "0",
                      textTransform: "uppercase",
                    }}
                  >
                    Feedback semanal
                  </div>
                  <h3 style={{ marginTop: "6px", marginBottom: 0 }}>{weeklyFeedback.title}</h3>
                  <p style={{ margin: "8px 0 0", color: "#cbd5e1" }}>{weeklyFeedback.summary}</p>
                </div>
                <span
                  style={{
                    color: getWeeklyFeedbackStatusColor(weeklyFeedback.status),
                    fontSize: "12px",
                    fontWeight: "bold",
                    whiteSpace: "nowrap",
                  }}
                >
                  {getWeeklyFeedbackStatusLabel(weeklyFeedback.status)}
                </span>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                  gap: "10px",
                  marginTop: "14px",
                }}
              >
                <div>
                  <strong>{weeklyFeedback.signals?.recent_session_count || 0}</strong>
                  <p style={{ margin: "3px 0 0", color: "#94a3b8", fontSize: "13px" }}>treinos recentes</p>
                </div>
                <div>
                  <strong>{weeklyFeedback.signals?.recent_failure_count || 0}</strong>
                  <p style={{ margin: "3px 0 0", color: "#94a3b8", fontSize: "13px" }}>falhas recentes</p>
                </div>
                <div>
                  <strong>{weeklyFeedback.signals?.watchlist_count || 0}</strong>
                  <p style={{ margin: "3px 0 0", color: "#94a3b8", fontSize: "13px" }}>exercícios a vigiar</p>
                </div>
                <div>
                  <strong>
                    {weeklyFeedback.signals?.volume_trend?.change_percent > 0 ? "+" : ""}
                    {weeklyFeedback.signals?.volume_trend?.change_percent || 0}%
                  </strong>
                  <p style={{ margin: "3px 0 0", color: "#94a3b8", fontSize: "13px" }}>tendência volume</p>
                </div>
              </div>

              <div style={{ display: "grid", gap: "8px", marginTop: "14px" }}>
                {(weeklyFeedback.feedback || []).map((item) => (
                  <p key={item} style={{ margin: 0, color: "#cbd5e1", fontSize: "13px" }}>
                    {item}
                  </p>
                ))}
              </div>

              {weeklyFeedback.deload?.recommended && (
                <div
                  style={{
                    marginTop: "14px",
                    padding: "12px",
                    border: "1px solid rgba(251, 191, 36, 0.35)",
                    borderRadius: "8px",
                    background: "rgba(120, 53, 15, 0.28)",
                  }}
                >
                  <strong style={{ color: "#fde68a" }}>Protocolo de deload sugerido</strong>
                  <p style={{ margin: "6px 0 0", color: "#fef3c7", fontSize: "13px" }}>
                    {weeklyFeedback.deload.duration} · volume a {Math.round((weeklyFeedback.deload.volume_multiplier || 0) * 100)}% · RIR alvo {weeklyFeedback.deload.target_rir}+
                  </p>
                  <div style={{ display: "grid", gap: "4px", marginTop: "8px" }}>
                    {(weeklyFeedback.deload.protocol || []).map((item) => (
                      <p key={item} style={{ margin: 0, color: "#fde68a", fontSize: "12px" }}>
                        {item}
                      </p>
                    ))}
                  </div>
                  {weeklyFeedback.deload.reasons?.length > 0 && (
                    <p style={{ margin: "8px 0 0", color: "#fbbf24", fontSize: "12px" }}>
                      Motivo: {weeklyFeedback.deload.reasons.join(", ")}
                    </p>
                  )}
                </div>
              )}
            </section>
          )}

          {adaptivePlan && (
            <section
              style={{
                marginTop: "16px",
                padding: "16px",
                border: "1px solid #334155",
                borderRadius: "8px",
                background: "rgba(20, 83, 45, 0.28)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  gap: "12px",
                  alignItems: "flex-start",
                }}
              >
                <div>
                  <div
                    style={{
                      color: "#86efac",
                      fontSize: "12px",
                      fontWeight: "bold",
                      letterSpacing: "0",
                      textTransform: "uppercase",
                    }}
                  >
                    Plano adaptativo
                  </div>
                  <h3 style={{ marginTop: "6px", marginBottom: 0 }}>Ajustes sugeridos</h3>
                </div>
                <span style={{ color: "#bbf7d0", fontSize: "12px", fontWeight: "bold" }}>
                  {adaptivePlan.summary?.high_priority_count || 0} prioridade alta
                </span>
              </div>

              <div style={{ display: "grid", gap: "10px", marginTop: "12px" }}>
                {(adaptivePlan.recommendations || [])
                  .filter((recommendation) => recommendation.action !== "maintain_plan")
                  .slice(0, 6)
                  .map((recommendation) => (
                    <div
                      key={recommendation.training_exercise}
                      style={{
                        padding: "12px",
                        border: "1px solid rgba(134, 239, 172, 0.2)",
                        borderRadius: "8px",
                        background: "rgba(15, 23, 42, 0.38)",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          gap: "12px",
                          alignItems: "flex-start",
                        }}
                      >
                        <div>
                          <strong>{recommendation.exercise_name}</strong>
                          <p style={{ margin: "4px 0 0", color: "#cbd5e1", fontSize: "13px" }}>
                            {recommendation.workout_name}
                          </p>
                        </div>
                        <span
                          style={{
                            color: getAdaptiveActionColor(recommendation.action),
                            fontSize: "12px",
                            fontWeight: "bold",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {getAdaptiveActionLabel(recommendation.action)}
                        </span>
                      </div>
                      <p style={{ margin: "8px 0 0", color: "#e5e7eb" }}>
                        {recommendation.message}
                      </p>
                      <p style={{ margin: "6px 0 0", color: "#94a3b8", fontSize: "13px" }}>
                        Séries: {recommendation.current_sets} → {recommendation.recommended_sets} | RIR: {recommendation.current_target_rir} → {recommendation.recommended_target_rir} | carga {recommendation.load_adjustment > 0 ? "+" : ""}{recommendation.load_adjustment}kg
                      </p>
                      {recommendation.evidence?.length > 0 && (
                        <div style={{ display: "grid", gap: "3px", marginTop: "8px" }}>
                          {recommendation.evidence.map((item) => (
                            <p key={item} style={{ margin: 0, color: "#94a3b8", fontSize: "12px" }}>
                              {item}
                            </p>
                          ))}
                        </div>
                      )}
                      <div
                        style={{
                          display: "flex",
                          flexWrap: "wrap",
                          gap: "8px",
                          marginTop: "12px",
                        }}
                      >
                        <button
                          type="button"
                          onClick={() => recordAdaptiveDecision(recommendation, "APPLIED")}
                          disabled={Boolean(applyingAdaptiveById[recommendation.training_exercise])}
                          style={{
                            padding: "8px 10px",
                            border: "1px solid #86efac",
                            borderRadius: "6px",
                            background: "#166534",
                            color: "#f0fdf4",
                            cursor: "pointer",
                          }}
                        >
                          {applyingAdaptiveById[recommendation.training_exercise] ? "A aplicar..." : "Aplicar"}
                        </button>
                        <button
                          type="button"
                          onClick={() => recordAdaptiveDecision(recommendation, "DEFERRED")}
                          disabled={Boolean(applyingAdaptiveById[recommendation.training_exercise])}
                          style={{
                            padding: "8px 10px",
                            border: "1px solid #475569",
                            borderRadius: "6px",
                            background: "rgba(15, 23, 42, 0.8)",
                            color: "#e2e8f0",
                            cursor: "pointer",
                          }}
                        >
                          Adiar
                        </button>
                        <button
                          type="button"
                          onClick={() => recordAdaptiveDecision(recommendation, "IGNORED")}
                          disabled={Boolean(applyingAdaptiveById[recommendation.training_exercise])}
                          style={{
                            padding: "8px 10px",
                            border: "1px solid #475569",
                            borderRadius: "6px",
                            background: "rgba(15, 23, 42, 0.8)",
                            color: "#cbd5e1",
                            cursor: "pointer",
                          }}
                        >
                          Ignorar
                        </button>
                      </div>
                    </div>
                  ))}
                {(adaptivePlan.recommendations || []).filter((recommendation) => recommendation.action !== "maintain_plan").length === 0 && (
                  <p style={{ margin: 0, color: "#94a3b8" }}>
                    Sem ajustes adaptativos por agora. Mantém o plano e continua a recolher dados.
                  </p>
                )}
              </div>

              {adaptiveDecisions.length > 0 && (
                <div style={{ marginTop: "16px" }}>
                  <strong style={{ color: "#bbf7d0", fontSize: "13px" }}>Últimas decisões</strong>
                  <div style={{ display: "grid", gap: "8px", marginTop: "8px" }}>
                    {adaptiveDecisions.slice(0, 5).map((decision) => (
                      <div
                        key={decision.id}
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          gap: "10px",
                          padding: "10px",
                          border: "1px solid rgba(148, 163, 184, 0.18)",
                          borderRadius: "6px",
                          background: "rgba(15, 23, 42, 0.32)",
                        }}
                      >
                        <div>
                          <strong style={{ fontSize: "13px" }}>{decision.exercise_name}</strong>
                          <p style={{ margin: "3px 0 0", color: "#94a3b8", fontSize: "12px" }}>
                            {getAdaptiveActionLabel(decision.action)} · Séries {decision.current_sets} → {decision.recommended_sets} · RIR {decision.current_target_rir} → {decision.recommended_target_rir} · carga {decision.load_adjustment > 0 ? "+" : ""}{decision.load_adjustment}kg
                          </p>
                        </div>
                        <span style={{ color: "#e2e8f0", fontSize: "12px", whiteSpace: "nowrap" }}>
                          {getAdaptiveDecisionStatusLabel(decision.status)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </section>
          )}

          {latestWorkoutProgression && (
            <section
              style={{
                marginTop: "16px",
                padding: "16px",
                border: "1px solid #334155",
                borderRadius: "8px",
                background: "rgba(15, 23, 42, 0.72)",
              }}
            >
              <div
                style={{
                  color: "#94a3b8",
                  fontSize: "12px",
                  fontWeight: "bold",
                  letterSpacing: "0",
                  textTransform: "uppercase",
                }}
              >
                Próximo treino
              </div>
              <h3 style={{ marginTop: "6px", marginBottom: "12px" }}>
                Progressão para {latestWorkoutProgression.workout_name}
              </h3>

              <div style={{ display: "grid", gap: "10px" }}>
                {latestWorkoutProgression.recommendations.map((recommendation) => (
                  <div
                    key={recommendation.training_exercise}
                    style={{
                      padding: "12px",
                      border: "1px solid rgba(148, 163, 184, 0.26)",
                      borderRadius: "8px",
                      background: "rgba(15, 23, 42, 0.44)",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        gap: "12px",
                        alignItems: "flex-start",
                      }}
                    >
                      <strong>{recommendation.exercise_name}</strong>
                      <span
                        style={{
                          color: "#38bdf8",
                          fontSize: "13px",
                          fontWeight: "bold",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {getProgressionActionLabel(recommendation.action)}
                      </span>
                    </div>
                    <p style={{ marginTop: "6px", color: "#e5e7eb" }}>
                      {formatProgressionTarget(recommendation)}
                    </p>
                    <p style={{ marginTop: "6px", color: "#94a3b8", fontSize: "13px" }}>
                      {recommendation.message}
                    </p>
                    <div
                      style={{
                        display: "flex",
                        flexWrap: "wrap",
                        gap: "8px",
                        marginTop: "10px",
                        fontSize: "12px",
                        fontWeight: "bold",
                      }}
                    >
                      <span style={{ color: "#bae6fd" }}>
                        {getDecisionSourceLabel(recommendation.source)}
                      </span>
                      {recommendation.confidence && (
                        <span style={{ color: getConfidenceColor(recommendation.confidence) }}>
                          Confiança {recommendation.confidence}
                        </span>
                      )}
                    </div>
                    {recommendation.decision_basis?.length > 0 && (
                      <div style={{ display: "grid", gap: "4px", marginTop: "8px" }}>
                        {recommendation.decision_basis.map((basis) => (
                          <p key={basis} style={{ margin: 0, color: "#cbd5e1", fontSize: "12px" }}>
                            {basis}
                          </p>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          <AiCoachSummaryPanel
            summary={latestAiCoach}
            getSourceLabel={getAiCoachSourceLabel}
          />

          {program.workouts.map((workout) => {
            const activeWorkoutId = getActiveWorkoutId();
            const activeSessionId = activeSessionByWorkout[workout.id];
            const isActiveWorkout = activeWorkoutId === String(workout.id);
            const hasActiveWorkout = Boolean(activeWorkoutId);
            const isWorkoutOpen = isActiveWorkout || openWorkoutId === workout.id;
            const workoutStats = getWorkoutSessionStats(workout);

            if (hasActiveWorkout && !isActiveWorkout) {
              return null;
            }

            return (
              <div
                key={workout.id}
                style={{ border: "1px solid #ccc", padding: "16px", marginTop: "16px" }}
              >
                <button
                  onClick={() => toggleWorkout(workout.id)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    padding: "12px",
                    fontSize: "18px",
                    fontWeight: "bold",
                    cursor: hasActiveWorkout ? "default" : "pointer",
                    background: "transparent",
                    border: "none",
                  }}
                >
                  {isWorkoutOpen ? "▼" : "▶"} Day {workout.order} - {workout.name}
                </button>

                {isWorkoutOpen && (
                  <div style={{ marginTop: "12px" }}>
                    {!activeSessionId ? (
                      <button onClick={() => startWorkoutSession(workout)}>
                        Start Workout
                      </button>
                    ) : (
                      <div style={{ marginBottom: "16px" }}>
                        <p style={{ color: "green" }}>Workout session active. Session ID: {activeSessionId}</p>
                        <div
                          style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                            gap: "12px",
                            marginTop: "12px",
                          }}
                        >
                          <div>
                            <strong>Volume</strong>
                            <p>{workoutStats.volume.toFixed(1)} kg</p>
                          </div>
                          <div>
                            <strong>Séries concluídas</strong>
                            <p>{workoutStats.sets}</p>
                          </div>
                        </div>

                        <textarea
                          placeholder="Final workout notes"
                          value={sessionNotes[workout.id] || ""}
                          onChange={(e) =>
                            setSessionNotes({
                              ...sessionNotes,
                              [workout.id]: e.target.value,
                            })
                          }
                          style={{ display: "block", width: "100%", marginTop: "8px" }}
                        />

                        <button onClick={() => finishWorkoutSession(workout)} style={{ marginTop: "8px" }}>
                          Finish Workout
                        </button>
                      </div>
                    )}

                    {activeSessionId && workout.exercises.map((item) => {
                      const exerciseLogs = getExerciseLogs(item.id);
                      const isOpen = Boolean(openExerciseById[item.id]);
                      const isSubstitutionOpen = Boolean(openSubstitutionByExerciseId[item.id]);
                      const isWeightScaleOpen = Boolean(openWeightScaleByExerciseId[item.id]);
                      const substitutionData = substitutionOptionsByExerciseId[item.id];
                      const weightScaleForm = getWeightScaleForm(item);
                      const calibrationState = getCalibrationState(item);
                      const calibrationForm = getCalibrationForm(item);
                      const needsCalibration = exerciseNeedsCalibration(item);
                      const calibrationCompletedToday = Boolean(completedCalibrationByExerciseId[item.id]);
                      const blocksNormalTraining = needsCalibration || calibrationCompletedToday;
                      const hasLoggedSets = exerciseLogs.current_sets.length > 0;
                      const isReplacing = Boolean(isReplacingExerciseById[item.id]);
                      const isSavingWeightScale = Boolean(isSavingWeightScaleByExerciseId[item.id]);
                      const isSavingCalibration = Boolean(isSavingCalibrationByExerciseId[item.id]);
                      const restSeconds = restTimers[item.id] || 0;
                      const calibrationInputsLocked = !calibrationState.scale_configured || restSeconds > 0 || isSavingCalibration;
                      const rows = getExerciseRows(item);
                      const guidance = getGuidanceForExercise(item, rows, restSeconds);

                      return (
                        <div
                          key={item.id}
                          style={{
                            borderBottom: "1px solid #ddd",
                            padding: "14px 0",
                          }}
                        >
                          <div className="exercise-row-shell">
                            <button
                              className="exercise-main-button"
                              onClick={() => toggleExercise(item)}
                            >
                              <img
                                className="exercise-row-image"
                                src={getExerciseImageUrl(item)}
                                alt={item.exercise_localized_name || item.exercise_name}
                              />
                              <span className="exercise-row-copy">
                                <span className="exercise-row-title">
                                  <span aria-hidden="true">{isOpen ? "▼" : "▶"}</span>
                                  {item.exercise_name}
                                </span>
                                <span className="exercise-row-meta">
                                  {item.exercise_localized_name || item.exercise_muscle_group}
                                  {" · "}
                                  {item.exercise_muscle_group}
                                  {" · "}
                                  {item.exercise_equipment}
                                  {needsCalibration ? " · Calibração necessária" : ""}
                                </span>
                              </span>
                            </button>

                            <button
                              className="exercise-replace-button"
                              onClick={() => toggleExerciseSubstitutions(item)}
                              disabled={hasLoggedSets || isReplacing}
                              title={hasLoggedSets ? "Termina este exercício antes de trocar." : "Trocar por outro exercício do mesmo grupo muscular"}
                            >
                              {isReplacing ? "A trocar..." : "Trocar"}
                            </button>

                            <button
                              className="exercise-scale-button"
                              onClick={() => toggleWeightScaleMenu(item)}
                              disabled={isSavingWeightScale}
                              title="Configurar placas e bolachas desta máquina"
                            >
                              Escala
                            </button>
                          </div>

                          <ExerciseWeightScalePanel
                            exercise={item}
                            isOpen={isWeightScaleOpen}
                            form={weightScaleForm}
                            isSaving={isSavingWeightScale}
                            updateWeightScaleForm={updateWeightScaleForm}
                            updateMicroWeightScaleRow={updateMicroWeightScaleRow}
                            addMicroWeightScaleRow={addMicroWeightScaleRow}
                            removeMicroWeightScaleRow={removeMicroWeightScaleRow}
                            saveWeightScale={saveWeightScale}
                          />

                          {isSubstitutionOpen && !hasLoggedSets && (
                            <div className="exercise-substitution-panel">
                              <div className="exercise-substitution-header">
                                <strong>Alternativas para {item.exercise_muscle_group}</strong>
                                <span>Só aparecem exercícios do mesmo grupo muscular.</span>
                              </div>

                              {!substitutionData && (
                                <p className="exercise-substitution-empty">A carregar alternativas...</p>
                              )}

                              {substitutionData?.options?.length === 0 && (
                                <p className="exercise-substitution-empty">
                                  Ainda não existem alternativas registadas para este grupo.
                                </p>
                              )}

                              <div className="exercise-option-grid">
                                {substitutionData?.options?.map((option) => (
                                  <button
                                    key={option.id}
                                    className="exercise-option-card"
                                    onClick={() => replaceExercise(item, option.id)}
                                    disabled={isReplacing}
                                  >
                                    <img
                                      src={option.image_url || "/exercise-screens/IMG_3620.PNG"}
                                      alt={option.localized_name || option.name}
                                    />
                                    <span>
                                      <strong>{option.name}</strong>
                                      <small>{option.localized_name || option.equipment}</small>
                                      <small>{option.equipment} · {option.movement_pattern}</small>
                                    </span>
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}

                          {isOpen && (
                            <div style={{ marginTop: "12px" }}>
                              <p>
                                Target: {item.sets} sets | {TARGET_REPS} reps | RIR {item.target_rir}
                              </p>

                              <ExerciseCalibrationPanel
                                exercise={item}
                                needsCalibration={needsCalibration}
                                calibrationCompletedToday={calibrationCompletedToday}
                                calibrationState={calibrationState}
                                calibrationForm={calibrationForm}
                                calibrationInputsLocked={calibrationInputsLocked}
                                restSeconds={restSeconds}
                                isSavingCalibration={isSavingCalibration}
                                colorOptions={getCalibrationColorOptions()}
                                getColorMeta={getCalibrationColorMeta}
                                formatTimer={formatTimer}
                                toggleWeightScaleMenu={toggleWeightScaleMenu}
                                updateCalibrationForm={updateCalibrationForm}
                                saveExerciseCalibration={saveExerciseCalibration}
                              />

                              {!blocksNormalTraining && exerciseLogs.previous_session && (
                                <p style={{ marginTop: "8px", color: "#777" }}>
                                  Anterior: {exerciseLogs.previous_session.workout_name}
                                </p>
                              )}

                              <div
                                style={{
                                  display: blocksNormalTraining ? "none" : "block",
                                  marginTop: "12px",
                                  padding: "16px",
                                  border: "1px solid #334155",
                                  borderRadius: "8px",
                                  background: "rgba(15, 23, 42, 0.78)",
                                }}
                              >
                                <div
                                  style={{
                                    color: guidance.isResting ? "#0ea5e9" : "#94a3b8",
                                    fontSize: "12px",
                                    fontWeight: "bold",
                                    letterSpacing: "0",
                                    textTransform: "uppercase",
                                  }}
                                >
                                  {guidance.eyebrow}
                                </div>
                                <strong
                                  style={{
                                    display: "block",
                                    marginTop: "6px",
                                    color: "#f8fafc",
                                    fontSize: "18px",
                                  }}
                                >
                                  {guidance.title}
                                </strong>
                                <p style={{ marginTop: "6px", color: "#cbd5e1" }}>{guidance.message}</p>

                                {guidance.reason && !guidance.isResting && (
                                  <p style={{ marginTop: "6px", color: "#94a3b8", fontSize: "13px" }}>
                                    {guidance.reason}
                                  </p>
                                )}

                                {guidance.source && !guidance.isResting && (
                                  <div
                                    style={{
                                      display: "flex",
                                      flexWrap: "wrap",
                                      gap: "8px",
                                      marginTop: "10px",
                                      fontSize: "12px",
                                      fontWeight: "bold",
                                    }}
                                  >
                                    <span style={{ color: "#bae6fd" }}>
                                      {getDecisionSourceLabel(guidance.source)}
                                    </span>
                                    {guidance.llmStatus && (
                                      <span style={{ color: guidance.llmStatus === "llm_enabled" ? "#86efac" : "#fbbf24" }}>
                                        {getLlmStatusLabel(guidance.llmStatus)}
                                      </span>
                                    )}
                                    {guidance.confidence && (
                                      <span style={{ color: getConfidenceColor(guidance.confidence) }}>
                                        Confiança {guidance.confidence}
                                      </span>
                                    )}
                                    {guidance.guardrailApplied && (
                                      <span title={guidance.guardrailReason} style={{ color: "#fbbf24" }}>
                                        Guardrail aplicado
                                      </span>
                                    )}
                                  </div>
                                )}

                                {guidance.decisionBasis?.length > 0 && !guidance.isResting && (
                                  <div style={{ display: "grid", gap: "4px", marginTop: "8px" }}>
                                    {guidance.decisionBasis.map((basis) => (
                                      <p key={basis} style={{ margin: 0, color: "#cbd5e1", fontSize: "12px" }}>
                                        {basis}
                                      </p>
                                    ))}
                                  </div>
                                )}

                                {guidance.isResting && (
                                  <div style={{ marginTop: "14px" }}>
                                    <div
                                      style={{
                                        color: "#0ea5e9",
                                        fontSize: "42px",
                                        fontWeight: "bold",
                                        lineHeight: "1",
                                      }}
                                    >
                                      {formatTimer(restSeconds)}
                                    </div>
                                    <div
                                      style={{
                                        display: "grid",
                                        gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                                        gap: "8px",
                                        marginTop: "12px",
                                      }}
                                    >
                                      <button type="button" onClick={() => adjustRestTimer(item.id, -15)}>
                                        -15s
                                      </button>
                                      <button type="button" onClick={() => adjustRestTimer(item.id, 15)}>
                                        +15s
                                      </button>
                                    </div>
                                  </div>
                                )}
                              </div>

                              <ExerciseSetTable
                                exercise={item}
                                rows={rows}
                                blocksNormalTraining={blocksNormalTraining}
                                setForms={setForms}
                                setTypes={SET_TYPES}
                                warmupEffort={WARMUP_EFFORT}
                                openRestMenuBySet={openRestMenuBySet}
                                openSetTypeMenuBySet={openSetTypeMenuBySet}
                                openCompletionMenuBySet={openCompletionMenuBySet}
                                getSetFormKey={getSetFormKey}
                                getCurrentSetForRow={getCurrentSetForRow}
                                getSetTypeForExerciseRow={getSetTypeForExerciseRow}
                                getPreviousSetForExerciseRow={getPreviousSetForExerciseRow}
                                getSetTypeMeta={getSetTypeMeta}
                                getVisibleSetLabel={getVisibleSetLabel}
                                getEffortMetaFromSet={getEffortMetaFromSet}
                                getRestSecondsForRow={getRestSecondsForRow}
                                getPlannedValuesForExerciseRow={getPlannedValuesForExerciseRow}
                                getEffortOptionsForSet={getEffortOptionsForSet}
                                formatPreviousSet={formatPreviousSet}
                                formatTimer={formatTimer}
                                updateSetForm={updateSetForm}
                                toggleRestMenu={toggleRestMenu}
                                toggleSetTypeMenu={toggleSetTypeMenu}
                                toggleCompletionMenu={toggleCompletionMenu}
                                selectSetType={selectSetType}
                                removeExerciseRow={removeExerciseRow}
                                saveSet={saveSet}
                                undoSet={undoSet}
                              />

                              {!blocksNormalTraining && (
                                <button onClick={() => addExerciseRow(item)} style={{ marginTop: "12px", width: "100%" }}>
                                  + Adicionar Série
                                </button>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default App;
