// =============================================================================
// accountsApi.js
// -----------------------------------------------------------------------------
// Funções de acesso aos endpoints de contas e perfis de atleta.
// É usado pelo App.jsx para criar utilizadores, criar/listar perfis, exportar
// histórico e limpar atletas experimentais durante esta fase de testes.
// Mantém os URLs de accounts fora dos componentes React.
// =============================================================================
import { apiRequest } from "./client";

export function createUser(payload) {
  return apiRequest("/api/accounts/create-user/", {
    method: "POST",
    body: payload,
  });
}

export function listProfiles() {
  return apiRequest("/api/accounts/profiles/");
}

export function createProfile(payload) {
  return apiRequest("/api/accounts/profiles/", {
    method: "POST",
    body: payload,
  });
}

export function exportProfileHistory(profileId) {
  return apiRequest(`/api/accounts/profiles/${profileId}/export/`, {
    parseAs: "blob",
  });
}

export function deleteExperimentalUsers() {
  return apiRequest("/api/accounts/experimental/delete-users/", {
    method: "DELETE",
  });
}
