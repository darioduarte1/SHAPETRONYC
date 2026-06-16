import { useEffect, useState } from "react";

function App() {
  const [exercises, setExercises] = useState([]);
  const [selectedExercise, setSelectedExercise] = useState("");
  const [weight, setWeight] = useState("");
  const [reps, setReps] = useState("");
  const [rir, setRir] = useState("");
  const [isFailure, setIsFailure] = useState(false);
  const [recommendation, setRecommendation] = useState(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/exercises/")
      .then((response) => response.json())
      .then((data) => setExercises(data));
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();

    const response = await fetch("http://127.0.0.1:8000/api/recommendations/next-set/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        weight: Number(weight),
        reps: Number(reps),
        rir: rir === "" ? null : Number(rir),
        is_failure: isFailure,
      }),
    });

    const data = await response.json();
    setRecommendation(data);
  }

  return (
    <div style={{ padding: "24px", maxWidth: "600px", margin: "0 auto" }}>
      <h1>SHAPETRONYC</h1>

      <h2>Registar Série</h2>

      <form onSubmit={handleSubmit}>
        <label>Exercício</label>
        <select
          value={selectedExercise}
          onChange={(e) => setSelectedExercise(e.target.value)}
          style={{ display: "block", width: "100%", marginBottom: "12px" }}
        >
          <option value="">Selecionar exercício</option>

          {exercises.map((exercise) => (
            <option key={exercise.id} value={exercise.id}>
              {exercise.name}
            </option>
          ))}
        </select>

        <label>Peso</label>
        <input
          type="number"
          value={weight}
          onChange={(e) => setWeight(e.target.value)}
          style={{ display: "block", width: "100%", marginBottom: "12px" }}
        />

        <label>Reps</label>
        <input
          type="number"
          value={reps}
          onChange={(e) => setReps(e.target.value)}
          style={{ display: "block", width: "100%", marginBottom: "12px" }}
        />

        <label>RIR</label>
        <input
          type="number"
          value={rir}
          onChange={(e) => setRir(e.target.value)}
          style={{ display: "block", width: "100%", marginBottom: "12px" }}
        />

        <label>
          <input
            type="checkbox"
            checked={isFailure}
            onChange={(e) => setIsFailure(e.target.checked)}
          />
          Falha
        </label>

        <button type="submit" style={{ display: "block", marginTop: "16px" }}>
          Calcular Próxima Série
        </button>
      </form>

      {recommendation && (
        <div style={{ marginTop: "24px", padding: "16px", border: "1px solid #ccc" }}>
          <h2>Próxima Série</h2>
          <p><strong>Peso recomendado:</strong> {recommendation.recommended_weight} kg</p>
          <p><strong>Reps alvo:</strong> {recommendation.target_reps}</p>
          <p><strong>Motivo:</strong> {recommendation.reason}</p>
        </div>
      )}
    </div>
  );
}

export default App;