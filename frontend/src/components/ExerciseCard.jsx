// =============================================================================
// ExerciseCard.jsx
// -----------------------------------------------------------------------------
// Componente visual de um exercício dentro de um workout.
// É usado pelo WorkoutCard para mostrar imagem, dados do exercício, escala, substituição, calibração, orientação do coach e tabela de séries.
// Recebe estado, helpers e ações do App.jsx para manter a lógica centralizada.
// =============================================================================
import ExerciseCalibrationPanel from "./ExerciseCalibrationPanel";
import ExerciseGuidanceCard from "./ExerciseGuidanceCard";
import ExerciseHeader from "./ExerciseHeader";
import ExerciseSetTable from "./ExerciseSetTable";
import ExerciseSubstitutionPanel from "./ExerciseSubstitutionPanel";
import ExerciseWeightScalePanel from "./ExerciseWeightScalePanel";

export default function ExerciseCard({
  exercise,
  exerciseLogs,
  isOpen,
  isSubstitutionOpen,
  isWeightScaleOpen,
  substitutionData,
  weightScaleForm,
  calibrationState,
  calibrationForm,
  needsCalibration,
  calibrationCompletedToday,
  blocksNormalTraining,
  hasLoggedSets,
  isReplacing,
  isSavingWeightScale,
  isSavingCalibration,
  restSeconds,
  calibrationInputsLocked,
  rows,
  guidance,
  constants,
  setForms,
  menus,
  imageUrl,
  colorOptions,
  toggleExercise,
  toggleExerciseSubstitutions,
  toggleWeightScaleMenu,
  replaceExercise,
  updateWeightScaleForm,
  updateMicroWeightScaleRow,
  addMicroWeightScaleRow,
  removeMicroWeightScaleRow,
  saveWeightScale,
  getColorMeta,
  formatTimer,
  updateCalibrationForm,
  saveExerciseCalibration,
  getDecisionSourceLabel,
  getLlmStatusLabel,
  getConfidenceColor,
  adjustRestTimer,
  setTableHandlers,
  addExerciseRow,
}) {
  const { targetReps, setTypes, warmupEffort } = constants;

  return (
    <div className="exercise-card">
      <ExerciseHeader
        exercise={exercise}
        imageUrl={imageUrl}
        isOpen={isOpen}
        needsCalibration={needsCalibration}
        hasLoggedSets={hasLoggedSets}
        isReplacing={isReplacing}
        isSavingWeightScale={isSavingWeightScale}
        toggleExercise={toggleExercise}
        toggleExerciseSubstitutions={toggleExerciseSubstitutions}
        toggleWeightScaleMenu={toggleWeightScaleMenu}
      />

      <ExerciseWeightScalePanel
        exercise={exercise}
        isOpen={isWeightScaleOpen}
        form={weightScaleForm}
        isSaving={isSavingWeightScale}
        updateWeightScaleForm={updateWeightScaleForm}
        updateMicroWeightScaleRow={updateMicroWeightScaleRow}
        addMicroWeightScaleRow={addMicroWeightScaleRow}
        removeMicroWeightScaleRow={removeMicroWeightScaleRow}
        saveWeightScale={saveWeightScale}
      />

      <ExerciseSubstitutionPanel
        exercise={exercise}
        isOpen={isSubstitutionOpen}
        hasLoggedSets={hasLoggedSets}
        substitutionData={substitutionData}
        isReplacing={isReplacing}
        replaceExercise={replaceExercise}
      />

      {isOpen && (
        <div className="exercise-card-body">
          <p>
            Target: {exercise.sets} sets | {targetReps} reps | RIR {exercise.target_rir}
          </p>

          <ExerciseCalibrationPanel
            exercise={exercise}
            needsCalibration={needsCalibration}
            calibrationCompletedToday={calibrationCompletedToday}
            calibrationState={calibrationState}
            calibrationForm={calibrationForm}
            calibrationInputsLocked={calibrationInputsLocked}
            restSeconds={restSeconds}
            isSavingCalibration={isSavingCalibration}
            colorOptions={colorOptions}
            getColorMeta={getColorMeta}
            formatTimer={formatTimer}
            toggleWeightScaleMenu={toggleWeightScaleMenu}
            updateCalibrationForm={updateCalibrationForm}
            saveExerciseCalibration={saveExerciseCalibration}
          />

          {!blocksNormalTraining && exerciseLogs.previous_session && (
            <p className="previous-session-note">
              Anterior: {exerciseLogs.previous_session.workout_name}
            </p>
          )}

          {!blocksNormalTraining && (
            <ExerciseGuidanceCard
              exercise={exercise}
              guidance={guidance}
              restSeconds={restSeconds}
              formatTimer={formatTimer}
              adjustRestTimer={adjustRestTimer}
              getDecisionSourceLabel={getDecisionSourceLabel}
              getLlmStatusLabel={getLlmStatusLabel}
              getConfidenceColor={getConfidenceColor}
            />
          )}

          <ExerciseSetTable
            exercise={exercise}
            rows={rows}
            blocksNormalTraining={blocksNormalTraining}
            setForms={setForms}
            setTypes={setTypes}
            warmupEffort={warmupEffort}
            openRestMenuBySet={menus.openRestMenuBySet}
            openSetTypeMenuBySet={menus.openSetTypeMenuBySet}
            openCompletionMenuBySet={menus.openCompletionMenuBySet}
            {...setTableHandlers}
          />

          {!blocksNormalTraining && (
            <button onClick={() => addExerciseRow(exercise)} className="add-set-button">
              + Adicionar Série
            </button>
          )}
        </div>
      )}
    </div>
  );
}
