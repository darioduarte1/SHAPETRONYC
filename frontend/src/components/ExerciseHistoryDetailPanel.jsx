// =============================================================================
// ExerciseHistoryDetailPanel.jsx
// -----------------------------------------------------------------------------
// Componente visual do histórico detalhado de um exercício.
// É usado no dashboard do atleta para abrir um exercício específico e consultar
// calibração, evolução da carga, últimas séries, falhas e tendência atual.
// Ajuda a tornar visível a memória da app por máquina/exercício.
// =============================================================================
function formatValue(value, suffix = "") {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return `${value}${suffix}`;
}

function formatWeight(value, formatNumber) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  return `${formatNumber(value)} kg`;
}

function getSetTypeLabel(setType) {
  const labels = {
    WARMUP: "Aquecimento",
    WORKING: "Normal",
    DROP: "Drop",
    CALIBRATION: "Experimental",
  };

  return labels[setType] || setType;
}

export default function ExerciseHistoryDetailPanel({
  exercise,
  formatDate,
  formatNumber,
  getConfidenceColor,
}) {
  const calibration = exercise.calibration;
  const trendClass = exercise.status?.status === "watch" ? "warning" : exercise.status?.status;
  const sets = [
    ...(calibration?.sets || []),
    ...(exercise.latest_sets || []),
  ];

  return (
    <div className="exercise-history-detail-panel">
      <div className="exercise-history-summary">
        <div>
          <strong>{exercise.status?.label || "Histórico"}</strong>
          <p>{exercise.status?.summary || "Ainda há poucos dados para avaliar este exercício."}</p>
        </div>
        <span className={`exercise-history-status ${trendClass || "stable"}`}>
          {exercise.status?.label || "Estável"}
        </span>
      </div>

      <div className="exercise-history-metrics">
        <span>{exercise.sessions || 0} treino(s)</span>
        <span>{exercise.working_sets || 0} série(s) normais</span>
        <span>{formatWeight(exercise.latest_working_weight, formatNumber)}</span>
        <span>
          {Number(exercise.load_change || 0) > 0 ? "+" : ""}
          {formatNumber(exercise.load_change)} kg
        </span>
      </div>

      {calibration && (
        <div className="exercise-history-calibration">
          <div>
            <strong>Peso calibrado</strong>
            <p>
              {formatWeight(calibration.estimated_working_weight, formatNumber)} · {calibration.set_count} série(s)
              {calibration.updated_at ? ` · ${formatDate(calibration.updated_at)}` : ""}
            </p>
          </div>
          <span style={{ color: getConfidenceColor(calibration.confidence) }}>
            Confiança {calibration.confidence}
          </span>
        </div>
      )}

      <div className="exercise-history-set-list">
        {sets.map((setLog) => (
          <div key={`${exercise.exercise_id}-${setLog.set_type}-${setLog.id}`} className="exercise-history-set-row">
            <span>{getSetTypeLabel(setLog.set_type)} {setLog.set_number}</span>
            <span>{formatWeight(setLog.weight_used, formatNumber)}</span>
            <span>{formatValue(setLog.reps_completed, " reps")}</span>
            <span>
              {setLog.set_type === "WARMUP" || setLog.set_type === "CALIBRATION"
                ? setLog.result_color || "-"
                : setLog.reached_failure
                  ? "Falha"
                  : `RIR ${formatValue(setLog.rir)}`}
            </span>
          </div>
        ))}
        {sets.length === 0 && (
          <p className="muted-text no-margin">Ainda sem séries registadas neste exercício.</p>
        )}
      </div>
    </div>
  );
}
