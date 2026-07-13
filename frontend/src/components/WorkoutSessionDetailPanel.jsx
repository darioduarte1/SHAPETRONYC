// =============================================================================
// WorkoutSessionDetailPanel.jsx
// -----------------------------------------------------------------------------
// Componente visual do detalhe de um treino antigo.
// É usado pelo dashboard para abrir uma sessão concluída e mostrar feedback
// guardado do coach, métricas, exercícios, séries, cargas, reps, RIR e calibração.
// Mantém o histórico consultável sem misturar detalhe denso no resumo do dashboard.
// =============================================================================
import AiCoachSummaryPanel from "./AiCoachSummaryPanel";

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

export default function WorkoutSessionDetailPanel({
  session,
  formatDate,
  formatNumber,
}) {
  return (
    <div className="session-detail-panel">
      <div className="session-detail-heading">
        <div>
          <strong>{session.workout_name}</strong>
          <p>{formatDate(session.completed_at)}</p>
        </div>
        <div className="session-detail-metrics">
          <span>{formatNumber(session.volume)} kg</span>
          <span>{session.sets || 0} série(s)</span>
          <span>{session.failure_count || 0} falha(s)</span>
        </div>
      </div>

      {session.coach_feedback && (
        <AiCoachSummaryPanel
          summary={session.coach_feedback}
          getSourceLabel={(status) => status || "histórico"}
          compact
        />
      )}

      <div className="session-exercise-list">
        {(session.exercises || []).map((exercise) => (
          <div key={`${session.id}-${exercise.exercise_id}`} className="session-exercise-card">
            <div className="session-exercise-heading">
              <strong>{exercise.exercise_name}</strong>
              <span>
                {exercise.target_min_reps === exercise.target_max_reps
                  ? `${exercise.target_max_reps || 12} reps`
                  : `${exercise.target_min_reps || 10}-${exercise.target_max_reps || 12} reps`}
                {exercise.target_rir !== null && exercise.target_rir !== undefined
                  ? ` · RIR ${exercise.target_rir}`
                  : ""}
              </span>
            </div>

            {exercise.calibration && (
              <div className="session-calibration-summary">
                <span>
                  Calibração: {formatNumber(exercise.calibration.estimated_working_weight)} kg
                </span>
                <span>Confiança {exercise.calibration.confidence}</span>
              </div>
            )}

            <div className="session-set-list">
              {[...(exercise.calibration?.sets || []), ...(exercise.sets || [])].map((setLog) => (
                <div key={`${exercise.exercise_id}-${setLog.set_type}-${setLog.id}`} className="session-set-row">
                  <span>{getSetTypeLabel(setLog.set_type)} {setLog.set_number}</span>
                  <span>{formatWeight(setLog.weight_used, formatNumber)}</span>
                  <span>{formatValue(setLog.reps_completed, " reps")}</span>
                  <span>
                    {setLog.set_type === "WARMUP" || setLog.set_type === "CALIBRATION"
                      ? "-"
                      : setLog.reached_failure
                        ? "Falha"
                        : `RIR ${formatValue(setLog.rir)}`}
                  </span>
                </div>
              ))}
              {!(exercise.sets || []).length && !(exercise.calibration?.sets || []).length && (
                <p className="muted-text no-margin">Sem séries registadas neste exercício.</p>
              )}
            </div>
          </div>
        ))}
        {session.exercises?.length === 0 && (
          <p className="muted-text no-margin">Sem detalhe de exercícios nesta sessão.</p>
        )}
      </div>
    </div>
  );
}
