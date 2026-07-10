// =============================================================================
// AiCoachSummaryPanel.jsx
// -----------------------------------------------------------------------------
// Componente visual que mostra o resumo textual do coach/IA.
// É usado no ecrã principal do programa para apresentar feedback geral gerado a partir dos dados recentes do atleta.
// Recebe a origem da decisão e o conteúdo já calculado, sem executar regras de treino.
// =============================================================================
export default function AiCoachSummaryPanel({
  summary,
  getSourceLabel,
}) {
  if (!summary) {
    return null;
  }

  return (
    <section className="ai-coach-panel">
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
              <strong>{item.title}</strong>
              <p>{item.message}</p>
            </div>
          ))}
        </div>
      )}

      <p className="ai-coach-next">{summary.next_session_strategy}</p>
      <p className="ai-coach-recovery">{summary.recovery_note}</p>
    </section>
  );
}
