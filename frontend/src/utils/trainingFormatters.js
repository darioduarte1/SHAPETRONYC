// =============================================================================
// trainingFormatters.js
// -----------------------------------------------------------------------------
// Conjunto de funções utilitárias de formatação e labels do frontend.
// É usado pelo App.jsx e componentes para traduzir estados técnicos em texto, cores e valores legíveis.
// Não altera dados; apenas prepara informação para apresentação visual.
// =============================================================================
export function formatNumber(value, digits = 1) {
  return Number(value || 0).toFixed(digits);
}

export function formatDashboardDate(dateValue) {
  if (!dateValue) {
    return "-";
  }

  return new Date(dateValue).toLocaleDateString("pt-PT", {
    day: "2-digit",
    month: "short",
  });
}

export function getDashboardMaxWeeklyVolume(dashboard) {
  return Math.max(...((dashboard?.weekly_volume || []).map((week) => Number(week.volume) || 0)), 1);
}

export function getAdaptiveActionLabel(action) {
  const labels = {
    protect_recovery: "Proteger recuperação",
    increase_margin: "Aumentar margem",
    progress_load: "Progredir carga",
    maintain_plan: "Manter plano",
  };

  return labels[action] || "Ajuste";
}

export function getAdaptiveActionColor(action) {
  const colors = {
    protect_recovery: "#fbbf24",
    increase_margin: "#38bdf8",
    progress_load: "#86efac",
    maintain_plan: "#94a3b8",
  };

  return colors[action] || "#94a3b8";
}

export function getAdaptiveDecisionStatusLabel(status) {
  const labels = {
    APPLIED: "Aplicada",
    DEFERRED: "Adiada",
    IGNORED: "Ignorada",
  };

  return labels[status] || status;
}

export function getWeeklyFeedbackStatusColor(status) {
  const colors = {
    deload_recommended: "#fbbf24",
    monitor: "#38bdf8",
    progressing: "#86efac",
  };

  return colors[status] || "#94a3b8";
}

export function getWeeklyFeedbackStatusLabel(status) {
  const labels = {
    deload_recommended: "Deload recomendado",
    monitor: "Monitorizar",
    progressing: "Progressão saudável",
  };

  return labels[status] || "Feedback semanal";
}

export function getTrainingBlockPhaseLabel(phase) {
  const labels = {
    BUILD: "Build",
    DELOAD: "Deload",
    RETURN: "Retorno",
  };

  return labels[phase] || "Bloco";
}

export function getTrainingBlockPhaseColor(phase) {
  const colors = {
    BUILD: "#86efac",
    DELOAD: "#fbbf24",
    RETURN: "#38bdf8",
  };

  return colors[phase] || "#94a3b8";
}

export function getProgressionActionLabel(action) {
  const labels = {
    increase_load: "Subir carga",
    maintain_load: "Manter carga",
    reduce_volume: "Reduzir volume",
    adjust_target_rir: "Alterar RIR",
    maintain: "Manter plano",
  };

  return labels[action] || "Recomendação";
}

export function formatProgressionTarget(recommendation) {
  const weightLabel =
    recommendation.recommended_weight === "" || recommendation.recommended_weight === null
      ? "carga do plano"
      : `${recommendation.recommended_weight}kg`;

  return `${weightLabel} | ${recommendation.recommended_sets} séries | ${recommendation.target_reps} reps | RIR ${recommendation.target_rir}`;
}

export function getAiCoachSourceLabel(status) {
  const labels = {
    llm_enabled: "OpenAI",
    llm_error: "Fallback local",
    llm_disabled: "Fallback local",
  };

  return labels[status] || "Coach";
}

export function getDecisionSourceLabel(source) {
  const labels = {
    hybrid_local_training_coach: "Coach híbrido local",
    hybrid_local_workout_progression: "Progressão híbrida local",
    openai_training_decision: "IA OpenAI série a série",
    ollama_training_decision: "IA Ollama local",
    last_15_workout_history: "Histórico últimos 15 treinos",
    warmup_from_first_working_set: "Aquecimento proporcional",
    warmup_ramp_from_first_working_set: "Aquecimento progressivo",
    training_coach_engine: "Motor local",
  };

  return labels[source] || "Motor local";
}

export function getLlmStatusLabel(status) {
  const labels = {
    llm_enabled: "IA ativa",
    llm_error: "Fallback local",
    llm_disabled: "Regras locais",
  };

  return labels[status] || "";
}

export function getConfidenceColor(confidence) {
  const colors = {
    alta: "#22c55e",
    média: "#eab308",
    baixa: "#f97316",
  };

  return colors[confidence] || "#94a3b8";
}
