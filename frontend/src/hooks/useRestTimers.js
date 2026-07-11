// =============================================================================
// useRestTimers.js
// -----------------------------------------------------------------------------
// Hook responsável pelos temporizadores de descanso no frontend.
// É usado pelo App.jsx e pela calibração para iniciar, ajustar e limpar contagens
// regressivas entre séries normais ou experimentais.
// Centraliza o intervalo de atualização para não ficar misturado na UI principal.
// =============================================================================
import { useEffect, useState } from "react";

export default function useRestTimers() {
  const [restTimers, setRestTimers] = useState({});

  useEffect(() => {
    const hasRunningTimer = Object.values(restTimers).some((seconds) => seconds > 0);

    if (!hasRunningTimer) {
      return;
    }

    const timerId = window.setInterval(() => {
      setRestTimers((currentTimers) =>
        Object.fromEntries(
          Object.entries(currentTimers).map(([exerciseId, seconds]) => [
            exerciseId,
            Math.max(0, seconds - 1),
          ])
        )
      );
    }, 1000);

    return () => window.clearInterval(timerId);
  }, [restTimers]);

  function formatTimer(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    return `${minutes}min ${String(seconds).padStart(2, "0")}s`;
  }

  function adjustRestTimer(exerciseId, secondsDelta) {
    setRestTimers((currentTimers) => ({
      ...currentTimers,
      [exerciseId]: Math.max(0, (currentTimers[exerciseId] || 0) + secondsDelta),
    }));
  }

  return {
    restTimers,
    setRestTimers,
    formatTimer,
    adjustRestTimer,
  };
}
