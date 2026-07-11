// =============================================================================
// ProgramScreen.jsx
// -----------------------------------------------------------------------------
// Ecrã principal do programa de treino depois de o atleta ter plano criado.
// É usado pelo App.jsx para renderizar dashboard, bloco, feedback, plano
// adaptativo, progressão, resumo da IA e todos os workouts do programa.
// Mantém o ecrã operacional do treino fora do componente principal da app.
// =============================================================================
import AdaptivePlanPanel from "./AdaptivePlanPanel";
import AiCoachSummaryPanel from "./AiCoachSummaryPanel";
import AthleteDashboardPanel from "./AthleteDashboardPanel";
import ProgramHeader from "./ProgramHeader";
import TrainingBlockPanel from "./TrainingBlockPanel";
import WeeklyFeedbackPanel from "./WeeklyFeedbackPanel";
import WorkoutCard from "./WorkoutCard";
import WorkoutProgressionPanel from "./WorkoutProgressionPanel";
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
} from "../utils/trainingFormatters";
import {
  SET_TYPES,
  TARGET_REPS,
  WARMUP_EFFORT,
} from "../utils/trainingConstants";

export default function ProgramScreen({
  program,
  athleteDashboard,
  trainingBlock,
  weeklyFeedback,
  adaptivePlan,
  adaptiveDecisions,
  applyingAdaptiveById,
  latestWorkoutProgression,
  latestAiCoach,
  activeSessionByWorkout,
  sessionNotes,
  openWorkoutId,
  setSessionNotes,
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
  exportUserTrainingData,
  recordAdaptiveDecision,
  getActiveWorkoutId,
  getWorkoutSessionStats,
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
  setTableHandlers,
}) {
  return (
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
              setTableHandlers,
            }}
          />
        );
      })}
    </div>
  );
}
