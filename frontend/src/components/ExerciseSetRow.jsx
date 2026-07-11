// =============================================================================
// ExerciseSetRow.jsx
// -----------------------------------------------------------------------------
// Componente visual de uma linha da tabela de séries.
// É usado pelo ExerciseSetTable para renderizar uma série de aquecimento,
// trabalho ou drop, incluindo inputs, menus, estado concluído e esforço registado.
// Mantém a tabela mais legível e concentra a interação de cada linha.
// =============================================================================
import { EffortMenu, RestMenu, SetTypeMenu } from "./ExerciseSetMenus";

export default function ExerciseSetRow({
  exercise,
  rows,
  sourceSetNumber,
  displaySetNumber,
  setForms,
  setTypes,
  warmupEffort,
  openRestMenuBySet,
  openSetTypeMenuBySet,
  openCompletionMenuBySet,
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
}) {
  const setFormKey = getSetFormKey(exercise.id, sourceSetNumber);
  const currentSet = getCurrentSetForRow(exercise.id, displaySetNumber);
  const rowForm = setForms[setFormKey] || {};
  const rowSetType = getSetTypeForExerciseRow(
    exercise,
    sourceSetNumber,
    displaySetNumber
  );
  const previousSet = getPreviousSetForExerciseRow(
    exercise,
    rows,
    sourceSetNumber,
    displaySetNumber
  );
  const setTypeMeta = getSetTypeMeta(rowSetType);
  const visibleSetLabel = getVisibleSetLabel(
    exercise,
    rows,
    sourceSetNumber,
    displaySetNumber
  );
  const isCompleted = Boolean(currentSet);
  const effortMeta = getEffortMetaFromSet(currentSet);
  const restSecondsForRow = getRestSecondsForRow(setFormKey);
  const plannedValues = getPlannedValuesForExerciseRow(
    exercise,
    rows,
    sourceSetNumber,
    displaySetNumber
  );
  const weightValue = currentSet?.weight_used ?? rowForm.weight_used ?? plannedValues.weight;
  const repsValue = currentSet?.reps_completed ?? rowForm.reps_completed ?? plannedValues.reps;
  const availableEffortOptions = getEffortOptionsForSet(rowSetType, repsValue);

  return (
    <tr className={displaySetNumber % 2 === 0 ? "striped" : ""}>
      <td>
        <div className="exercise-set-controls">
          <div className="exercise-set-menu-anchor">
            <button
              type="button"
              className="exercise-row-icon-button"
              disabled={isCompleted}
              onClick={() => toggleRestMenu(setFormKey)}
              title="Configurar descanso"
            >
              ...
            </button>

            {openRestMenuBySet[setFormKey] && !isCompleted && (
              <RestMenu
                exercise={exercise}
                sourceSetNumber={sourceSetNumber}
                displaySetNumber={displaySetNumber}
                restSecondsForRow={restSecondsForRow}
                formatTimer={formatTimer}
                updateSetForm={updateSetForm}
                removeExerciseRow={removeExerciseRow}
              />
            )}
          </div>

          <div className="exercise-set-menu-anchor">
            <button
              type="button"
              className="exercise-set-type-button"
              disabled={isCompleted}
              onClick={() => toggleSetTypeMenu(setFormKey)}
              title="Alterar tipo de série"
              style={{ color: setTypeMeta.color }}
            >
              {visibleSetLabel}
            </button>

            {openSetTypeMenuBySet[setFormKey] && !isCompleted && (
              <SetTypeMenu
                setTypes={setTypes}
                rowSetType={rowSetType}
                selectSetType={selectSetType}
                setFormKey={setFormKey}
              />
            )}
          </div>
        </div>
      </td>
      <td className="previous-set-cell">{formatPreviousSet(previousSet)}</td>
      <td>
        <input
          type="number"
          step="0.1"
          value={weightValue}
          disabled={isCompleted}
          onChange={(event) => updateSetForm(setFormKey, "weight_used", event.target.value)}
        />
      </td>
      <td>
        <input
          type="number"
          value={repsValue}
          disabled={isCompleted}
          onChange={(event) => updateSetForm(setFormKey, "reps_completed", event.target.value)}
        />
      </td>
      <td className="completed-set-cell">
        <div className="exercise-set-menu-anchor inline">
          <button
            type="button"
            className={`exercise-check-button ${isCompleted ? "completed" : ""}`}
            title={isCompleted ? "Desfazer série" : "Guardar série"}
            onClick={() => {
              if (isCompleted) {
                undoSet(exercise, sourceSetNumber, displaySetNumber);
                return;
              }

              if (rowSetType === "WARMUP") {
                saveSet(exercise, sourceSetNumber, displaySetNumber, warmupEffort);
              } else {
                toggleCompletionMenu(setFormKey);
              }
            }}
          >
            ✓
          </button>

          {effortMeta && (
            <span className="effort-chip" style={{ color: effortMeta.color }}>
              {effortMeta.label}
            </span>
          )}

          {openCompletionMenuBySet[setFormKey] && !isCompleted && rowSetType !== "WARMUP" && (
            <EffortMenu
              availableEffortOptions={availableEffortOptions}
              saveSet={saveSet}
              exercise={exercise}
              sourceSetNumber={sourceSetNumber}
              displaySetNumber={displaySetNumber}
            />
          )}
        </div>
      </td>
    </tr>
  );
}
