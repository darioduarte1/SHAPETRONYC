// =============================================================================
// useExerciseGuidance.js
// -----------------------------------------------------------------------------
// Hook responsável pela mensagem de "próximo passo" dentro de cada exercício.
// É usado pelo App.jsx e WorkoutCard para combinar descanso, recomendações da IA,
// séries já feitas e valores planeados numa orientação simples para o atleta.
// Mantém o texto dinâmico da sessão separado da tabela e do componente principal.
// =============================================================================

export default function useExerciseGuidance({
  recommendations,
  getCurrentSetForRow,
  getSetTypeForExerciseRow,
  getVisibleSetLabel,
  getPlannedValuesForExerciseRow,
  getWarmupReferenceSet,
  getExerciseTargetLabel,
}) {
  function getNextExerciseRow(exercise, rows) {
    return rows.find((row) => !getCurrentSetForRow(exercise.id, row.displaySetNumber));
  }

  function getGuidanceForExercise(exercise, rows, restSeconds) {
    if (restSeconds > 0) {
      return {
        eyebrow: "Descanso",
        title: "Aguarda antes da próxima série",
        message: "Respira, recupera a técnica e prepara a próxima execução.",
        isResting: true,
      };
    }

    const latestRecommendation = recommendations[exercise.id];

    if (latestRecommendation?.exercise_status === "complete") {
      return {
        eyebrow: "Exercício concluído",
        title: latestRecommendation.guidance_title || "Passa para o próximo exercício",
        message: latestRecommendation.guidance_message || "O coach decidiu que continuar agora acrescenta mais fadiga do que benefício.",
        reason: latestRecommendation.reason,
        isResting: false,
        source: latestRecommendation.source,
        confidence: latestRecommendation.confidence,
        llmStatus: latestRecommendation.llm_status,
        guardrailApplied: latestRecommendation.guardrail_applied,
        guardrailReason: latestRecommendation.guardrail_reason,
        decisionBasis: latestRecommendation.decision_basis || [],
        decisionEnvelope: latestRecommendation.decision_envelope,
      };
    }

    const nextRow = getNextExerciseRow(exercise, rows);

    if (!nextRow) {
      return {
        eyebrow: "Exercício concluído",
        title: "Todas as séries deste exercício estão registadas",
        message: "Segue para o próximo exercício quando te sentires pronto.",
        isResting: false,
      };
    }

    const rowSetType = getSetTypeForExerciseRow(exercise, nextRow.sourceSetNumber, nextRow.displaySetNumber);
    const visibleSetLabel = getVisibleSetLabel(exercise, rows, nextRow.sourceSetNumber, nextRow.displaySetNumber);
    const plannedValues = getPlannedValuesForExerciseRow(
      exercise,
      rows,
      nextRow.sourceSetNumber,
      nextRow.displaySetNumber
    );
    const warmupReferenceSet = getWarmupReferenceSet(
      exercise,
      rows,
      nextRow.sourceSetNumber,
      nextRow.displaySetNumber
    );
    const recommendedWeight = plannedValues.weight || latestRecommendation?.recommended_weight;
    const recommendedReps = plannedValues.reps || latestRecommendation?.target_reps;
    const targetLabel = getExerciseTargetLabel(exercise);
    const hasLoadTarget = recommendedWeight !== "" && recommendedWeight !== undefined && recommendedReps;
    const loadCue = hasLoadTarget
      ? `Aponta para ${recommendedWeight}kg x ${targetLabel} reps.`
      : `Trabalha com o objectivo de chegar às ${targetLabel} reps.`;
    const warmupCue = plannedValues.weight && plannedValues.reps
      ? `Aquecimento recomendado: ${plannedValues.weight}kg x ${plannedValues.reps} reps.`
      : warmupReferenceSet
        ? `Mantém a referência anterior de ${warmupReferenceSet.weight_used}kg x ${warmupReferenceSet.reps_completed} reps.`
        : `Sobe a carga gradualmente até sentires o movimento pronto.`;
    const coachTitle = latestRecommendation?.guidance_title;
    const coachMessage = latestRecommendation?.guidance_message;
    const reason = latestRecommendation?.reason || plannedValues.reason || "";
    const coachMetadata = {
      source: latestRecommendation?.source || plannedValues.source,
      confidence: latestRecommendation?.confidence || plannedValues.confidence,
      llmStatus: latestRecommendation?.llm_status,
      guardrailApplied: latestRecommendation?.guardrail_applied,
      guardrailReason: latestRecommendation?.guardrail_reason,
      decisionBasis: latestRecommendation?.decision_basis || plannedValues.decisionBasis || [],
      decisionEnvelope: latestRecommendation?.decision_envelope,
    };

    if (rowSetType === "WARMUP") {
      return {
        eyebrow: "Próximo passo",
        title: `Faz a série ${visibleSetLabel} de aquecimento`,
        message: `Usa uma carga controlada para preparar o movimento. ${warmupCue}`,
        reason: "",
        isResting: false,
        ...coachMetadata,
      };
    }

    if (rowSetType === "DROP") {
      return {
        eyebrow: "Próximo passo",
        title: coachTitle ? `Série ${visibleSetLabel}: ${coachTitle}` : `Faz a série ${visibleSetLabel} em drop`,
        message: coachMessage ? `${coachMessage} ${loadCue}` : `Reduz a carga e mantém a execução limpa até ao alvo. ${loadCue}`,
        reason,
        isResting: false,
        ...coachMetadata,
      };
    }

    return {
      eyebrow: "Próximo passo",
      title: coachTitle ? `Série ${visibleSetLabel}: ${coachTitle}` : `Faz a série ${visibleSetLabel}`,
      message: coachMessage ? `${coachMessage} ${loadCue}` : `Mantém o controlo e respeita o esforço planeado. ${loadCue}`,
      reason,
      isResting: false,
      ...coachMetadata,
    };
  }

  return {
    getNextExerciseRow,
    getGuidanceForExercise,
  };
}
