// =============================================================================
// ExerciseSetTable.jsx
// -----------------------------------------------------------------------------
// Componente visual da tabela de séries de um exercício.
// É usado pelo ExerciseCard para listar aquecimentos e séries normais, permitir editar carga/reps/esforço e marcar/desmarcar séries feitas.
// Não decide a progressão; dispara ações recebidas por props para guardar ou desfazer séries.
// =============================================================================
import ExerciseSetRow from "./ExerciseSetRow";

export default function ExerciseSetTable({
  exercise,
  rows,
  blocksNormalTraining,
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
  if (blocksNormalTraining) {
    return null;
  }

  return (
    <div className="exercise-set-table-wrap">
      <table className="exercise-set-table">
        <thead>
          <tr>
            <th>Série</th>
            <th>Anterior</th>
            <th>Kg</th>
            <th>Reps</th>
            <th>Feita</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(({ sourceSetNumber, displaySetNumber }) => {
            return (
              <ExerciseSetRow
                key={sourceSetNumber}
                exercise={exercise}
                rows={rows}
                sourceSetNumber={sourceSetNumber}
                displaySetNumber={displaySetNumber}
                setForms={setForms}
                setTypes={setTypes}
                warmupEffort={warmupEffort}
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
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
