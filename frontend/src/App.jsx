import { useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [step, setStep] = useState(1);
  const [profileId, setProfileId] = useState(null);
  const [userId, setUserId] = useState(null);
  const [program, setProgram] = useState(null);
  const [setForms, setSetForms] = useState({});
  const [savedSets, setSavedSets] = useState([]);
  const [recommendations, setRecommendations] = useState({});
  const [activeSessionByWorkout, setActiveSessionByWorkout] = useState({});
  const [sessionNotes, setSessionNotes] = useState({});

  const [form, setForm] = useState({
    username: "",
    gender: "MALE",
    age: 34,
    height_cm: 172,
    weight_kg: 72,
    goal: "HYPERTROPHY",
    level: "INTERMEDIATE",
    training_experience: "ONE_TO_THREE",
    days_per_week: 5,
  });

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  function updateSetForm(trainingExerciseId, field, value) {
    setSetForms({
      ...setForms,
      [trainingExerciseId]: {
        ...setForms[trainingExerciseId],
        [field]: value,
      },
    });
  }

  async function createProfile(e) {
    e.preventDefault();

    const userResponse = await fetch(`${API_BASE_URL}/api/accounts/create-user/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: form.username }),
    });

    const userData = await userResponse.json();
    setUserId(userData.id);

    const profileResponse = await fetch(`${API_BASE_URL}/api/accounts/profiles/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user: userData.id,
        gender: form.gender,
        age: Number(form.age),
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        goal: form.goal,
        level: form.level,
        training_experience: form.training_experience,
        days_per_week: Number(form.days_per_week),
      }),
    });

    const profileData = await profileResponse.json();

    setProfileId(profileData.id);
    setStep(3);
  }

  async function generateProgram() {
    const response = await fetch(`${API_BASE_URL}/api/training/generate-program/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile_id: profileId }),
    });

    const data = await response.json();
    setProgram(data);
    setStep(4);
  }

  async function startWorkoutSession(workout) {
    const response = await fetch(`${API_BASE_URL}/api/training/start-session/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile_id: profileId,
        workout_id: workout.id,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      alert("Erro ao iniciar treino.");
      return;
    }

    setActiveSessionByWorkout({
      ...activeSessionByWorkout,
      [workout.id]: data.id,
    });
  }

  async function finishWorkoutSession(workout) {
    const sessionId = activeSessionByWorkout[workout.id];

    if (!sessionId) {
      alert("Não existe sessão ativa para este treino.");
      return;
    }

    const response = await fetch(`${API_BASE_URL}/api/training/finish-session/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        notes: sessionNotes[workout.id] || "",
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      alert("Erro ao terminar treino.");
      return;
    }

    setActiveSessionByWorkout({
      ...activeSessionByWorkout,
      [workout.id]: null,
    });

    alert(`Workout finished: ${data.workout_name}`);
  }

  async function saveSet(exercise) {
    const formData = setForms[exercise.id] || {};
    const sessionId = activeSessionByWorkout[exercise.workout];

    if (!sessionId) {
      alert("Primeiro tens de iniciar o treino com Start Workout.");
      return;
    }

    if (!formData.weight_used || !formData.reps_completed) {
      alert("Preenche pelo menos o peso usado e as reps realizadas.");
      return;
    }

    if (!formData.reached_failure && formData.rir === undefined) {
      alert("Se não chegaste à falha, tens de indicar o RIR.");
      return;
    }

    const response = await fetch(`${API_BASE_URL}/api/progression/set-logs/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user: userId,
        workout_session: sessionId,
        training_exercise: exercise.id,
        exercise: exercise.exercise,
        set_number: Number(formData.set_number || 1),
        planned_weight: formData.planned_weight ? Number(formData.planned_weight) : null,
        weight_used: Number(formData.weight_used),
        target_min_reps: exercise.target_min_reps,
        target_max_reps: exercise.target_max_reps,
        reps_completed: Number(formData.reps_completed),
        rir: formData.reached_failure ? null : Number(formData.rir),
        reached_failure: Boolean(formData.reached_failure),
        notes: formData.notes || "",
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      alert("Erro ao guardar a série. Vê a consola.");
      return;
    }

    setSavedSets([...savedSets, data]);

    const recommendationResponse = await fetch(`${API_BASE_URL}/api/recommendations/next-set/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        weight: Number(formData.weight_used),
        reps: Number(formData.reps_completed),
        rir: formData.reached_failure ? null : Number(formData.rir),
        is_failure: Boolean(formData.reached_failure),
        notes: formData.notes || "",
      }),
    });

    const recommendationData = await recommendationResponse.json();

    setRecommendations({
      ...recommendations,
      [exercise.id]: recommendationData,
    });

    setSetForms({
      ...setForms,
      [exercise.id]: {
        ...formData,
        set_number: Number(formData.set_number || 1) + 1,
        reps_completed: "",
        rir: "",
        notes: "",
      },
    });
  }

  function wasSetSaved(trainingExerciseId) {
    return savedSets.some((set) => set.training_exercise === trainingExerciseId);
  }

  return (
    <div style={{ padding: "24px", maxWidth: "850px", margin: "0 auto" }}>
      <h1>SHAPETRONYC</h1>

      {step === 1 && (
        <div>
          <h2>Adaptive training built around you</h2>
          <p>Create your profile and SHAPETRONYC will generate your first training program.</p>
          <button onClick={() => setStep(2)}>Get Started</button>
        </div>
      )}

      {step === 2 && (
        <form onSubmit={createProfile}>
          <h2>Create Profile</h2>

          <label>Username</label>
          <input name="username" value={form.username} onChange={handleChange} required />

          <label>Gender</label>
          <select name="gender" value={form.gender} onChange={handleChange}>
            <option value="MALE">Male</option>
            <option value="FEMALE">Female</option>
          </select>

          <label>Age</label>
          <input name="age" type="number" value={form.age} onChange={handleChange} />

          <label>Height cm</label>
          <input name="height_cm" type="number" value={form.height_cm} onChange={handleChange} />

          <label>Weight kg</label>
          <input name="weight_kg" type="number" value={form.weight_kg} onChange={handleChange} />

          <label>Goal</label>
          <select name="goal" value={form.goal} onChange={handleChange}>
            <option value="HYPERTROPHY">Gain muscle</option>
            <option value="STRENGTH">Gain strength</option>
            <option value="FAT_LOSS">Lose fat</option>
            <option value="RECOMPOSITION">Recomposition</option>
            <option value="GENERAL_FITNESS">General fitness</option>
          </select>

          <label>Level</label>
          <select name="level" value={form.level} onChange={handleChange}>
            <option value="BEGINNER">Beginner</option>
            <option value="INTERMEDIATE">Intermediate</option>
            <option value="ADVANCED">Advanced</option>
          </select>

          <p><strong>Beginner:</strong> less volume, focus on technique and consistency.</p>
          <p><strong>Intermediate:</strong> more volume, higher frequency and harder progression.</p>
          <p><strong>Advanced:</strong> more specialization, higher fatigue and recovery demands.</p>

          <label>Training Experience</label>
          <select name="training_experience" value={form.training_experience} onChange={handleChange}>
            <option value="LESS_THAN_1">Less than 1 year</option>
            <option value="ONE_TO_THREE">1-3 years</option>
            <option value="THREE_TO_FIVE">3-5 years</option>
            <option value="MORE_THAN_FIVE">More than 5 years</option>
          </select>

          <label>Days per week</label>
          <select name="days_per_week" value={form.days_per_week} onChange={handleChange}>
            {[2, 3, 4, 5, 6, 7].map((day) => (
              <option key={day} value={day}>{day}</option>
            ))}
          </select>

          <button type="submit">Create Profile</button>
        </form>
      )}

      {step === 3 && (
        <div>
          <h2>Profile created</h2>
          <button onClick={generateProgram}>Generate My Program</button>
        </div>
      )}

      {step === 4 && program && (
        <div>
          <h2>{program.name}</h2>

          {program.workouts.map((workout) => {
            const activeSessionId = activeSessionByWorkout[workout.id];

            return (
              <div key={workout.id} style={{ border: "1px solid #ccc", padding: "16px", marginTop: "16px" }}>
                <h3>Day {workout.order} - {workout.name}</h3>

                {!activeSessionId ? (
                  <button onClick={() => startWorkoutSession(workout)}>
                    Start Workout
                  </button>
                ) : (
                  <div style={{ marginBottom: "16px" }}>
                    <p style={{ color: "green" }}>Workout session active. Session ID: {activeSessionId}</p>

                    <textarea
                      placeholder="Final workout notes"
                      value={sessionNotes[workout.id] || ""}
                      onChange={(e) =>
                        setSessionNotes({
                          ...sessionNotes,
                          [workout.id]: e.target.value,
                        })
                      }
                      style={{ display: "block", width: "100%", marginTop: "8px" }}
                    />

                    <button onClick={() => finishWorkoutSession(workout)} style={{ marginTop: "8px" }}>
                      Finish Workout
                    </button>
                  </div>
                )}

                {workout.exercises.map((item) => {
                  const currentForm = setForms[item.id] || {};
                  const reachedFailure = Boolean(currentForm.reached_failure);

                  return (
                    <div key={item.id} style={{ borderBottom: "1px solid #ddd", padding: "16px 0" }}>
                      <strong>{item.exercise_name}</strong>

                      <p>
                        Target: {item.sets} sets | {item.target_min_reps}-{item.target_max_reps} reps | RIR {item.target_rir}
                      </p>

                      <input
                        type="number"
                        placeholder="Set number"
                        value={currentForm.set_number || ""}
                        onChange={(e) => updateSetForm(item.id, "set_number", e.target.value)}
                      />

                      <input
                        type="number"
                        placeholder="Planned weight"
                        value={currentForm.planned_weight || ""}
                        onChange={(e) => updateSetForm(item.id, "planned_weight", e.target.value)}
                      />

                      <input
                        type="number"
                        placeholder="Weight used"
                        value={currentForm.weight_used || ""}
                        onChange={(e) => updateSetForm(item.id, "weight_used", e.target.value)}
                      />

                      <input
                        type="number"
                        placeholder="Reps completed"
                        value={currentForm.reps_completed || ""}
                        onChange={(e) => updateSetForm(item.id, "reps_completed", e.target.value)}
                      />

                      <label style={{ display: "block", marginTop: "8px" }}>
                        <input
                          type="checkbox"
                          checked={reachedFailure}
                          onChange={(e) => updateSetForm(item.id, "reached_failure", e.target.checked)}
                        />
                        Reached failure
                      </label>

                      {!reachedFailure && (
                        <input
                          type="number"
                          placeholder="RIR"
                          value={currentForm.rir || ""}
                          onChange={(e) => updateSetForm(item.id, "rir", e.target.value)}
                        />
                      )}

                      <textarea
                        placeholder="Notes for AI feedback"
                        value={currentForm.notes || ""}
                        onChange={(e) => updateSetForm(item.id, "notes", e.target.value)}
                        style={{ display: "block", width: "100%", marginTop: "8px" }}
                      />

                      <button onClick={() => saveSet(item)} style={{ marginTop: "8px" }}>
                        Save Set
                      </button>

                      {wasSetSaved(item.id) && (
                        <p style={{ color: "green" }}>At least one set saved for this exercise.</p>
                      )}

                      {recommendations[item.id] && (
                        <div style={{ marginTop: "8px", padding: "12px", border: "1px solid #999" }}>
                          <strong>Next set recommendation</strong>
                          <p>Weight: {recommendations[item.id].recommended_weight} kg</p>
                          <p>Target reps: {recommendations[item.id].target_reps}</p>
                          <p>Reason: {recommendations[item.id].reason}</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default App;