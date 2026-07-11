// =============================================================================
// App.jsx
// -----------------------------------------------------------------------------
// Componente principal da interface React.
// Controla o fluxo da app: criação/login do atleta, geração do programa, dashboard, treino ativo, calibração, escalas e comunicação com a API.
// Mantém grande parte do estado global do frontend e passa dados/funções para os componentes especializados.
// =============================================================================
import { useState } from "react";
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
import useCoachContext from "./hooks/useCoachContext";
import useExerciseCalibration from "./hooks/useExerciseCalibration";
import useExerciseGuidance from "./hooks/useExerciseGuidance";
import useExerciseHistory from "./hooks/useExerciseHistory";
import useExerciseSetRows from "./hooks/useExerciseSetRows";
import useExerciseSubstitutions from "./hooks/useExerciseSubstitutions";
import useProfileAccess from "./hooks/useProfileAccess";
import useProgramData from "./hooks/useProgramData";
import useRestTimers from "./hooks/useRestTimers";
import useSetControls from "./hooks/useSetControls";
import useSetLogging from "./hooks/useSetLogging";
import useTrainingSession from "./hooks/useTrainingSession";
import useWeightScales from "./hooks/useWeightScales";
import useWorkoutExerciseActions from "./hooks/useWorkoutExerciseActions";
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
import {
  SET_TYPES,
  TARGET_REPS,
  WARMUP_EFFORT,
} from "./utils/trainingConstants";

function App() {
  const [step, setStep] = useState(1);
  const [profileId, setProfileId] = useState(null);
  const [userId, setUserId] = useState(null);
  const [recommendations, setRecommendations] = useState({});
  const [openExerciseById, setOpenExerciseById] = useState({});

  const {
    restTimers,
    setRestTimers,
    formatTimer,
    adjustRestTimer,
  } = useRestTimers();

  const {
    setForms,
    setSetForms,
    openCompletionMenuBySet,
    setOpenCompletionMenuBySet,
    openRestMenuBySet,
    setOpenRestMenuBySet,
    openSetTypeMenuBySet,
    setOpenSetTypeMenuBySet,
    removedSetByKey,
    setRemovedSetByKey,
    updateSetForm,
    getRestSecondsForRow,
    toggleCompletionMenu,
    toggleRestMenu,
    toggleSetTypeMenu,
    selectSetType,
  } = useSetControls();

  function resetTrainingState() {
    setOpenWorkoutId(null);
    setRecommendations({});
    setExerciseLogsById({});
    setExerciseRowCounts({});
    setCalibrationFormsByExerciseId({});
    setCompletedCalibrationByExerciseId({});
    setRemovedSetByKey({});
    setOpenSetTypeMenuBySet({});
  }

  const {
    program,
    setProgram,
    programError,
    setProgramError,
    isGeneratingProgram,
    latestWorkoutProgression,
    setLatestWorkoutProgression,
    latestAiCoach,
    setLatestAiCoach,
    athleteDashboard,
    setAthleteDashboard,
    adaptivePlan,
    setAdaptivePlan,
    adaptiveDecisions,
    setAdaptiveDecisions,
    weeklyFeedback,
    setWeeklyFeedback,
    trainingBlock,
    setTrainingBlock,
    applyingAdaptiveById,
    setApplyingAdaptiveById,
    loadAthleteDashboard,
    loadAdaptivePlan,
    loadAdaptiveDecisions,
    loadWeeklyFeedback,
    loadTrainingBlock,
    loadProgramPanels,
    generateProgram,
    recordAdaptiveDecision,
  } = useProgramData({ profileId, setStep, resetTrainingState });

  function resetAllTrainingState() {
    resetTrainingState();
    setSetForms({});
  }

  function resetAllAppState() {
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
  }

  const {
    form,
    setForm,
    levelGuidance,
    goalLabels,
    loginUsername,
    setLoginUsername,
    loginError,
    isLoggingIn,
    isDeletingExperimentalUsers,
    deleteUsersMessage,
    handleChange,
    exportUserTrainingData,
    loginExistingProfile,
    createProfile,
    deleteExperimentalUsers,
  } = useProfileAccess({
    profileId,
    setProfileId,
    userId,
    setUserId,
    setStep,
    setProgram,
    setProgramError,
    setLatestWorkoutProgression,
    setLatestAiCoach,
    loadProgramPanels,
    resetAllTrainingState,
    resetAllAppState,
  });

  const {
    exerciseLogsById,
    setExerciseLogsById,
    exerciseRowCounts,
    setExerciseRowCounts,
    getExerciseLogs,
    loadExerciseHistory,
  } = useExerciseHistory({
    profileId,
    getActiveSessionByWorkout: () => activeSessionByWorkout,
  });

  const {
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
  } = useExerciseCalibration({
    profileId,
    restTimers,
    setRestTimers,
    getExerciseLogs,
    setExerciseLogsById,
    loadExerciseHistory,
  });

  const {
    substitutionOptionsByExerciseId,
    setSubstitutionOptionsByExerciseId,
    openSubstitutionByExerciseId,
    setOpenSubstitutionByExerciseId,
    isReplacingExerciseById,
    setIsReplacingExerciseById,
    toggleExerciseSubstitutions,
    replaceExercise,
  } = useExerciseSubstitutions({
    setProgram,
    setRecommendations,
    setExerciseLogsById,
    setOpenExerciseById,
    loadProgramPanels,
  });

  const {
    activeSessionByWorkout,
    setActiveSessionByWorkout,
    sessionNotes,
    setSessionNotes,
    openWorkoutId,
    setOpenWorkoutId,
    getActiveWorkoutId,
    toggleWorkout,
    startWorkoutSession,
    finishWorkoutSession,
  } = useTrainingSession({
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
  });

  const {
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
  } = useWeightScales({
    profileId,
    activeSessionByWorkout,
    setProgram,
    loadExerciseHistory,
  });

  const {
    getSetFormKey,
    getSetTypeMeta,
    getEffortMetaFromSet,
    getCurrentSetForRow,
    getPreviousSetForExerciseRow,
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
  } = useExerciseSetRows({
    exerciseRowCounts,
    setForms,
    removedSetByKey,
    getExerciseLogs,
  });

  const {
    buildUserCoachContext,
    buildExerciseCoachContext,
  } = useCoachContext({ userId, form });

  const {
    getGuidanceForExercise,
  } = useExerciseGuidance({
    recommendations,
    getCurrentSetForRow,
    getSetTypeForExerciseRow,
    getVisibleSetLabel,
    getPlannedValuesForExerciseRow,
    getWarmupReferenceSet,
    getExerciseTargetLabel,
  });

  const {
    getWorkoutSessionStats,
    toggleExercise,
    getExerciseImageUrl,
    addExerciseRow,
    removeExerciseRow,
  } = useWorkoutExerciseActions({
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
  });

  const {
    saveSet,
    undoSet,
  } = useSetLogging({
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
  });

  function exerciseNeedsCalibration(exercise) {
    return Boolean(getCalibrationState(exercise).needs_calibration);
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
