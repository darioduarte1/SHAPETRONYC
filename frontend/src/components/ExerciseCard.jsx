// =============================================================================
// ExerciseCard.jsx
// -----------------------------------------------------------------------------
// Componente visual de um exercício dentro de um workout.
// É usado pelo WorkoutCard para mostrar imagem, dados do exercício, escala, substituição, calibração, orientação do coach e tabela de séries.
// Recebe estado, helpers e ações do App.jsx para manter a lógica centralizada.
// =============================================================================
import ExerciseCalibrationPanel from "./ExerciseCalibrationPanel";
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
      <div className="exercise-row-shell">
        <button
          className="exercise-main-button"
          onClick={() => toggleExercise(exercise)}
        >
          <img
            className="exercise-row-image"
            src={imageUrl}
            alt={exercise.exercise_localized_name || exercise.exercise_name}
          />
          <span className="exercise-row-copy">
            <span className="exercise-row-title">
              <span aria-hidden="true">{isOpen ? "▼" : "▶"}</span>
              {exercise.exercise_name}
            </span>
            <span className="exercise-row-meta">
              {exercise.exercise_localized_name || exercise.exercise_muscle_group}
              {" · "}
              {exercise.exercise_muscle_group}
              {" · "}
              {exercise.exercise_equipment}
              {needsCalibration ? " · Calibração necessária" : ""}
            </span>
          </span>
        </button>

        <button
          className="exercise-replace-button"
          onClick={() => toggleExerciseSubstitutions(exercise)}
          disabled={hasLoggedSets || isReplacing}
          title={hasLoggedSets ? "Termina este exercício antes de trocar." : "Trocar por outro exercício do mesmo grupo muscular"}
        >
          {isReplacing ? "A trocar..." : "Trocar"}
        </button>

        <button
          className="exercise-scale-button"
          onClick={() => toggleWeightScaleMenu(exercise)}
          disabled={isSavingWeightScale}
          title="Configurar placas e bolachas desta máquina"
        >
          Escala
        </button>
      </div>

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

          <div className="exercise-guidance-card" hidden={blocksNormalTraining}>
            <div
              className="exercise-guidance-eyebrow"
              style={{ color: guidance.isResting ? "#0ea5e9" : "#94a3b8" }}
            >
              {guidance.eyebrow}
            </div>
            <strong>{guidance.title}</strong>
            <p>{guidance.message}</p>

            {guidance.reason && !guidance.isResting && (
              <p className="exercise-guidance-reason">{guidance.reason}</p>
            )}

            {guidance.source && !guidance.isResting && (
              <div className="exercise-guidance-meta">
                <span>{getDecisionSourceLabel(guidance.source)}</span>
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
              <div className="exercise-guidance-basis">
                {guidance.decisionBasis.map((basis) => (
                  <p key={basis}>{basis}</p>
                ))}
              </div>
            )}

            {guidance.isResting && (
              <div className="exercise-rest-card">
                <div>{formatTimer(restSeconds)}</div>
                <div>
                  <button type="button" onClick={() => adjustRestTimer(exercise.id, -15)}>
                    -15s
                  </button>
                  <button type="button" onClick={() => adjustRestTimer(exercise.id, 15)}>
                    +15s
                  </button>
                </div>
              </div>
            )}
          </div>

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
