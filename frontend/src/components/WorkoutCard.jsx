// =============================================================================
// WorkoutCard.jsx
// -----------------------------------------------------------------------------
// Componente visual de cada treino dentro do programa.
// É usado pelo App.jsx para renderizar workouts, controlar abertura, iniciar/finalizar sessões e listar exercícios.
// Distribui estado, helpers e ações para ExerciseCard mantendo a estrutura do treino organizada.
// =============================================================================
import ActiveWorkoutSummary from "./ActiveWorkoutSummary";
import ExerciseCard from "./ExerciseCard";

export default function WorkoutCard({
  workout,
  activeWorkoutId,
  activeSessionId,
  hasActiveWorkout,
  isWorkoutOpen,
  workoutStats,
  sessionNote,
  setSessionNote,
  constants,
  experimentalMode = false,
  state,
  helpers,
  actions,
}) {
  const isActiveWorkout = activeWorkoutId === String(workout.id);

  if (hasActiveWorkout && !isActiveWorkout) {
    return null;
  }

  return (
    <div className="workout-card">
      <button
        onClick={() => actions.toggleWorkout(workout.id)}
        className="workout-toggle-button"
        style={{ cursor: hasActiveWorkout ? "default" : "pointer" }}
      >
        {isWorkoutOpen ? "▼" : "▶"} Day {workout.order} - {workout.name}
      </button>

      {isWorkoutOpen && (
        <div className="workout-card-body">
          {!activeSessionId ? (
            <button onClick={() => actions.startWorkoutSession(workout)}>
              Start Workout
            </button>
          ) : (
            <ActiveWorkoutSummary
              activeSessionId={activeSessionId}
              workout={workout}
              workoutStats={workoutStats}
              sessionNote={sessionNote}
              setSessionNote={setSessionNote}
              finishWorkoutSession={actions.finishWorkoutSession}
            />
          )}

          {activeSessionId && workout.exercises.map((exercise) => {
            const exerciseLogs = helpers.getExerciseLogs(exercise.id);
            const isOpen = Boolean(state.openExerciseById[exercise.id]);
            const isSubstitutionOpen = Boolean(state.openSubstitutionByExerciseId[exercise.id]);
            const isWeightScaleOpen = Boolean(state.openWeightScaleByExerciseId[exercise.id]);
            const substitutionData = state.substitutionOptionsByExerciseId[exercise.id];
            const weightScaleForm = helpers.getWeightScaleForm(exercise);
            const calibrationState = helpers.getCalibrationState(exercise);
            const calibrationForm = helpers.getCalibrationForm(exercise);
            const needsCalibration = helpers.exerciseNeedsCalibration(exercise);
            const calibrationCompletedToday = Boolean(state.completedCalibrationByExerciseId[exercise.id]);
            const blocksNormalTraining = needsCalibration || calibrationCompletedToday;
            const hasLoggedSets = exerciseLogs.current_sets.length > 0;
            const isReplacing = Boolean(state.isReplacingExerciseById[exercise.id]);
            const isSavingWeightScale = Boolean(state.isSavingWeightScaleByExerciseId[exercise.id]);
            const isSavingCalibration = Boolean(state.isSavingCalibrationByExerciseId[exercise.id]);
            const restSeconds = state.restTimers[exercise.id] || 0;
            const calibrationInputsLocked =
              !calibrationState.scale_configured || restSeconds > 0 || isSavingCalibration;
            const rows = helpers.getExerciseRows(exercise);
            const guidance = helpers.getGuidanceForExercise(exercise, rows, restSeconds);

            return (
              <ExerciseCard
                key={exercise.id}
                exercise={exercise}
                exerciseLogs={exerciseLogs}
                isOpen={isOpen}
                isSubstitutionOpen={isSubstitutionOpen}
                isWeightScaleOpen={isWeightScaleOpen}
                substitutionData={substitutionData}
                weightScaleForm={weightScaleForm}
                calibrationState={calibrationState}
                calibrationForm={calibrationForm}
                needsCalibration={needsCalibration}
                calibrationCompletedToday={calibrationCompletedToday}
                blocksNormalTraining={blocksNormalTraining}
                hasLoggedSets={hasLoggedSets}
                isReplacing={isReplacing}
                isSavingWeightScale={isSavingWeightScale}
                isSavingCalibration={isSavingCalibration}
                restSeconds={restSeconds}
                calibrationInputsLocked={calibrationInputsLocked}
                rows={rows}
                guidance={guidance}
                constants={constants}
                experimentalMode={experimentalMode}
                setForms={state.setForms}
                menus={{
                  openRestMenuBySet: state.openRestMenuBySet,
                  openSetTypeMenuBySet: state.openSetTypeMenuBySet,
                  openCompletionMenuBySet: state.openCompletionMenuBySet,
                }}
                imageUrl={helpers.getExerciseImageUrl(exercise)}
                colorOptions={helpers.getCalibrationColorOptions()}
                toggleExercise={actions.toggleExercise}
                toggleExerciseSubstitutions={actions.toggleExerciseSubstitutions}
                toggleWeightScaleMenu={actions.toggleWeightScaleMenu}
                replaceExercise={actions.replaceExercise}
                updateWeightScaleForm={actions.updateWeightScaleForm}
                updateMicroWeightScaleRow={actions.updateMicroWeightScaleRow}
                addMicroWeightScaleRow={actions.addMicroWeightScaleRow}
                removeMicroWeightScaleRow={actions.removeMicroWeightScaleRow}
                saveWeightScale={actions.saveWeightScale}
                getColorMeta={helpers.getCalibrationColorMeta}
                formatTimer={helpers.formatTimer}
                updateCalibrationForm={actions.updateCalibrationForm}
                saveExerciseCalibration={actions.saveExerciseCalibration}
                getDecisionSourceLabel={helpers.getDecisionSourceLabel}
                getLlmStatusLabel={helpers.getLlmStatusLabel}
                getConfidenceColor={helpers.getConfidenceColor}
                adjustRestTimer={actions.adjustRestTimer}
                setTableHandlers={actions.setTableHandlers}
                addExerciseRow={actions.addExerciseRow}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
