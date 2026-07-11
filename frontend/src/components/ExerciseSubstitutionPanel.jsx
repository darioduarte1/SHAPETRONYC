// =============================================================================
// ExerciseSubstitutionPanel.jsx
// -----------------------------------------------------------------------------
// Componente visual para trocar um exercício por outro.
// É usado dentro do ExerciseCard quando o atleta abre a zona de substituição.
// Mostra alternativas compatíveis e chama a ação de substituição recebida por props.
// =============================================================================
export default function ExerciseSubstitutionPanel({
  exercise,
  isOpen,
  hasLoggedSets,
  substitutionData,
  isReplacing,
  replaceExercise,
}) {
  if (!isOpen || hasLoggedSets) {
    return null;
  }

  return (
    <div className="exercise-substitution-panel">
      <div className="exercise-substitution-header">
        <strong>Alternativas para {exercise.exercise_muscle_group}</strong>
        <span>Só aparecem exercícios do mesmo grupo muscular.</span>
      </div>

      {!substitutionData && (
        <p className="exercise-substitution-empty">A carregar alternativas...</p>
      )}

      {substitutionData?.options?.length === 0 && (
        <p className="exercise-substitution-empty">
          Ainda não existem alternativas registadas para este grupo.
        </p>
      )}

      <div className="exercise-option-grid">
        {substitutionData?.options?.map((option) => (
          <button
            key={option.id}
            className="exercise-option-card"
            onClick={() => replaceExercise(exercise, option.id)}
            disabled={isReplacing}
          >
            <img
              src={option.image_url || "/exercise-screens/IMG_3620.PNG"}
              alt={option.localized_name || option.name}
            />
            <span>
              <strong>{option.name}</strong>
              <small>{option.localized_name || option.equipment}</small>
              <small>{option.equipment} · {option.movement_pattern}</small>
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
