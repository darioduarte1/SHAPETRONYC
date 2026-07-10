export default function AdaptivePlanPanel({
  adaptivePlan,
  adaptiveDecisions,
  applyingAdaptiveById,
  getActionLabel,
  getActionColor,
  getDecisionStatusLabel,
  recordAdaptiveDecision,
}) {
  if (!adaptivePlan) {
    return null;
  }

  const actionableRecommendations = (adaptivePlan.recommendations || []).filter(
    (recommendation) => recommendation.action !== "maintain_plan"
  );

  return (
    <section className="adaptive-plan-panel">
      <div className="panel-heading-row">
        <div>
          <div className="panel-kicker adaptive">Plano adaptativo</div>
          <h3>Ajustes sugeridos</h3>
        </div>
        <span className="adaptive-priority-count">
          {adaptivePlan.summary?.high_priority_count || 0} prioridade alta
        </span>
      </div>

      <div className="adaptive-recommendation-list">
        {actionableRecommendations.slice(0, 6).map((recommendation) => (
          <div key={recommendation.training_exercise} className="adaptive-recommendation-card">
            <div className="adaptive-recommendation-heading">
              <div>
                <strong>{recommendation.exercise_name}</strong>
                <p>{recommendation.workout_name}</p>
              </div>
              <span style={{ color: getActionColor(recommendation.action) }}>
                {getActionLabel(recommendation.action)}
              </span>
            </div>
            <p className="adaptive-message">{recommendation.message}</p>
            <p className="adaptive-target">
              Séries: {recommendation.current_sets} → {recommendation.recommended_sets} | RIR:{" "}
              {recommendation.current_target_rir} → {recommendation.recommended_target_rir} | carga{" "}
              {recommendation.load_adjustment > 0 ? "+" : ""}
              {recommendation.load_adjustment}kg
            </p>
            {recommendation.evidence?.length > 0 && (
              <div className="adaptive-evidence-list">
                {recommendation.evidence.map((item) => (
                  <p key={item}>{item}</p>
                ))}
              </div>
            )}
            <div className="adaptive-action-row">
              <button
                type="button"
                className="adaptive-apply-button"
                onClick={() => recordAdaptiveDecision(recommendation, "APPLIED")}
                disabled={Boolean(applyingAdaptiveById[recommendation.training_exercise])}
              >
                {applyingAdaptiveById[recommendation.training_exercise] ? "A aplicar..." : "Aplicar"}
              </button>
              <button
                type="button"
                onClick={() => recordAdaptiveDecision(recommendation, "DEFERRED")}
                disabled={Boolean(applyingAdaptiveById[recommendation.training_exercise])}
              >
                Adiar
              </button>
              <button
                type="button"
                onClick={() => recordAdaptiveDecision(recommendation, "IGNORED")}
                disabled={Boolean(applyingAdaptiveById[recommendation.training_exercise])}
              >
                Ignorar
              </button>
            </div>
          </div>
        ))}
        {actionableRecommendations.length === 0 && (
          <p className="adaptive-empty">
            Sem ajustes adaptativos por agora. Mantém o plano e continua a recolher dados.
          </p>
        )}
      </div>

      {adaptiveDecisions.length > 0 && (
        <div className="adaptive-decisions">
          <strong>Últimas decisões</strong>
          <div>
            {adaptiveDecisions.slice(0, 5).map((decision) => (
              <div key={decision.id} className="adaptive-decision-row">
                <div>
                  <strong>{decision.exercise_name}</strong>
                  <p>
                    {getActionLabel(decision.action)} · Séries {decision.current_sets} →{" "}
                    {decision.recommended_sets} · RIR {decision.current_target_rir} →{" "}
                    {decision.recommended_target_rir} · carga{" "}
                    {decision.load_adjustment > 0 ? "+" : ""}
                    {decision.load_adjustment}kg
                  </p>
                </div>
                <span>{getDecisionStatusLabel(decision.status)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
