// =============================================================================
// ExerciseSetTable.jsx
// -----------------------------------------------------------------------------
// Componente visual da tabela de séries de um exercício.
// É usado pelo ExerciseCard para listar aquecimentos e séries normais, permitir editar carga/reps/esforço e marcar/desmarcar séries feitas.
// Não decide a progressão; dispara ações recebidas por props para guardar ou desfazer séries.
// =============================================================================
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
            const weightValue =
              currentSet?.weight_used ?? rowForm.weight_used ?? plannedValues.weight;
            const repsValue =
              currentSet?.reps_completed ??
              rowForm.reps_completed ??
              plannedValues.reps;
            const availableEffortOptions = getEffortOptionsForSet(rowSetType, repsValue);

            return (
              <tr
                key={sourceSetNumber}
                className={displaySetNumber % 2 === 0 ? "striped" : ""}
              >
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
                        <div className="exercise-row-popover rest">
                          <label>Descanso após série</label>
                          <input
                            type="number"
                            min="15"
                            step="15"
                            value={restSecondsForRow}
                            onChange={(event) =>
                              updateSetForm(setFormKey, "rest_seconds", event.target.value)
                            }
                          />
                          <div className="exercise-rest-preset-grid">
                            {[60, 90, 120, 180].map((seconds) => (
                              <button
                                key={seconds}
                                type="button"
                                onClick={() => updateSetForm(setFormKey, "rest_seconds", seconds)}
                              >
                                {formatTimer(seconds)}
                              </button>
                            ))}
                          </div>

                          <button
                            type="button"
                            className="exercise-remove-set-button"
                            onClick={() => removeExerciseRow(exercise, sourceSetNumber, displaySetNumber)}
                          >
                            Remover série
                          </button>
                        </div>
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
                        <div className="exercise-row-popover set-type">
                          {setTypes.map((setType) => (
                            <button
                              key={setType.value}
                              type="button"
                              className={rowSetType === setType.value ? "selected" : ""}
                              onClick={() => selectSetType(setFormKey, setType.value)}
                            >
                              <span style={{ color: setType.color }}>{setType.shortLabel}</span>
                              {setType.label}
                            </button>
                          ))}
                        </div>
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
                      <div className="exercise-row-popover effort">
                        {availableEffortOptions.map((option) => (
                          <button
                            key={option.value}
                            type="button"
                            style={{ color: option.color }}
                            onClick={() => saveSet(exercise, sourceSetNumber, displaySetNumber, option)}
                          >
                            {option.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
