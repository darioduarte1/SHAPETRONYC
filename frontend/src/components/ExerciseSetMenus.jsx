// =============================================================================
// ExerciseSetMenus.jsx
// -----------------------------------------------------------------------------
// Componentes auxiliares dos menus da tabela de séries.
// São usados pelo ExerciseSetRow para configurar descanso, remover linhas,
// escolher tipo de série e selecionar o esforço/RIR antes de guardar.
// Mantêm os popovers da tabela concentrados num ficheiro próprio.
// =============================================================================

export function RestMenu({
  exercise,
  sourceSetNumber,
  displaySetNumber,
  restSecondsForRow,
  formatTimer,
  updateSetForm,
  removeExerciseRow,
}) {
  const setFormKey = `${exercise.id}-${sourceSetNumber}`;

  return (
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
  );
}

export function SetTypeMenu({ setTypes, rowSetType, selectSetType, setFormKey }) {
  return (
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
  );
}

export function EffortMenu({ availableEffortOptions, saveSet, exercise, sourceSetNumber, displaySetNumber }) {
  return (
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
  );
}
