// =============================================================================
// ExerciseHeader.jsx
// -----------------------------------------------------------------------------
// Componente visual do cabeçalho de um exercício.
// É usado pelo ExerciseCard para mostrar imagem, nome, metadados, estado de
// calibração e botões de trocar exercício ou configurar escala da máquina.
// Mantém a zona superior do exercício isolada do corpo de treino.
// =============================================================================

export default function ExerciseHeader({
  exercise,
  imageUrl,
  isOpen,
  needsCalibration,
  hasLoggedSets,
  isReplacing,
  isSavingWeightScale,
  toggleExercise,
  toggleExerciseSubstitutions,
  toggleWeightScaleMenu,
}) {
  return (
    <div className="exercise-row-shell">
      <button
        className="exercise-main-button"
        onClick={() => toggleExercise(exercise)}
      >
        <img
          className="exercise-row-image"
          src={imageUrl}
          alt={exercise.exercise_localized_name || exercise.exercise_name}
        />
        <span className="exercise-row-copy">
          <span className="exercise-row-title">
            <span aria-hidden="true">{isOpen ? "▼" : "▶"}</span>
            {exercise.exercise_name}
          </span>
          <span className="exercise-row-meta">
            {exercise.exercise_localized_name || exercise.exercise_muscle_group}
            {" · "}
            {exercise.exercise_muscle_group}
            {" · "}
            {exercise.exercise_equipment}
            {needsCalibration ? " · Calibração necessária" : ""}
          </span>
        </span>
      </button>

      <button
        className="exercise-replace-button"
        onClick={() => toggleExerciseSubstitutions(exercise)}
        disabled={hasLoggedSets || isReplacing}
        title={hasLoggedSets ? "Termina este exercício antes de trocar." : "Trocar por outro exercício do mesmo grupo muscular"}
      >
        {isReplacing ? "A trocar..." : "Trocar"}
      </button>

      <button
        className="exercise-scale-button"
        onClick={() => toggleWeightScaleMenu(exercise)}
        disabled={isSavingWeightScale}
        title="Configurar placas e bolachas desta máquina"
      >
        Escala
      </button>
    </div>
  );
}
