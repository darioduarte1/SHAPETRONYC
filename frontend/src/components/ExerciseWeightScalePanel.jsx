// =============================================================================
// ExerciseWeightScalePanel.jsx
// -----------------------------------------------------------------------------
// Componente visual para registar a escala de pesos de uma máquina.
// É usado dentro do ExerciseCard e da calibração para garantir que a app conhece os pesos reais disponíveis.
// Permite preencher placas, bolachas e incrementos antes de a IA recomendar cargas.
// =============================================================================
export default function ExerciseWeightScalePanel({
  exercise,
  isOpen,
  form,
  isSaving,
  updateWeightScaleForm,
  updateMicroWeightScaleRow,
  addMicroWeightScaleRow,
  removeMicroWeightScaleRow,
  saveWeightScale,
}) {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="exercise-weight-scale-panel">
      <div className="exercise-substitution-header">
        <strong>Escala de pesos da máquina</strong>
        <span>Usada pela IA para recomendar cargas possíveis.</span>
      </div>

      <div className="exercise-weight-scale-grid">
        <label className="profile-field">
          <span>Placas principais</span>
          <input
            value={form.main_weight_options}
            onChange={(event) =>
              updateWeightScaleForm(exercise, "main_weight_options", event.target.value)
            }
            placeholder="4, 10, 12, 18, 24, 30"
          />
        </label>

        <div className="profile-field">
          <span>Bolachas / extras</span>
          <div className="exercise-micro-weight-list">
            {(form.micro_weight_options || []).map((microWeightRow, rowIndex) => (
              <div className="exercise-micro-weight-row" key={`${rowIndex}-${microWeightRow.weight}`}>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={microWeightRow.count}
                  onChange={(event) =>
                    updateMicroWeightScaleRow(exercise, rowIndex, "count", event.target.value)
                  }
                  placeholder="Qtd."
                />
                <input
                  type="text"
                  inputMode="decimal"
                  min="0"
                  value={microWeightRow.weight}
                  onChange={(event) =>
                    updateMicroWeightScaleRow(exercise, rowIndex, "weight", event.target.value)
                  }
                  placeholder="Kg"
                />
                <button
                  type="button"
                  className="exercise-micro-weight-remove"
                  onClick={() => removeMicroWeightScaleRow(exercise, rowIndex)}
                  title="Remover bolacha"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
          <button
            type="button"
            className="exercise-micro-weight-add"
            onClick={() => addMicroWeightScaleRow(exercise)}
          >
            + Adicionar bolacha
          </button>
        </div>
      </div>

      <button
        type="button"
        className="exercise-scale-save-button"
        onClick={() => saveWeightScale(exercise)}
        disabled={isSaving}
      >
        {isSaving ? "A guardar..." : "Guardar escala"}
      </button>
    </div>
  );
}
