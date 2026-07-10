export default function ExerciseCalibrationPanel({
  exercise,
  needsCalibration,
  calibrationCompletedToday,
  calibrationState,
  calibrationForm,
  calibrationInputsLocked,
  restSeconds,
  isSavingCalibration,
  colorOptions,
  getColorMeta,
  formatTimer,
  toggleWeightScaleMenu,
  updateCalibrationForm,
  saveExerciseCalibration,
}) {
  if (needsCalibration) {
    const selectedColorMeta = getColorMeta(calibrationForm.result_color);

    return (
      <div className="exercise-calibration-panel">
        <div className="exercise-substitution-header">
          <strong>Treino experimental obrigatório</strong>
          <span>
            Série {calibrationState.next_step?.set_number || 1} de{" "}
            {calibrationState.protocol?.target_sets || 3}
          </span>
        </div>

        <p className="exercise-calibration-copy">
          O objetivo não é treinar: é descobrir o peso que leva à falha técnica perto da rep 12.
          Faz 3 séries até ao máximo possível com técnica limpa; a app ajusta a carga a cada série.
        </p>

        {!calibrationState.scale_configured && (
          <div className="exercise-calibration-warning">
            <span>Preenche primeiro a escala da máquina para a IA saber os saltos reais disponíveis.</span>
            <button type="button" onClick={() => toggleWeightScaleMenu(exercise)}>
              Abrir escala
            </button>
          </div>
        )}

        {calibrationState.calibration_sets?.length > 0 && (
          <div className="exercise-calibration-history">
            {calibrationState.calibration_sets.map((setLog, index) => {
              const colorMeta = getColorMeta(setLog.result_color || setLog.reps_completed);

              return (
                <span
                  key={`${setLog.weight_used}-${index}`}
                  style={{
                    borderColor: colorMeta?.border,
                    background: colorMeta?.background,
                    color: colorMeta?.color,
                  }}
                >
                  S{index + 1}: {setLog.weight_used}kg · {colorMeta?.label || "resultado registado"}
                </span>
              );
            })}
          </div>
        )}

        {calibrationState.next_step && (
          <p className="exercise-calibration-estimate">
            Próxima série experimental:{" "}
            {calibrationState.next_step.recommended_weight
              ? `${calibrationState.next_step.recommended_weight}kg`
              : "preencher escala"}{" "}
            · até falha técnica
            <br />
            {calibrationState.next_step.message}
          </p>
        )}

        {restSeconds > 0 && (
          <div className="exercise-calibration-warning">
            <span>Descanso obrigatório antes da próxima série experimental.</span>
            <strong>{formatTimer(restSeconds)}</strong>
          </div>
        )}

        <div className="exercise-calibration-grid">
          <label className="profile-field">
            <span>Peso usado</span>
            <input
              type="number"
              step="0.5"
              value={calibrationForm.weight_used}
              disabled={calibrationInputsLocked}
              onChange={(event) =>
                updateCalibrationForm(exercise, "weight_used", event.target.value)
              }
            />
          </label>
        </div>

        <div className="exercise-calibration-color-scale">
          {colorOptions.map((colorOption) => (
            <button
              key={colorOption.key}
              type="button"
              disabled={calibrationInputsLocked}
              className={`exercise-calibration-color-chip ${colorOption.key} ${
                calibrationForm.result_color === colorOption.key ? "selected" : ""
              }`}
              onClick={() =>
                updateCalibrationForm(exercise, "result_color", colorOption.key)
              }
            >
              <strong>{colorOption.label}</strong>
              {colorOption.text}
            </button>
          ))}
        </div>

        {selectedColorMeta && (
          <p
            className="exercise-calibration-estimate"
            style={{
              borderColor: selectedColorMeta.border,
              background: selectedColorMeta.background,
              color: selectedColorMeta.color,
            }}
          >
            Resultado: {selectedColorMeta.label} · {selectedColorMeta.text}
          </p>
        )}

        <label className="profile-field">
          <span>Notas da calibração</span>
          <input
            value={calibrationForm.notes}
            disabled={calibrationInputsLocked}
            onChange={(event) =>
              updateCalibrationForm(exercise, "notes", event.target.value)
            }
            placeholder="Ex: técnica fácil, máquina pesada, amplitude controlada"
          />
        </label>

        {calibrationState.estimated_working_weight && (
          <p className="exercise-calibration-estimate">
            Peso estimado atual: {calibrationState.estimated_working_weight}kg · confiança{" "}
            {calibrationState.confidence}
          </p>
        )}

        <button
          type="button"
          className="exercise-scale-save-button"
          onClick={() => saveExerciseCalibration(exercise)}
          disabled={calibrationInputsLocked}
        >
          {!calibrationState.scale_configured
            ? "Preenche a escala primeiro"
            : restSeconds > 0
              ? `Aguarda ${formatTimer(restSeconds)}`
              : isSavingCalibration
                ? "A guardar..."
                : "Guardar série experimental"}
        </button>
      </div>
    );
  }

  if (!calibrationCompletedToday) {
    return null;
  }

  return (
    <div className="exercise-calibration-panel">
      <div className="exercise-substitution-header">
        <strong>Máquina concluída por hoje</strong>
        <span>Treino experimental fechado</span>
      </div>
      <p className="exercise-calibration-copy">
        Já temos os dados necessários desta máquina. Hoje não há séries normais aqui;
        segue para a próxima máquina do treino.
      </p>
      {calibrationState.estimated_working_weight && (
        <p className="exercise-calibration-estimate">
          Peso padrão estimado para o próximo treino: {calibrationState.estimated_working_weight}kg.
        </p>
      )}
    </div>
  );
}
