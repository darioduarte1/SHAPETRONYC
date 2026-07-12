// =============================================================================
// AiCoachSummaryPanel.jsx
// -----------------------------------------------------------------------------
// Componente visual que mostra o resumo textual do coach/IA.
// É usado no ecrã principal do programa para apresentar feedback geral gerado a partir dos dados recentes do atleta.
// Recebe a origem da decisão e o conteúdo já calculado, sem executar regras de treino.
// =============================================================================
function formatMetricValue(value, suffix = "") {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  if (typeof value === "number") {
    return `${Number(value).toFixed(Number.isInteger(value) ? 0 : 1)}${suffix}`;
  }

  return `${value}${suffix}`;
}

export default function AiCoachSummaryPanel({
  summary,
  getSourceLabel,
  compact = false,
}) {
  if (!summary) {
    return null;
  }

  return (
    <section className={`ai-coach-panel ${compact ? "compact" : ""}`}>
      <div className="panel-heading-row">
        <div>
          <div className="panel-kicker blue">AI Coach</div>
          <h3>{summary.headline}</h3>
        </div>
        <span className="panel-source">{getSourceLabel(summary.status)}</span>
      </div>

      <p className="ai-coach-summary">{summary.summary}</p>

      <div className="ai-coach-metrics">
        <div>
          <strong>Volume</strong>
          <p>{Number(summary.metrics?.total_volume || 0).toFixed(1)} kg</p>
        </div>
        <div>
          <strong>Séries</strong>
          <p>{summary.metrics?.total_sets || 0}</p>
        </div>
        <div>
          <strong>Falhas</strong>
          <p>{summary.metrics?.failure_count || 0}</p>
        </div>
      </div>

      <div className="ai-coach-focus-list">
        {summary.focus_points?.map((point) => (
          <p key={point}>{point}</p>
        ))}
      </div>

      {summary.exercise_feedback?.length > 0 && (
        <div className="ai-coach-exercise-list">
          {summary.exercise_feedback.map((item) => (
            <div key={`${item.exercise_name}-${item.title}`} className="ai-coach-exercise-card">
              <div className="ai-coach-exercise-heading">
                <strong>{item.title}</strong>
                {item.status?.label && (
                  <span className={`ai-coach-status ${item.status.tone || "muted"}`}>
                    {item.status.label}
                  </span>
                )}
              </div>
              <p>{item.message}</p>
              <div className="ai-coach-exercise-metrics">
                <span>{formatMetricValue(item.metrics?.volume, "kg")} volume</span>
                <span>{formatMetricValue(item.metrics?.working_sets)} série(s)</span>
                <span>{formatMetricValue(item.metrics?.average_rir)} RIR médio</span>
                <span>{formatMetricValue(item.metrics?.failures)} falha(s)</span>
              </div>
              {item.next_step && (
                <p className="ai-coach-exercise-next">{item.next_step}</p>
              )}
              {item.reason && (
                <p className="ai-coach-exercise-reason">{item.reason}</p>
              )}
            </div>
          ))}
        </div>
      )}

      <p className="ai-coach-next">{summary.next_session_strategy}</p>
      <p className="ai-coach-recovery">{summary.recovery_note}</p>
    </section>
  );
}
