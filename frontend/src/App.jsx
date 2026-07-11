// =============================================================================
// App.jsx
// -----------------------------------------------------------------------------
// Componente principal da interface React.
// Controla o fluxo da app: criação/login do atleta, geração do programa, dashboard, treino ativo, calibração, escalas e comunicação com a API.
// Mantém grande parte do estado global do frontend e passa dados/funções para os componentes especializados.
// =============================================================================
import { useState } from "react";
import AppMessages from "./components/AppMessages";
import HomeScreen from "./components/HomeScreen";
import ProgramScreen from "./components/ProgramScreen";
import ProfileForm from "./components/ProfileForm";
import useAppMessages from "./hooks/useAppMessages";
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
import { EXPERIMENTAL_MODE } from "./utils/appConfig";

function App() {
  const [step, setStep] = useState(1);
  const [profileId, setProfileId] = useState(null);
  const [userId, setUserId] = useState(null);
  const [recommendations, setRecommendations] = useState({});
  const [openExerciseById, setOpenExerciseById] = useState({});
  const {
    messages,
    dismissMessage,
    notifyError,
    notifySuccess,
  } = useAppMessages();

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
    loadProgramPanels,
    generateProgram,
    recordAdaptiveDecision,
  } = useProgramData({ profileId, setStep, resetTrainingState, notifyError });

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
    notifyError,
    notifySuccess,
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
    notifyError,
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
    notifyError,
  });

  const {
    activeSessionByWorkout,
    setActiveSessionByWorkout,
    sessionNotes,
    setSessionNotes,
    openWorkoutId,
    setOpenWorkoutId,
    workoutStatusMessage,
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
    notifyError,
    notifySuccess,
  });

  const {
    openWeightScaleByExerciseId,
    setOpenWeightScaleByExerciseId,
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
    notifyError,
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
    notifyError,
  });

  function exerciseNeedsCalibration(exercise) {
    return Boolean(getCalibrationState(exercise).needs_calibration);
  }

  return (
    <div className={step === 1 ? "app-shell home-app-shell" : step === 2 ? "app-shell profile-app-shell" : "app-shell"}>
      <h1>SHAPETRONYC</h1>
      <AppMessages messages={messages} dismissMessage={dismissMessage} />

      {step === 1 && (
        <HomeScreen
          experimentalMode={EXPERIMENTAL_MODE}
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
        <ProgramScreen
          program={program}
          athleteDashboard={athleteDashboard}
          trainingBlock={trainingBlock}
          weeklyFeedback={weeklyFeedback}
          adaptivePlan={adaptivePlan}
          adaptiveDecisions={adaptiveDecisions}
          applyingAdaptiveById={applyingAdaptiveById}
          latestWorkoutProgression={latestWorkoutProgression}
          latestAiCoach={latestAiCoach}
          activeSessionByWorkout={activeSessionByWorkout}
          sessionNotes={sessionNotes}
          openWorkoutId={openWorkoutId}
          workoutStatusMessage={workoutStatusMessage}
          experimentalMode={EXPERIMENTAL_MODE}
          setSessionNotes={setSessionNotes}
          setForms={setForms}
          openExerciseById={openExerciseById}
          openSubstitutionByExerciseId={openSubstitutionByExerciseId}
          openWeightScaleByExerciseId={openWeightScaleByExerciseId}
          substitutionOptionsByExerciseId={substitutionOptionsByExerciseId}
          completedCalibrationByExerciseId={completedCalibrationByExerciseId}
          isReplacingExerciseById={isReplacingExerciseById}
          isSavingWeightScaleByExerciseId={isSavingWeightScaleByExerciseId}
          isSavingCalibrationByExerciseId={isSavingCalibrationByExerciseId}
          restTimers={restTimers}
          openRestMenuBySet={openRestMenuBySet}
          openSetTypeMenuBySet={openSetTypeMenuBySet}
          openCompletionMenuBySet={openCompletionMenuBySet}
          exportUserTrainingData={exportUserTrainingData}
          recordAdaptiveDecision={recordAdaptiveDecision}
          getActiveWorkoutId={getActiveWorkoutId}
          getWorkoutSessionStats={getWorkoutSessionStats}
          getExerciseLogs={getExerciseLogs}
          getWeightScaleForm={getWeightScaleForm}
          getCalibrationState={getCalibrationState}
          getCalibrationForm={getCalibrationForm}
          exerciseNeedsCalibration={exerciseNeedsCalibration}
          getExerciseRows={getExerciseRows}
          getGuidanceForExercise={getGuidanceForExercise}
          getExerciseImageUrl={getExerciseImageUrl}
          getCalibrationColorOptions={getCalibrationColorOptions}
          getCalibrationColorMeta={getCalibrationColorMeta}
          formatTimer={formatTimer}
          toggleWorkout={toggleWorkout}
          startWorkoutSession={startWorkoutSession}
          finishWorkoutSession={finishWorkoutSession}
          toggleExercise={toggleExercise}
          toggleExerciseSubstitutions={toggleExerciseSubstitutions}
          toggleWeightScaleMenu={toggleWeightScaleMenu}
          replaceExercise={replaceExercise}
          updateWeightScaleForm={updateWeightScaleForm}
          updateMicroWeightScaleRow={updateMicroWeightScaleRow}
          addMicroWeightScaleRow={addMicroWeightScaleRow}
          removeMicroWeightScaleRow={removeMicroWeightScaleRow}
          saveWeightScale={saveWeightScale}
          updateCalibrationForm={updateCalibrationForm}
          saveExerciseCalibration={saveExerciseCalibration}
          adjustRestTimer={adjustRestTimer}
          addExerciseRow={addExerciseRow}
          setTableHandlers={{
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
          }}
        />
      )}
    </div>
  );
}

export default App;
