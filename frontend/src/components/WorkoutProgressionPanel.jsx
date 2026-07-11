// =============================================================================
// WorkoutProgressionPanel.jsx
// -----------------------------------------------------------------------------
// Componente visual das recomendações para o próximo treino.
// É usado no ecrã principal para mostrar carga, séries, reps e RIR sugeridos por exercício.
// Recebe recomendações já calculadas e ajuda o atleta a perceber a progressão planeada.
// =============================================================================
export default function WorkoutProgressionPanel({
  progression,
  getActionLabel,
  getSourceLabel,
  getConfidenceColor,
  formatTarget,
}) {
  if (!progression) {
    return null;
  }

  return (
    <section className="workout-progression-panel">
      <div className="panel-kicker">Próximo treino</div>
      <h3>Progressão para {progression.workout_name}</h3>

      <div className="workout-progression-list">
        {progression.recommendations.map((recommendation) => (
          <div key={recommendation.training_exercise} className="workout-progression-card">
            <div className="progression-card-heading">
              <strong>{recommendation.exercise_name}</strong>
              <span>{getActionLabel(recommendation.action)}</span>
            </div>
            <p className="progression-target">{formatTarget(recommendation)}</p>
            <p className="progression-message">{recommendation.message}</p>
            <div className="progression-meta">
              <span>{getSourceLabel(recommendation.source)}</span>
              {recommendation.confidence && (
                <span style={{ color: getConfidenceColor(recommendation.confidence) }}>
                  Confiança {recommendation.confidence}
                </span>
              )}
            </div>
            {recommendation.decision_basis?.length > 0 && (
              <div className="progression-basis-list">
                {recommendation.decision_basis.map((basis) => (
                  <p key={basis}>{basis}</p>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
