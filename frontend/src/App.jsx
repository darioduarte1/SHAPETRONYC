import { useEffect, useState } from "react";
import AdaptivePlanPanel from "./components/AdaptivePlanPanel";
import AiCoachSummaryPanel from "./components/AiCoachSummaryPanel";
import AthleteDashboardPanel from "./components/AthleteDashboardPanel";
import HomeScreen from "./components/HomeScreen";
import ProgramHeader from "./components/ProgramHeader";
import ProfileForm from "./components/ProfileForm";
import TrainingBlockPanel from "./components/TrainingBlockPanel";
import WeeklyFeedbackPanel from "./components/WeeklyFeedbackPanel";
import WorkoutCard from "./components/WorkoutCard";
import WorkoutProgressionPanel from "./components/WorkoutProgressionPanel";
import {
  formatDashboardDate,
  formatNumber,
  formatProgressionTarget,
  getAdaptiveActionColor,
  getAdaptiveActionLabel,
  getAdaptiveDecisionStatusLabel,
  getAiCoachSourceLabel,
  getConfidenceColor,
  getDashboardMaxWeeklyVolume,
  getDecisionSourceLabel,
  getLlmStatusLabel,
  getProgressionActionLabel,
  getTrainingBlockPhaseColor,
  getTrainingBlockPhaseLabel,
  getWeeklyFeedbackStatusColor,
  getWeeklyFeedbackStatusLabel,
} from "./utils/trainingFormatters";

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
        <HomeScreen
          loginUsername={loginUsername}
          setLoginUsername={setLoginUsername}
          loginError={loginError}
          isLoggingIn={isLoggingIn}
          loginExistingProfile={loginExistingProfile}
          goToProfileSetup={() => setStep(2)}
          deleteExperimentalUsers={deleteExperimentalUsers}
          isDeletingExperimentalUsers={isDeletingExperimentalUsers}
          deleteUsersMessage={deleteUsersMessage}
        />
      )}

      {step === 2 && (
        <ProfileForm
          form={form}
          setForm={setForm}
          handleChange={handleChange}
          createProfile={createProfile}
          goalLabels={goalLabels}
          levelGuidance={levelGuidance}
        />
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
          <ProgramHeader
            programName={program.name}
            exportUserTrainingData={exportUserTrainingData}
          />

          <AthleteDashboardPanel
            dashboard={athleteDashboard}
            formatDate={formatDashboardDate}
            formatNumber={formatNumber}
            getConfidenceColor={getConfidenceColor}
            getMaxWeeklyVolume={getDashboardMaxWeeklyVolume}
          />

          <TrainingBlockPanel
            trainingBlock={trainingBlock}
            formatNumber={formatNumber}
            getPhaseLabel={getTrainingBlockPhaseLabel}
            getPhaseColor={getTrainingBlockPhaseColor}
          />

          <WeeklyFeedbackPanel
            feedback={weeklyFeedback}
            getStatusLabel={getWeeklyFeedbackStatusLabel}
            getStatusColor={getWeeklyFeedbackStatusColor}
          />

          <AdaptivePlanPanel
            adaptivePlan={adaptivePlan}
            adaptiveDecisions={adaptiveDecisions}
            applyingAdaptiveById={applyingAdaptiveById}
            getActionLabel={getAdaptiveActionLabel}
            getActionColor={getAdaptiveActionColor}
            getDecisionStatusLabel={getAdaptiveDecisionStatusLabel}
            recordAdaptiveDecision={recordAdaptiveDecision}
          />

          <WorkoutProgressionPanel
            progression={latestWorkoutProgression}
            getActionLabel={getProgressionActionLabel}
            getSourceLabel={getDecisionSourceLabel}
            getConfidenceColor={getConfidenceColor}
            formatTarget={formatProgressionTarget}
          />

          <AiCoachSummaryPanel
            summary={latestAiCoach}
            getSourceLabel={getAiCoachSourceLabel}
          />

          {program.workouts.map((workout) => {
            const activeWorkoutId = getActiveWorkoutId();
            const activeSessionId = activeSessionByWorkout[workout.id];
            const hasActiveWorkout = Boolean(activeWorkoutId);

            return (
              <WorkoutCard
                key={workout.id}
                workout={workout}
                activeWorkoutId={activeWorkoutId}
                activeSessionId={activeSessionId}
                hasActiveWorkout={hasActiveWorkout}
                isWorkoutOpen={activeWorkoutId === String(workout.id) || openWorkoutId === workout.id}
                workoutStats={getWorkoutSessionStats(workout)}
                sessionNote={sessionNotes[workout.id]}
                setSessionNote={(workoutId, value) =>
                  setSessionNotes({
                    ...sessionNotes,
                    [workoutId]: value,
                  })
                }
                constants={{ targetReps: TARGET_REPS, setTypes: SET_TYPES, warmupEffort: WARMUP_EFFORT }}
                state={{
                  setForms,
                  openExerciseById,
                  openSubstitutionByExerciseId,
                  openWeightScaleByExerciseId,
                  substitutionOptionsByExerciseId,
                  completedCalibrationByExerciseId,
                  isReplacingExerciseById,
                  isSavingWeightScaleByExerciseId,
                  isSavingCalibrationByExerciseId,
                  restTimers,
                  openRestMenuBySet,
                  openSetTypeMenuBySet,
                  openCompletionMenuBySet,
                }}
                helpers={{
                  getExerciseLogs,
                  getWeightScaleForm,
                  getCalibrationState,
                  getCalibrationForm,
                  exerciseNeedsCalibration,
                  getExerciseRows,
                  getGuidanceForExercise,
                  getExerciseImageUrl,
                  getCalibrationColorOptions,
                  getCalibrationColorMeta,
                  formatTimer,
                  getDecisionSourceLabel,
                  getLlmStatusLabel,
                  getConfidenceColor,
                }}
                actions={{
                  toggleWorkout,
                  startWorkoutSession,
                  finishWorkoutSession,
                  toggleExercise,
                  toggleExerciseSubstitutions,
                  toggleWeightScaleMenu,
                  replaceExercise,
                  updateWeightScaleForm,
                  updateMicroWeightScaleRow,
                  addMicroWeightScaleRow,
                  removeMicroWeightScaleRow,
                  saveWeightScale,
                  updateCalibrationForm,
                  saveExerciseCalibration,
                  adjustRestTimer,
                  addExerciseRow,
                  setTableHandlers: {
                    getSetFormKey,
                    getCurrentSetForRow,
                    getSetTypeForExerciseRow,
                    getPreviousSetForExerciseRow,
                    getSetTypeMeta,
                    getVisibleSetLabel,
                    getEffortMetaFromSet,
                    getRestSecondsForRow,
                    getPlannedValuesForExerciseRow,
                    getEffortOptionsForSet,
                    formatPreviousSet,
                    formatTimer,
                    updateSetForm,
                    toggleRestMenu,
                    toggleSetTypeMenu,
                    toggleCompletionMenu,
                    selectSetType,
                    removeExerciseRow,
                    saveSet,
                    undoSet,
                  },
                }}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}

export default App;
