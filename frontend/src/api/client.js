// =============================================================================
// client.js
// -----------------------------------------------------------------------------
// Cliente base da API usado por todos os módulos de frontend/src/api.
// Centraliza o URL do backend, o envio de JSON, leitura de respostas e erros HTTP.
// Evita que componentes React tenham de repetir fetch, headers e parsing manual.
// =============================================================================
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(message, { status, data } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export async function apiRequest(path, options = {}) {
  const { body, headers, parseAs = "json", ...fetchOptions } = options;
  const requestOptions = {
    ...fetchOptions,
    headers: {
      ...(body !== undefined && !(body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
      ...(headers || {}),
    },
  };

  if (body !== undefined) {
    requestOptions.body = body instanceof FormData ? body : JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, requestOptions);

  if (parseAs === "blob") {
    if (!response.ok) {
      throw new ApiError("API request failed", {
        status: response.status,
        data: await readErrorData(response),
      });
    }

    return response.blob();
  }

  const data = await readJsonData(response);

  if (!response.ok) {
    throw new ApiError("API request failed", {
      status: response.status,
      data,
    });
  }

  return data;
}

async function readJsonData(response) {
  const text = await response.text();

  if (!text) {
    return null;
  }

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

async function readErrorData(response) {
  try {
    return await readJsonData(response);
  } catch {
    return null;
  }
}
