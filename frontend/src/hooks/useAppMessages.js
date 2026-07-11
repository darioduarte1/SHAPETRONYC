// =============================================================================
// useAppMessages.js
// -----------------------------------------------------------------------------
// Hook responsável pelas mensagens internas da aplicação.
// É usado pelo App.jsx para substituir alertas nativos do browser por avisos
// visíveis dentro da UI, sem bloquear treino, calibração ou navegação.
// Expõe helpers simples para mensagens de erro, sucesso e informação.
// =============================================================================
import { useCallback, useState } from "react";

function buildMessage(type, title, detail = "") {
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    type,
    title,
    detail,
  };
}

export default function useAppMessages() {
  const [messages, setMessages] = useState([]);

  const pushMessage = useCallback((type, title, detail = "") => {
    setMessages((currentMessages) => [
      buildMessage(type, title, detail),
      ...currentMessages.slice(0, 3),
    ]);
  }, []);

  const dismissMessage = useCallback((messageId) => {
    setMessages((currentMessages) =>
      currentMessages.filter((message) => message.id !== messageId)
    );
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    dismissMessage,
    clearMessages,
    notifyError: useCallback(
      (title, detail = "") => pushMessage("error", title, detail),
      [pushMessage]
    ),
    notifySuccess: useCallback(
      (title, detail = "") => pushMessage("success", title, detail),
      [pushMessage]
    ),
    notifyInfo: useCallback(
      (title, detail = "") => pushMessage("info", title, detail),
      [pushMessage]
    ),
  };
}
