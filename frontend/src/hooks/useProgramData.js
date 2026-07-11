// =============================================================================
// useProgramData.js
// -----------------------------------------------------------------------------
// Hook responsável pelos dados globais do programa e painéis analíticos.
// É usado pelo App.jsx para carregar dashboard, plano adaptativo, decisões,
// feedback semanal, bloco de treino e recomendações para o próximo treino.
// Centraliza chamadas à API de training ligadas ao estado geral do atleta.
// =============================================================================
import { useState } from "react";
import * as trainingApi from "../api/trainingApi";

export default function useProgramData({ profileId, setStep, resetTrainingState }) {
  const [program, setProgram] = useState(null);
  const [programError, setProgramError] = useState("");
  const [isGeneratingProgram, setIsGeneratingProgram] = useState(false);
  const [latestWorkoutProgression, setLatestWorkoutProgression] = useState(null);
  const [latestAiCoach, setLatestAiCoach] = useState(null);
  const [athleteDashboard, setAthleteDashboard] = useState(null);
  const [adaptivePlan, setAdaptivePlan] = useState(null);
  const [adaptiveDecisions, setAdaptiveDecisions] = useState([]);
  const [weeklyFeedback, setWeeklyFeedback] = useState(null);
  const [trainingBlock, setTrainingBlock] = useState(null);
  const [applyingAdaptiveById, setApplyingAdaptiveById] = useState({});

  async function loadAthleteDashboard(profileIdOverride = null) {
    const dashboardProfileId = profileIdOverride || profileId;

    if (!dashboardProfileId) {
      return null;
    }

    try {
      const data = await trainingApi.getDashboard(dashboardProfileId);
      setAthleteDashboard(data);
      return data;
    } catch (error) {
      console.error(error.data || error);
      return null;
    }
  }

  async function loadAdaptivePlan(profileIdOverride = null) {
    const adaptiveProfileId = profileIdOverride || profileId;

    if (!adaptiveProfileId) {
      return null;
    }

    try {
      const data = await trainingApi.getAdaptivePlan(adaptiveProfileId);
      setAdaptivePlan(data);
      return data;
    } catch (error) {
      console.error(error.data || error);
      return null;
    }
  }

  async function loadAdaptiveDecisions(profileIdOverride = null) {
    const decisionsProfileId = profileIdOverride || profileId;

    if (!decisionsProfileId) {
      return [];
    }

    try {
      const data = await trainingApi.getAdaptiveDecisions(decisionsProfileId);
      setAdaptiveDecisions(data.decisions || []);
      return data.decisions || [];
    } catch (error) {
      console.error(error.data || error);
      return [];
    }
  }

  async function loadWeeklyFeedback(profileIdOverride = null) {
    const feedbackProfileId = profileIdOverride || profileId;

    if (!feedbackProfileId) {
      return null;
    }

    try {
      const data = await trainingApi.getWeeklyFeedback(feedbackProfileId);
      setWeeklyFeedback(data);
      return data;
    } catch (error) {
      console.error(error.data || error);
      return null;
    }
  }

  async function loadTrainingBlock(profileIdOverride = null) {
    const blockProfileId = profileIdOverride || profileId;

    if (!blockProfileId) {
      return null;
    }

    try {
      const data = await trainingApi.getTrainingBlock(blockProfileId);
      setTrainingBlock(data);
      return data;
    } catch (error) {
      console.error(error.data || error);
      return null;
    }
  }

  function loadProgramPanels(profileIdOverride = null) {
    loadAthleteDashboard(profileIdOverride);
    loadAdaptivePlan(profileIdOverride);
    loadAdaptiveDecisions(profileIdOverride);
    loadWeeklyFeedback(profileIdOverride);
    loadTrainingBlock(profileIdOverride);
  }

  async function generateProgram() {
    if (!profileId) {
      setProgramError("Não encontrei o perfil activo. Volta a criar o perfil antes de gerar o programa.");
      return;
    }

    setProgramError("");
    setIsGeneratingProgram(true);

    try {
      const data = await trainingApi.generateProgram({ profile_id: profileId });

      if (!Array.isArray(data.workouts)) {
        console.error(data);
        setProgramError("A resposta do programa veio incompleta. Tenta novamente.");
        return;
      }

      setProgram(data);
      setLatestWorkoutProgression(null);
      setLatestAiCoach(null);
      resetTrainingState();
      loadProgramPanels(profileId);
      setStep(4);
    } catch (error) {
      console.error(error);
      setProgramError("Não consegui contactar o servidor para gerar o programa.");
    } finally {
      setIsGeneratingProgram(false);
    }
  }

  async function recordAdaptiveDecision(recommendation, decisionStatus) {
    if (!profileId) {
      alert("Não encontrei o perfil ativo.");
      return;
    }

    if (decisionStatus === "APPLIED") {
      const shouldApply = window.confirm(
        `Aplicar ajuste em ${recommendation.exercise_name}?\n\nSéries: ${recommendation.current_sets} → ${recommendation.recommended_sets}\nRIR: ${recommendation.current_target_rir} → ${recommendation.recommended_target_rir}\nCarga sugerida: ${recommendation.load_adjustment > 0 ? "+" : ""}${recommendation.load_adjustment}kg`
      );

      if (!shouldApply) {
        return;
      }
    }

    setApplyingAdaptiveById({
      ...applyingAdaptiveById,
      [recommendation.training_exercise]: true,
    });

    let data;

    try {
      data = await trainingApi.applyAdaptivePlanDecision({
        profile_id: profileId,
        training_exercise_id: recommendation.training_exercise,
        status: decisionStatus,
      });
    } catch (error) {
      console.error(error.data || error);
      alert("Não consegui gravar a decisão adaptativa.");
      data = null;
    }

    setApplyingAdaptiveById((currentState) => ({
      ...currentState,
      [recommendation.training_exercise]: false,
    }));

    if (!data) {
      return;
    }

    if (decisionStatus === "APPLIED") {
      setProgram((currentProgram) => {
        if (!currentProgram) {
          return currentProgram;
        }

        return {
          ...currentProgram,
          workouts: currentProgram.workouts.map((workout) => ({
            ...workout,
            exercises: workout.exercises.map((exercise) => (
              exercise.id === data.updated_exercise.id
                ? {
                    ...exercise,
                    sets: data.updated_exercise.sets,
                    target_rir: data.updated_exercise.target_rir,
                  }
                : exercise
            )),
          })),
        };
      });
    }

    await loadAdaptivePlan();
    await loadAdaptiveDecisions();
    await loadWeeklyFeedback();
    await loadTrainingBlock();
  }

  return {
    program,
    setProgram,
    programError,
    setProgramError,
    isGeneratingProgram,
    latestWorkoutProgression,
    setLatestWorkoutProgression,
    latestAiCoach,
    setLatestAiCoach,
    athleteDashboard,
    setAthleteDashboard,
    adaptivePlan,
    setAdaptivePlan,
    adaptiveDecisions,
    setAdaptiveDecisions,
    weeklyFeedback,
    setWeeklyFeedback,
    trainingBlock,
    setTrainingBlock,
    applyingAdaptiveById,
    setApplyingAdaptiveById,
    loadAthleteDashboard,
    loadAdaptivePlan,
    loadAdaptiveDecisions,
    loadWeeklyFeedback,
    loadTrainingBlock,
    loadProgramPanels,
    generateProgram,
    recordAdaptiveDecision,
  };
}
