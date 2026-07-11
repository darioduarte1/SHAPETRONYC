// =============================================================================
// trainingApi.js
// -----------------------------------------------------------------------------
// Funções de acesso aos endpoints de treino, sessões, dashboard, calibração,
// escalas de máquina, blocos, feedback semanal e plano adaptativo.
// É usado pelo App.jsx para manter a comunicação com o backend organizada por
// domínio em vez de espalhar fetch diretamente pela interface.
// =============================================================================
import { apiRequest } from "./client";

export function saveExerciseWeightScale(profileId, trainingExerciseId, payload) {
  return apiRequest(`/api/training/exercise-weight-scale/${profileId}/${trainingExerciseId}/`, {
    method: "PATCH",
    body: payload,
  });
}

export function saveExerciseCalibration(payload) {
  return apiRequest("/api/training/exercise-calibration/", {
    method: "POST",
    body: payload,
  });
}

export function getDashboard(profileId) {
  return apiRequest(`/api/training/dashboard/${profileId}/`);
}

export function getAdaptivePlan(profileId) {
  return apiRequest(`/api/training/adaptive-plan/${profileId}/`);
}

export function getAdaptiveDecisions(profileId) {
  return apiRequest(`/api/training/adaptive-plan/decisions/${profileId}/`);
}

export function getWeeklyFeedback(profileId) {
  return apiRequest(`/api/training/weekly-feedback/${profileId}/`);
}

export function getTrainingBlock(profileId) {
  return apiRequest(`/api/training/training-blocks/${profileId}/`);
}

export function getProgram(profileId) {
  return apiRequest(`/api/training/program/${profileId}/`);
}

export function applyAdaptivePlanDecision(payload) {
  return apiRequest("/api/training/adaptive-plan/apply/", {
    method: "POST",
    body: payload,
  });
}

export function getExerciseSubstitutions(trainingExerciseId) {
  return apiRequest(`/api/training/exercise-substitutions/${trainingExerciseId}/`);
}

export function replaceTrainingExercise(payload) {
  return apiRequest("/api/training/replace-exercise/", {
    method: "POST",
    body: payload,
  });
}

export function generateProgram(payload) {
  return apiRequest("/api/training/generate-program/", {
    method: "POST",
    body: payload,
  });
}

export function startWorkoutSession(payload) {
  return apiRequest("/api/training/start-session/", {
    method: "POST",
    body: payload,
  });
}

export function finishWorkoutSession(payload) {
  return apiRequest("/api/training/finish-session/", {
    method: "POST",
    body: payload,
  });
}
