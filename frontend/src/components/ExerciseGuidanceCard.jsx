// =============================================================================
// ExerciseGuidanceCard.jsx
// -----------------------------------------------------------------------------
// Componente visual da orientação dinâmica do exercício.
// É usado pelo ExerciseCard para mostrar o próximo passo, motivo da decisão,
// metadados da IA/coach, base da decisão e timer de descanso quando aplicável.
// Mantém a apresentação do coach separada do painel de calibração e da tabela.
// =============================================================================
import CoachDecisionDebugPanel from "./CoachDecisionDebugPanel";

export default function ExerciseGuidanceCard({
  exercise,
  guidance,
  restSeconds,
  formatTimer,
  adjustRestTimer,
  getDecisionSourceLabel,
  getLlmStatusLabel,
  getConfidenceColor,
  showDebugPanel = false,
}) {
  return (
    <div className="exercise-guidance-card">
      <div
        className="exercise-guidance-eyebrow"
        style={{ color: guidance.isResting ? "#0ea5e9" : "#94a3b8" }}
      >
        {guidance.eyebrow}
      </div>
      <strong>{guidance.title}</strong>
      <p>{guidance.message}</p>

      {guidance.reason && !guidance.isResting && (
        <p className="exercise-guidance-reason">{guidance.reason}</p>
      )}

      {guidance.source && !guidance.isResting && (
        <div className="exercise-guidance-meta">
          <span>{getDecisionSourceLabel(guidance.source)}</span>
          {guidance.llmStatus && (
            <span style={{ color: guidance.llmStatus === "llm_enabled" ? "#86efac" : "#fbbf24" }}>
              {getLlmStatusLabel(guidance.llmStatus)}
            </span>
          )}
          {guidance.confidence && (
            <span style={{ color: getConfidenceColor(guidance.confidence) }}>
              Confiança {guidance.confidence}
            </span>
          )}
          {guidance.guardrailApplied && (
            <span title={guidance.guardrailReason} style={{ color: "#fbbf24" }}>
              Guardrail aplicado
            </span>
          )}
        </div>
      )}

      {guidance.decisionBasis?.length > 0 && !guidance.isResting && (
        <div className="exercise-guidance-basis">
          {guidance.decisionBasis.map((basis) => (
            <p key={basis}>{basis}</p>
          ))}
        </div>
      )}

      {guidance.isResting && (
        <div className="exercise-rest-card">
          <div>{formatTimer(restSeconds)}</div>
          <div>
            <button type="button" onClick={() => adjustRestTimer(exercise.id, -15)}>
              -15s
            </button>
            <button type="button" onClick={() => adjustRestTimer(exercise.id, 15)}>
              +15s
            </button>
          </div>
        </div>
      )}

      {showDebugPanel && !guidance.isResting && (
        <CoachDecisionDebugPanel envelope={guidance.decisionEnvelope} />
      )}
    </div>
  );
}
