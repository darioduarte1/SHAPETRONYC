// =============================================================================
// progressionApi.js
// -----------------------------------------------------------------------------
// Funções de acesso aos endpoints de progressão e séries executadas.
// É usado pelo App.jsx para carregar histórico de exercício, guardar séries e
// desfazer registos quando o utilizador corrige um treino.
// Mantém a camada de dados separada da UI.
// =============================================================================
import { apiRequest } from "./client";

export function getExerciseHistory(params) {
  return apiRequest(`/api/progression/exercise-history/?${new URLSearchParams(params)}`);
}

export function createSetLog(payload) {
  return apiRequest("/api/progression/set-logs/", {
    method: "POST",
    body: payload,
  });
}

export function deleteSetLog(setLogId) {
  return apiRequest(`/api/progression/set-logs/${setLogId}/`, {
    method: "DELETE",
  });
}
