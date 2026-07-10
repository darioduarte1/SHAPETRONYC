export default function WeeklyFeedbackPanel({
  feedback,
  getStatusLabel,
  getStatusColor,
}) {
  if (!feedback) {
    return null;
  }

  const statusColor = getStatusColor(feedback.status);

  return (
    <section className="weekly-feedback-panel">
      <div className="panel-heading-row">
        <div>
          <div className="panel-kicker" style={{ color: statusColor }}>
            Feedback semanal
          </div>
          <h3>{feedback.title}</h3>
          <p className="panel-copy">{feedback.summary}</p>
        </div>
        <span className="panel-source" style={{ color: statusColor }}>
          {getStatusLabel(feedback.status)}
        </span>
      </div>

      <div className="weekly-feedback-metrics">
        <div>
          <strong>{feedback.signals?.recent_session_count || 0}</strong>
          <p>treinos recentes</p>
        </div>
        <div>
          <strong>{feedback.signals?.recent_failure_count || 0}</strong>
          <p>falhas recentes</p>
        </div>
        <div>
          <strong>{feedback.signals?.watchlist_count || 0}</strong>
          <p>exercícios a vigiar</p>
        </div>
        <div>
          <strong>
            {feedback.signals?.volume_trend?.change_percent > 0 ? "+" : ""}
            {feedback.signals?.volume_trend?.change_percent || 0}%
          </strong>
          <p>tendência volume</p>
        </div>
      </div>

      <div className="weekly-feedback-list">
        {(feedback.feedback || []).map((item) => (
          <p key={item}>{item}</p>
        ))}
      </div>

      {feedback.deload?.recommended && (
        <div className="weekly-deload-card">
          <strong>Protocolo de deload sugerido</strong>
          <p>
            {feedback.deload.duration} · volume a{" "}
            {Math.round((feedback.deload.volume_multiplier || 0) * 100)}% · RIR alvo{" "}
            {feedback.deload.target_rir}+
          </p>
          <div>
            {(feedback.deload.protocol || []).map((item) => (
              <p key={item}>{item}</p>
            ))}
          </div>
          {feedback.deload.reasons?.length > 0 && (
            <p className="weekly-deload-reason">
              Motivo: {feedback.deload.reasons.join(", ")}
            </p>
          )}
        </div>
      )}
    </section>
  );
}
