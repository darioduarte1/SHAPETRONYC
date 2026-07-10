// =============================================================================
// recommendationsApi.js
// -----------------------------------------------------------------------------
// Funções de acesso aos endpoints de recomendação e decisão da IA.
// É usado pelo App.jsx após cada série para pedir ao backend a próxima decisão
// de treino, incluindo carga, reps, tipo de série e estado do exercício.
// Deixa os componentes livres de detalhes de URL e fetch.
// =============================================================================
import { apiRequest } from "./client";

export function getNextSetRecommendation(payload) {
  return apiRequest("/api/recommendations/next-set/", {
    method: "POST",
    body: payload,
  });
}
