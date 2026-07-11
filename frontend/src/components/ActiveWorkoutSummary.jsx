// =============================================================================
// ActiveWorkoutSummary.jsx
// -----------------------------------------------------------------------------
// Componente visual do resumo de um treino ativo.
// É usado pelo WorkoutCard para mostrar a sessão aberta, volume acumulado,
// séries concluídas, notas finais e ação de terminar o treino.
// Mantém o painel de sessão separado da listagem de exercícios.
// =============================================================================

export default function ActiveWorkoutSummary({
  activeSessionId,
  workout,
  workoutStats,
  sessionNote,
  setSessionNote,
  finishWorkoutSession,
}) {
  return (
    <div className="active-workout-summary">
      <p>Workout session active. Session ID: {activeSessionId}</p>
      <div className="active-workout-metrics">
        <div>
          <strong>Volume</strong>
          <p>{workoutStats.volume.toFixed(1)} kg</p>
        </div>
        <div>
          <strong>Séries concluídas</strong>
          <p>{workoutStats.sets}</p>
        </div>
      </div>

      <textarea
        placeholder="Final workout notes"
        value={sessionNote || ""}
        onChange={(event) => setSessionNote(workout.id, event.target.value)}
      />

      <button onClick={() => finishWorkoutSession(workout)}>
        Finish Workout
      </button>
    </div>
  );
}
