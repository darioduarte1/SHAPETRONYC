// =============================================================================
// CoachDecisionDebugPanel.jsx
// -----------------------------------------------------------------------------
// Painel experimental de auditoria da decisão híbrida do coach.
// É usado pelo ExerciseGuidanceCard para mostrar o que as regras decidiram,
// o que a IA tentou ajustar, que limites estavam ativos e qual decisão final
// foi aplicada. Ajuda a validar se a IA acrescenta valor sem quebrar guardrails.
// =============================================================================

function formatValue(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  if (typeof value === "boolean") {
    return value ? "sim" : "não";
  }

  if (Array.isArray(value)) {
    return value.length ? value.join(", ") : "-";
  }

  return String(value);
}

function DecisionMiniCard({ title, decision }) {
  if (!decision) {
    return (
      <div className="coach-decision-mini-card">
        <strong>{title}</strong>
        <p>Sem tentativa registada.</p>
      </div>
    );
  }

  return (
    <div className="coach-decision-mini-card">
      <strong>{title}</strong>
      <dl>
        <div>
          <dt>Ação</dt>
          <dd>{formatValue(decision.action)}</dd>
        </div>
        <div>
          <dt>Peso</dt>
          <dd>{formatValue(decision.recommended_weight)}</dd>
        </div>
        <div>
          <dt>Reps</dt>
          <dd>{formatValue(decision.target_reps)}</dd>
        </div>
        <div>
          <dt>Estado</dt>
          <dd>{formatValue(decision.exercise_status)}</dd>
        </div>
      </dl>
      {decision.reason && <p>{decision.reason}</p>}
    </div>
  );
}

export default function CoachDecisionDebugPanel({ envelope }) {
  if (!envelope) {
    return null;
  }

  const permissions = envelope.ai_permissions || {};
  const constraints = envelope.safety_constraints || {};
  const validation = envelope.validation || {};
  const weightScale = constraints.weight_scale || {};
  const guardrailApplied = validation.guardrail_applied;

  return (
    <details className="coach-decision-debug-panel">
      <summary>
        <span>Decisão do coach</span>
        <strong className={guardrailApplied ? "warning" : "ok"}>
          {validation.status || envelope.strategy}
        </strong>
      </summary>

      <div className="coach-decision-debug-grid">
        <DecisionMiniCard title="Regras" decision={envelope.local_decision} />
        <DecisionMiniCard title="IA tentou" decision={envelope.ai_decision} />
        <DecisionMiniCard title="Final" decision={envelope.final_decision} />
      </div>

      <div className="coach-decision-debug-section">
        <strong>Permissões da IA</strong>
        <div className="coach-decision-pill-grid">
          <span className={permissions.can_change_message ? "enabled" : ""}>mensagem</span>
          <span className={permissions.can_change_weight ? "enabled" : ""}>peso</span>
          <span className={permissions.can_increase_weight ? "enabled" : ""}>subir peso</span>
          <span className={permissions.can_add_set ? "enabled" : ""}>adicionar série</span>
          <span className={permissions.can_stop_exercise ? "enabled" : ""}>parar exercício</span>
        </div>
      </div>

      <div className="coach-decision-debug-section">
        <strong>Limites ativos</strong>
        <dl className="coach-decision-constraints">
          <div>
            <dt>Escala</dt>
            <dd>{weightScale.configured ? "preenchida" : "em falta"}</dd>
          </div>
          <div>
            <dt>Peso local</dt>
            <dd>{formatValue(constraints.local_recommended_weight)}</dd>
          </div>
          <div>
            <dt>Intervalo permitido</dt>
            <dd>{formatValue(constraints.min_weight)} - {formatValue(constraints.max_weight)}</dd>
          </div>
          <div>
            <dt>Pesos reais</dt>
            <dd>{formatValue(weightScale.available_weights)}</dd>
          </div>
        </dl>
      </div>

      {validation.reasons?.length > 0 && (
        <div className="coach-decision-debug-section">
          <strong>Validação</strong>
          {validation.reasons.map((reason) => (
            <p key={reason}>{reason}</p>
          ))}
        </div>
      )}
    </details>
  );
}
