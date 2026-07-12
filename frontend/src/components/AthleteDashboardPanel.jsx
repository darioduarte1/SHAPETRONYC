// =============================================================================
// AthleteDashboardPanel.jsx
// -----------------------------------------------------------------------------
// Componente visual do dashboard do atleta.
// É usado no ecrã principal para mostrar evolução, volume, séries, calibrações, últimos treinos, alertas e memória disponível.
// Recebe dados agregados do backend e funções de formatação vindas do App.jsx.
// =============================================================================
import { useState } from "react";
import AiCoachSummaryPanel from "./AiCoachSummaryPanel";

export default function AthleteDashboardPanel({
  dashboard,
  formatDate,
  formatNumber,
  getConfidenceColor,
  getMaxWeeklyVolume,
}) {
  const [openFeedbackSessionId, setOpenFeedbackSessionId] = useState(null);

  if (!dashboard) {
    return null;
  }

  return (
    <section className="dashboard-panel">
      <div className="panel-heading-row">
        <div>
          <div className="panel-kicker">Dashboard</div>
          <h3>Evolução do atleta</h3>
        </div>
        <span className="panel-date">
          Último treino: {formatDate(dashboard.summary?.last_workout_at)}
        </span>
      </div>

      <div className="dashboard-metrics">
        <div>
          <strong>{dashboard.summary?.completed_workouts || 0}</strong>
          <p>Treinos</p>
        </div>
        <div>
          <strong>{formatNumber(dashboard.summary?.total_volume)} kg</strong>
          <p>Volume</p>
        </div>
        <div>
          <strong>{dashboard.summary?.total_sets || 0}</strong>
          <p>Séries</p>
        </div>
        <div>
          <strong>{dashboard.summary?.average_rir ?? "-"}</strong>
          <p>RIR médio</p>
        </div>
        <div>
          <strong>{dashboard.summary?.calibrated_exercises || 0}</strong>
          <p>Calibrações</p>
        </div>
      </div>

      <div className="dashboard-grid">
        <div>
          <strong>Volume semanal</strong>
          {dashboard.weekly_volume?.length > 0 ? (
            <div
              className="weekly-volume-chart"
              style={{
                gridTemplateColumns: `repeat(${dashboard.weekly_volume.length}, minmax(32px, 1fr))`,
              }}
            >
              {dashboard.weekly_volume.map((week) => {
                const maxVolume = getMaxWeeklyVolume(dashboard);
                const height = Math.max(8, (Number(week.volume) / maxVolume) * 112);

                return (
                  <div key={week.week} className="weekly-volume-bar-wrap">
                    <div
                      className="weekly-volume-bar"
                      title={`${week.week}: ${formatNumber(week.volume)} kg`}
                      style={{ height: `${height}px` }}
                    />
                    <span>{week.week.split("-")[1]}</span>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="muted-text">Sem semanas concluídas.</p>
          )}
        </div>

        <div>
          <strong>Últimos treinos</strong>
          <div className="compact-list">
            {(dashboard.recent_sessions || []).slice(0, 4).map((session) => (
              <div key={session.id} className="recent-session-card">
                <div className="recent-session-row">
                  <span>
                    {session.workout_name}
                    {session.coach_feedback?.headline && (
                      <small>{session.coach_feedback.headline}</small>
                    )}
                  </span>
                  <span>{formatNumber(session.volume)} kg</span>
                </div>
                {session.coach_feedback && (
                  <button
                    type="button"
                    className="recent-session-feedback-button"
                    onClick={() =>
                      setOpenFeedbackSessionId(
                        openFeedbackSessionId === session.id ? null : session.id
                      )
                    }
                  >
                    {openFeedbackSessionId === session.id ? "Fechar feedback" : "Ver feedback"}
                  </button>
                )}
                {openFeedbackSessionId === session.id && session.coach_feedback && (
                  <AiCoachSummaryPanel
                    summary={session.coach_feedback}
                    getSourceLabel={(status) => status || "histórico"}
                    compact
                  />
                )}
              </div>
            ))}
            {dashboard.recent_sessions?.length === 0 && (
              <p className="muted-text no-margin">Ainda sem treinos concluídos.</p>
            )}
          </div>
        </div>
      </div>

      <div className="dashboard-grid compact">
        <div>
          <strong>Melhor progressão</strong>
          <div className="compact-list">
            {(dashboard.top_progressing_exercises || []).map((exercise) => (
              <div key={exercise.exercise_id}>
                <span>{exercise.exercise_name}</span>
                <p className="positive-text">
                  +{formatNumber(exercise.load_change)} kg em {exercise.sessions} treinos
                </p>
              </div>
            ))}
            {dashboard.top_progressing_exercises?.length === 0 && (
              <p className="muted-text no-margin">Sem progressões suficientes.</p>
            )}
          </div>
        </div>

        <div>
          <strong>A vigiar</strong>
          <div className="compact-list">
            {(dashboard.watchlist_exercises || []).map((exercise) => (
              <div key={exercise.exercise_id}>
                <span>{exercise.exercise_name}</span>
                <p className="warning-text">{exercise.reason}</p>
              </div>
            ))}
            {dashboard.watchlist_exercises?.length === 0 && (
              <p className="muted-text no-margin">Sem alertas recentes.</p>
            )}
          </div>
        </div>
      </div>

      {(dashboard.calibrated_exercises || []).length > 0 && (
        <div className="dashboard-section">
          <strong>Dados calibrados</strong>
          <div className="dashboard-card-grid">
            {dashboard.calibrated_exercises.map((exercise) => (
              <div key={exercise.exercise_id} className="calibrated-exercise-card">
                <span>{exercise.exercise_name}</span>
                <p>
                  Peso base: {formatNumber(exercise.estimated_working_weight)} kg · {exercise.set_count} série(s)
                </p>
                <p style={{ color: getConfidenceColor(exercise.confidence) }}>
                  Confiança {exercise.confidence}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="dashboard-section">
        <strong>Memória do atleta</strong>
        <div className="dashboard-card-grid">
          {(dashboard.training_memories || []).map((memory) => (
            <div key={memory.id} className="memory-card">
              <div className="memory-card-heading">
                <span>{memory.title}</span>
                <span style={{ color: getConfidenceColor(memory.confidence) }}>
                  {memory.confidence}
                </span>
              </div>
              <p>{memory.summary}</p>
              {memory.evidence?.length > 0 && (
                <div className="memory-evidence-list">
                  {memory.evidence.map((item) => (
                    <p key={item}>{item}</p>
                  ))}
                </div>
              )}
            </div>
          ))}
          {dashboard.training_memories?.length === 0 && (
            <p className="muted-text no-margin">
              Ainda sem memória suficiente. Termina mais alguns treinos para criar padrões.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
