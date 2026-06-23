import { useEffect, useState } from "react";

const API_BASE_URL = "http://127.0.0.1:8000";
const DEFAULT_REST_SECONDS = 120;
const TARGET_REPS = 12;

const SET_TYPES = [
  { value: "WARMUP", label: "Aquecimento", shortLabel: "W", color: "#eab308" },
  { value: "WORKING", label: "Normal", shortLabel: "N", color: "#f8fafc" },
  { value: "DROP", label: "Drop", shortLabel: "D", color: "#ef4444" },
];

const EFFORT_OPTIONS = [
  { value: "FAILURE", label: "FALHA", color: "#ef4444", reachedFailure: true, rir: null },
  { value: "RIR_0_1", label: "RIR 0/1", color: "#f97316", reachedFailure: false, rir: 1 },
  { value: "RIR_2_3", label: "RIR 2/3", color: "#eab308", reachedFailure: false, rir: 2 },
  { value: "RIR_4_PLUS", label: "RIR 4+", color: "#22c55e", reachedFailure: false, rir: 4 },
];

function App() {
  const [step, setStep] = useState(1);
  const [profileId, setProfileId] = useState(null);
  const [userId, setUserId] = useState(null);
  const [program, setProgram] = useState(null);
  const [setForms, setSetForms] = useState({});
  const [recommendations, setRecommendations] = useState({});
  const [activeSessionByWorkout, setActiveSessionByWorkout] = useState({});
  const [sessionNotes, setSessionNotes] = useState({});
  const [openExerciseById, setOpenExerciseById] = useState({});
  const [openWorkoutId, setOpenWorkoutId] = useState(null);
  const [exerciseLogsById, setExerciseLogsById] = useState({});
  const [exerciseRowCounts, setExerciseRowCounts] = useState({});
  const [restTimers, setRestTimers] = useState({});
  const [openCompletionMenuBySet, setOpenCompletionMenuBySet] = useState({});
  const [openRestMenuBySet, setOpenRestMenuBySet] = useState({});
  const [openSetTypeMenuBySet, setOpenSetTypeMenuBySet] = useState({});
  const [removedSetByKey, setRemovedSetByKey] = useState({});

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

  function getActiveWorkoutId() {
    return Object.keys(activeSessionByWorkout).find((workoutId) =>
      Boolean(activeSessionByWorkout[workoutId])
    );
  }

  function getSetFormKey(trainingExerciseId, setNumber) {
    return `${trainingExerciseId}-${setNumber}`;
  }

  function getSetTypeMeta(setType) {
    return SET_TYPES.find((type) => type.value === setType) || SET_TYPES[1];
  }

  function getEffortMetaFromSet(setLog) {
    if (!setLog) {
      return null;
    }

    if (setLog.reached_failure) {
      return EFFORT_OPTIONS[0];
    }

    if (setLog.rir === null || setLog.rir === undefined) {
      return null;
    }

    if (setLog.rir <= 1) {
      return EFFORT_OPTIONS[1];
    }

    if (setLog.rir <= 3) {
      return EFFORT_OPTIONS[2];
    }

    return EFFORT_OPTIONS[3];
  }

  function getExerciseLogs(trainingExerciseId) {
    return exerciseLogsById[trainingExerciseId] || {
      previous_sets: [],
      current_sets: [],
      previous_session: null,
      recommended_sets: [],
    };
  }

  function getCurrentSetForRow(trainingExerciseId, setNumber) {
    return getExerciseLogs(trainingExerciseId).current_sets.find(
      (setLog) => Number(setLog.set_number) === setNumber
    );
  }

  function getPreviousSetForRow(trainingExerciseId, setNumber) {
    return getExerciseLogs(trainingExerciseId).previous_sets[setNumber - 1];
  }

  function getRecommendedSetForRow(trainingExerciseId, setNumber) {
    const recommendedSet = getExerciseLogs(trainingExerciseId).recommended_sets.find(
      (setRecommendation) => Number(setRecommendation.set_number) === setNumber
    );

    return {
      weight: recommendedSet?.recommended_weight ?? "",
      reps: recommendedSet?.recommended_reps ?? "",
      reason: recommendedSet?.reason ?? "",
    };
  }

  function getWarmupReferenceSet(trainingExerciseId, setNumber) {
    const previousSet = getPreviousSetForRow(trainingExerciseId, setNumber);

    return previousSet?.set_type === "WARMUP" ? previousSet : null;
  }

  function getExerciseRowCount(exercise) {
    const logs = getExerciseLogs(exercise.id);

    return Math.max(
      exerciseRowCounts[exercise.id] || 0,
      exercise.sets,
      logs.previous_sets.length,
      logs.current_sets.length,
      1
    );
  }

  function getExerciseRows(exercise) {
    const rowCount = getExerciseRowCount(exercise);
    const visibleSourceRows = Array.from({ length: rowCount }, (_, index) => index + 1).filter((sourceSetNumber) => {
      const setFormKey = getSetFormKey(exercise.id, sourceSetNumber);

      return !removedSetByKey[setFormKey];
    });

    return visibleSourceRows.map((sourceSetNumber, index) => ({
      sourceSetNumber,
      displaySetNumber: index + 1,
    }));
  }

  function getSetTypeForExerciseRow(exercise, sourceSetNumber, displaySetNumber) {
    const setFormKey = getSetFormKey(exercise.id, sourceSetNumber);
    const currentSet = getCurrentSetForRow(exercise.id, displaySetNumber);
    const previousSet = getPreviousSetForRow(exercise.id, sourceSetNumber);
    const hasCurrentSets = getExerciseLogs(exercise.id).current_sets.length > 0;

    if (!currentSet && !setForms[setFormKey]?.set_type && !hasCurrentSets && sourceSetNumber === 1) {
      return "WARMUP";
    }

    return currentSet?.set_type || setForms[setFormKey]?.set_type || previousSet?.set_type || "WORKING";
  }

  function getVisibleSetLabel(exercise, rows, sourceSetNumber, displaySetNumber) {
    const rowSetType = getSetTypeForExerciseRow(exercise, sourceSetNumber, displaySetNumber);
    const sameTypeRows = rows.filter((row) =>
      getSetTypeForExerciseRow(exercise, row.sourceSetNumber, row.displaySetNumber) === rowSetType
    );
    const sameTypeIndex = sameTypeRows.findIndex((row) => row.sourceSetNumber === sourceSetNumber) + 1;

    if (rowSetType === "WARMUP") {
      return sameTypeRows.length > 1 ? `W${sameTypeIndex}` : "W";
    }

    if (rowSetType === "DROP") {
      return sameTypeRows.length > 1 ? `D${sameTypeIndex}` : "D";
    }

    return String(sameTypeIndex);
  }

  function getPlannedValuesForExerciseRow(exercise, sourceSetNumber, displaySetNumber) {
    const rowSetType = getSetTypeForExerciseRow(exercise, sourceSetNumber, displaySetNumber);

    if (rowSetType === "WARMUP") {
      const warmupReferenceSet = getWarmupReferenceSet(exercise.id, sourceSetNumber);

      return {
        weight: warmupReferenceSet?.weight_used ?? "",
        reps: warmupReferenceSet?.reps_completed ?? "",
        reason: "",
      };
    }

    return getRecommendedSetForRow(exercise.id, sourceSetNumber);
  }

  function shouldForceFailureEffort(setType, repsCompleted) {
    return setType === "WORKING" && Number(repsCompleted) < TARGET_REPS;
  }

  function getEffortOptionsForSet(setType, repsCompleted) {
    return shouldForceFailureEffort(setType, repsCompleted) ? [EFFORT_OPTIONS[0]] : EFFORT_OPTIONS;
  }

  function formatTimer(totalSeconds) {
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    return `${minutes}min ${String(seconds).padStart(2, "0")}s`;
  }

  function getRestSecondsForRow(setFormKey) {
    return Number(setForms[setFormKey]?.rest_seconds || DEFAULT_REST_SECONDS);
  }

  function formatPreviousSet(setLog) {
    if (!setLog) {
      return "-";
    }

    const effortMeta = getEffortMetaFromSet(setLog);
    const effortLabel = effortMeta ? ` ${effortMeta.label}` : "";

    return `${setLog.weight_used}kg x ${setLog.reps_completed}${effortLabel}`;
  }

  function getNextExerciseRow(exercise, rows) {
    return rows.find((row) => !getCurrentSetForRow(exercise.id, row.displaySetNumber));
  }

  function getGuidanceForExercise(exercise, rows, restSeconds) {
    if (restSeconds > 0) {
      return {
        eyebrow: "Descanso",
        title: "Aguarda antes da próxima série",
        message: "Respira, recupera a técnica e prepara a próxima execução.",
        isResting: true,
      };
    }

    const nextRow = getNextExerciseRow(exercise, rows);

    if (!nextRow) {
      return {
        eyebrow: "Exercício concluído",
        title: "Todas as séries deste exercício estão registadas",
        message: "Segue para o próximo exercício quando te sentires pronto.",
        isResting: false,
      };
    }

    const rowSetType = getSetTypeForExerciseRow(exercise, nextRow.sourceSetNumber, nextRow.displaySetNumber);
    const visibleSetLabel = getVisibleSetLabel(exercise, rows, nextRow.sourceSetNumber, nextRow.displaySetNumber);
    const plannedValues = getPlannedValuesForExerciseRow(exercise, nextRow.sourceSetNumber, nextRow.displaySetNumber);
    const warmupReferenceSet = getWarmupReferenceSet(exercise.id, nextRow.sourceSetNumber);
    const latestRecommendation = recommendations[exercise.id];
    const recommendedWeight = plannedValues.weight || latestRecommendation?.recommended_weight;
    const recommendedReps = plannedValues.reps || latestRecommendation?.target_reps;
    const hasLoadTarget = recommendedWeight !== "" && recommendedWeight !== undefined && recommendedReps;
    const loadCue = hasLoadTarget
      ? `Aponta para ${recommendedWeight}kg x ${recommendedReps} reps.`
      : `Trabalha com o objectivo de chegar às ${TARGET_REPS} reps.`;
    const warmupCue = warmupReferenceSet
      ? `Mantém a referência anterior de ${warmupReferenceSet.weight_used}kg x ${warmupReferenceSet.reps_completed} reps.`
      : `Sobe a carga gradualmente até sentires o movimento pronto.`;
    const reason =
      plannedValues.reason || latestRecommendation?.guidance_message || latestRecommendation?.reason || "";

    if (rowSetType === "WARMUP") {
      return {
        eyebrow: "Próximo passo",
        title: `Faz a série ${visibleSetLabel} de aquecimento`,
        message: `Usa uma carga controlada para preparar o movimento. ${warmupCue}`,
        reason: "",
        isResting: false,
      };
    }

    if (rowSetType === "DROP") {
      return {
        eyebrow: "Próximo passo",
        title: `Faz a série ${visibleSetLabel} em drop`,
        message: `Reduz a carga e mantém a execução limpa até ao alvo. ${loadCue}`,
        reason,
        isResting: false,
      };
    }

    return {
      eyebrow: "Próximo passo",
      title: `Faz a série ${visibleSetLabel}`,
      message: `Mantém o controlo e respeita o esforço planeado. ${loadCue}`,
      reason,
      isResting: false,
    };
  }

  function getWorkoutSessionStats(workout) {
    const workoutExercises = workout.exercises || [];
    const currentSets = workoutExercises.flatMap(
      (exercise) => getExerciseLogs(exercise.id).current_sets
    );
    const volume = currentSets.reduce(
      (total, setLog) => total + Number(setLog.weight_used) * Number(setLog.reps_completed),
      0
    );

    return {
      sets: currentSets.length,
      volume,
    };
  }

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  function updateSetForm(setFormKey, field, value) {
    setSetForms({
      ...setForms,
      [setFormKey]: {
        ...setForms[setFormKey],
        [field]: value,
      },
    });
  }

  function toggleWorkout(workoutId) {
    if (getActiveWorkoutId()) {
      return;
    }

    setOpenWorkoutId(openWorkoutId === workoutId ? null : workoutId);
  }

  async function toggleExercise(exercise) {
    const isOpening = !openExerciseById[exercise.id];

    setOpenExerciseById({
      ...openExerciseById,
      [exercise.id]: isOpening,
    });

    if (isOpening) {
      await loadExerciseHistory(exercise);
    }
  }

  function addExerciseRow(exercise) {
    setExerciseRowCounts({
      ...exerciseRowCounts,
      [exercise.id]: getExerciseRowCount(exercise) + 1,
    });
  }

  function removeExerciseRow(exercise, sourceSetNumber, displaySetNumber) {
    const setFormKey = getSetFormKey(exercise.id, sourceSetNumber);

    if (getCurrentSetForRow(exercise.id, displaySetNumber)) {
      return;
    }

    setRemovedSetByKey({
      ...removedSetByKey,
      [setFormKey]: true,
    });

    setSetForms((currentSetForms) => {
      const nextSetForms = { ...currentSetForms };
      delete nextSetForms[setFormKey];
      return nextSetForms;
    });

    setOpenRestMenuBySet({
      ...openRestMenuBySet,
      [setFormKey]: false,
    });

    setOpenCompletionMenuBySet({
      ...openCompletionMenuBySet,
      [setFormKey]: false,
    });

    setOpenSetTypeMenuBySet({
      ...openSetTypeMenuBySet,
      [setFormKey]: false,
    });
  }

  async function loadExerciseHistory(exercise, sessionIdOverride = null) {
    const sessionId = sessionIdOverride || activeSessionByWorkout[exercise.workout];

    if (!profileId || !sessionId) {
      return null;
    }

    const params = new URLSearchParams({
      profile_id: profileId,
      exercise_id: exercise.exercise,
      training_exercise_id: exercise.id,
      session_id: sessionId,
    });

    const response = await fetch(`${API_BASE_URL}/api/progression/exercise-history/?${params}`);
    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      return null;
    }

    setExerciseLogsById((currentLogs) => ({
      ...currentLogs,
      [exercise.id]: data,
    }));

    setExerciseRowCounts((currentCounts) => ({
      ...currentCounts,
      [exercise.id]: Math.max(
        currentCounts[exercise.id] || 0,
        exercise.sets,
        data.previous_sets.length,
        data.current_sets.length,
        1
      ),
    }));

    return data;
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
    setOpenWorkoutId(null);
    setExerciseLogsById({});
    setExerciseRowCounts({});
    setRemovedSetByKey({});
    setOpenSetTypeMenuBySet({});
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
    setOpenWorkoutId(workout.id);

    workout.exercises.forEach((exercise) => {
      loadExerciseHistory(exercise, data.id);
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
    setOpenWorkoutId(null);
    setOpenExerciseById({});
    setRestTimers({});
    setRemovedSetByKey({});
    setOpenSetTypeMenuBySet({});

    alert(`Workout finished: ${data.workout_name}`);
  }

  function toggleCompletionMenu(setFormKey) {
    setOpenCompletionMenuBySet({
      ...openCompletionMenuBySet,
      [setFormKey]: !openCompletionMenuBySet[setFormKey],
    });
  }

  function toggleRestMenu(setFormKey) {
    setOpenRestMenuBySet({
      ...openRestMenuBySet,
      [setFormKey]: !openRestMenuBySet[setFormKey],
    });
  }

  function adjustRestTimer(exerciseId, secondsDelta) {
    setRestTimers((currentTimers) => ({
      ...currentTimers,
      [exerciseId]: Math.max(0, (currentTimers[exerciseId] || 0) + secondsDelta),
    }));
  }

  function toggleSetTypeMenu(setFormKey) {
    setOpenSetTypeMenuBySet({
      ...openSetTypeMenuBySet,
      [setFormKey]: !openSetTypeMenuBySet[setFormKey],
    });
  }

  function selectSetType(setFormKey, setType) {
    updateSetForm(setFormKey, "set_type", setType);
    setOpenSetTypeMenuBySet({
      ...openSetTypeMenuBySet,
      [setFormKey]: false,
    });
  }

  async function saveSet(exercise, sourceSetNumber, displaySetNumber, effortOption) {
    const setFormKey = getSetFormKey(exercise.id, sourceSetNumber);
    const formData = setForms[setFormKey] || {};
    const sessionId = activeSessionByWorkout[exercise.workout];
    const previousSet = getPreviousSetForRow(exercise.id, sourceSetNumber);
    const setType = getSetTypeForExerciseRow(exercise, sourceSetNumber, displaySetNumber);
    const plannedValues = getPlannedValuesForExerciseRow(exercise, sourceSetNumber, displaySetNumber);
    const weightUsed = formData.weight_used ?? plannedValues.weight;
    const repsCompleted = formData.reps_completed ?? plannedValues.reps;
    const selectedEffortOption = shouldForceFailureEffort(setType, repsCompleted)
      ? EFFORT_OPTIONS[0]
      : effortOption || EFFORT_OPTIONS[2];
    const restSeconds = getRestSecondsForRow(setFormKey);

    if (!sessionId) {
      alert("Primeiro tens de iniciar o treino com Start Workout.");
      return;
    }

    if (weightUsed === "" || repsCompleted === "") {
      alert("Preenche o peso e as reps antes de confirmar a série.");
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
        set_number: displaySetNumber,
        set_type: setType,
        planned_weight: previousSet?.weight_used ?? null,
        weight_used: Number(weightUsed),
        target_min_reps: TARGET_REPS,
        target_max_reps: TARGET_REPS,
        reps_completed: Number(repsCompleted),
        rir: selectedEffortOption.reachedFailure ? null : selectedEffortOption.rir,
        reached_failure: selectedEffortOption.reachedFailure,
        notes: formData.notes || "",
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      console.error(data);
      alert("Erro ao guardar a série. Vê a consola.");
      return;
    }

    setExerciseLogsById((currentLogs) => {
      const currentExerciseLogs = currentLogs[exercise.id] || {
        previous_sets: [],
        current_sets: [],
        previous_session: null,
        recommended_sets: [],
      };
      const otherCurrentSets = currentExerciseLogs.current_sets.filter(
        (setLog) => Number(setLog.set_number) !== displaySetNumber
      );

      return {
        ...currentLogs,
        [exercise.id]: {
          ...currentExerciseLogs,
          current_sets: [...otherCurrentSets, data].sort(
            (firstSet, secondSet) => Number(firstSet.set_number) - Number(secondSet.set_number)
          ),
        },
      };
    });

    setRestTimers({
      ...restTimers,
      [exercise.id]: restSeconds,
    });

    setOpenCompletionMenuBySet({
      ...openCompletionMenuBySet,
      [setFormKey]: false,
    });

    setOpenRestMenuBySet({
      ...openRestMenuBySet,
      [setFormKey]: false,
    });

    setOpenSetTypeMenuBySet({
      ...openSetTypeMenuBySet,
      [setFormKey]: false,
    });

    const recommendationResponse = await fetch(`${API_BASE_URL}/api/recommendations/next-set/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        weight: Number(weightUsed),
        reps: Number(repsCompleted),
        rir: selectedEffortOption.reachedFailure ? null : selectedEffortOption.rir,
        is_failure: selectedEffortOption.reachedFailure,
        notes: formData.notes || "",
        set_type: setType,
      }),
    });

    const recommendationData = await recommendationResponse.json();

    if (recommendationResponse.ok) {
      setRecommendations({
        ...recommendations,
        [exercise.id]: recommendationData,
      });
    }
  }

  return (
    <div style={{ padding: "24px", maxWidth: "920px", margin: "0 auto" }}>
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
            const activeWorkoutId = getActiveWorkoutId();
            const activeSessionId = activeSessionByWorkout[workout.id];
            const isActiveWorkout = activeWorkoutId === String(workout.id);
            const hasActiveWorkout = Boolean(activeWorkoutId);
            const isWorkoutOpen = isActiveWorkout || openWorkoutId === workout.id;
            const workoutStats = getWorkoutSessionStats(workout);

            if (hasActiveWorkout && !isActiveWorkout) {
              return null;
            }

            return (
              <div
                key={workout.id}
                style={{ border: "1px solid #ccc", padding: "16px", marginTop: "16px" }}
              >
                <button
                  onClick={() => toggleWorkout(workout.id)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    padding: "12px",
                    fontSize: "18px",
                    fontWeight: "bold",
                    cursor: hasActiveWorkout ? "default" : "pointer",
                    background: "transparent",
                    border: "none",
                  }}
                >
                  {isWorkoutOpen ? "▼" : "▶"} Day {workout.order} - {workout.name}
                </button>

                {isWorkoutOpen && (
                  <div style={{ marginTop: "12px" }}>
                    {!activeSessionId ? (
                      <button onClick={() => startWorkoutSession(workout)}>
                        Start Workout
                      </button>
                    ) : (
                      <div style={{ marginBottom: "16px" }}>
                        <p style={{ color: "green" }}>Workout session active. Session ID: {activeSessionId}</p>
                        <div
                          style={{
                            display: "grid",
                            gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                            gap: "12px",
                            marginTop: "12px",
                          }}
                        >
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

                    {activeSessionId && workout.exercises.map((item) => {
                      const exerciseLogs = getExerciseLogs(item.id);
                      const isOpen = Boolean(openExerciseById[item.id]);
                      const restSeconds = restTimers[item.id] || 0;
                      const rows = getExerciseRows(item);
                      const guidance = getGuidanceForExercise(item, rows, restSeconds);

                      return (
                        <div
                          key={item.id}
                          style={{
                            borderBottom: "1px solid #ddd",
                            padding: "14px 0",
                          }}
                        >
                          <button
                            onClick={() => toggleExercise(item)}
                            style={{
                              width: "100%",
                              textAlign: "left",
                              padding: "12px",
                              fontSize: "16px",
                              fontWeight: "bold",
                              cursor: "pointer",
                            }}
                          >
                            {isOpen ? "▼" : "▶"} {item.exercise_name}
                          </button>

                          {isOpen && (
                            <div style={{ marginTop: "12px" }}>
                              <p>
                                Target: {item.sets} sets | {TARGET_REPS} reps | RIR {item.target_rir}
                              </p>

                              {exerciseLogs.previous_session && (
                                <p style={{ marginTop: "8px", color: "#777" }}>
                                  Anterior: {exerciseLogs.previous_session.workout_name}
                                </p>
                              )}

                              <div
                                style={{
                                  marginTop: "12px",
                                  padding: "16px",
                                  border: "1px solid #334155",
                                  borderRadius: "8px",
                                  background: "rgba(15, 23, 42, 0.78)",
                                }}
                              >
                                <div
                                  style={{
                                    color: guidance.isResting ? "#0ea5e9" : "#94a3b8",
                                    fontSize: "12px",
                                    fontWeight: "bold",
                                    letterSpacing: "0",
                                    textTransform: "uppercase",
                                  }}
                                >
                                  {guidance.eyebrow}
                                </div>
                                <strong
                                  style={{
                                    display: "block",
                                    marginTop: "6px",
                                    color: "#f8fafc",
                                    fontSize: "18px",
                                  }}
                                >
                                  {guidance.title}
                                </strong>
                                <p style={{ marginTop: "6px", color: "#cbd5e1" }}>{guidance.message}</p>

                                {guidance.reason && !guidance.isResting && (
                                  <p style={{ marginTop: "6px", color: "#94a3b8", fontSize: "13px" }}>
                                    {guidance.reason}
                                  </p>
                                )}

                                {guidance.isResting && (
                                  <div style={{ marginTop: "14px" }}>
                                    <div
                                      style={{
                                        color: "#0ea5e9",
                                        fontSize: "42px",
                                        fontWeight: "bold",
                                        lineHeight: "1",
                                      }}
                                    >
                                      {formatTimer(restSeconds)}
                                    </div>
                                    <div
                                      style={{
                                        display: "grid",
                                        gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                                        gap: "8px",
                                        marginTop: "12px",
                                      }}
                                    >
                                      <button type="button" onClick={() => adjustRestTimer(item.id, -15)}>
                                        -15s
                                      </button>
                                      <button type="button" onClick={() => adjustRestTimer(item.id, 15)}>
                                        +15s
                                      </button>
                                    </div>
                                  </div>
                                )}
                              </div>

                              <div style={{ overflowX: "auto", marginTop: "12px" }}>
                                <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "620px" }}>
                                  <thead>
                                    <tr style={{ color: "#777", textTransform: "uppercase", fontSize: "13px" }}>
                                      <th style={{ textAlign: "left", padding: "8px" }}>Série</th>
                                      <th style={{ textAlign: "left", padding: "8px" }}>Anterior</th>
                                      <th style={{ textAlign: "left", padding: "8px" }}>Kg</th>
                                      <th style={{ textAlign: "left", padding: "8px" }}>Reps</th>
                                      <th style={{ textAlign: "center", padding: "8px" }}>Feita</th>
                                    </tr>
                                  </thead>
                                  <tbody>
                                    {rows.map(({ sourceSetNumber, displaySetNumber }) => {
                                      const setFormKey = getSetFormKey(item.id, sourceSetNumber);
                                      const currentSet = getCurrentSetForRow(item.id, displaySetNumber);
                                      const previousSet = getPreviousSetForRow(item.id, sourceSetNumber);
                                      const rowForm = setForms[setFormKey] || {};
                                      const rowSetType = getSetTypeForExerciseRow(
                                        item,
                                        sourceSetNumber,
                                        displaySetNumber
                                      );
                                      const setTypeMeta = getSetTypeMeta(rowSetType);
                                      const visibleSetLabel = getVisibleSetLabel(
                                        item,
                                        rows,
                                        sourceSetNumber,
                                        displaySetNumber
                                      );
                                      const isCompleted = Boolean(currentSet);
                                      const effortMeta = getEffortMetaFromSet(currentSet);
                                      const restSecondsForRow = getRestSecondsForRow(setFormKey);
                                      const plannedValues = getPlannedValuesForExerciseRow(
                                        item,
                                        sourceSetNumber,
                                        displaySetNumber
                                      );
                                      const weightValue =
                                        currentSet?.weight_used ?? rowForm.weight_used ?? plannedValues.weight;
                                      const repsValue =
                                        currentSet?.reps_completed ??
                                        rowForm.reps_completed ??
                                        plannedValues.reps;
                                      const availableEffortOptions = getEffortOptionsForSet(rowSetType, repsValue);

                                      return (
                                        <tr
                                          key={sourceSetNumber}
                                          style={{
                                            background: displaySetNumber % 2 === 0 ? "rgba(148, 163, 184, 0.12)" : "transparent",
                                          }}
                                        >
                                          <td style={{ padding: "8px" }}>
                                            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                              <div style={{ position: "relative" }}>
                                                <button
                                                  type="button"
                                                  disabled={isCompleted}
                                                  onClick={() => toggleRestMenu(setFormKey)}
                                                  title="Configurar descanso"
                                                  style={{
                                                    width: "30px",
                                                    height: "30px",
                                                    borderRadius: "6px",
                                                    border: "1px solid #555",
                                                    background: "transparent",
                                                    color: "#999",
                                                    cursor: isCompleted ? "default" : "pointer",
                                                  }}
                                                >
                                                  ⋯
                                                </button>

                                                {openRestMenuBySet[setFormKey] && !isCompleted && (
                                                  <div
                                                    style={{
                                                      position: "absolute",
                                                      top: "36px",
                                                      left: "0",
                                                      zIndex: 10,
                                                      minWidth: "180px",
                                                      padding: "10px",
                                                      border: "1px solid #555",
                                                      borderRadius: "8px",
                                                      background: "#111827",
                                                      boxShadow: "0 12px 30px rgba(0, 0, 0, 0.35)",
                                                    }}
                                                  >
                                                    <label style={{ display: "block", fontSize: "13px", color: "#cbd5e1" }}>
                                                      Descanso após série
                                                    </label>
                                                    <input
                                                      type="number"
                                                      min="15"
                                                      step="15"
                                                      value={restSecondsForRow}
                                                      onChange={(e) =>
                                                        updateSetForm(setFormKey, "rest_seconds", e.target.value)
                                                      }
                                                      style={{ width: "100%", marginTop: "6px" }}
                                                    />
                                                    <div
                                                      style={{
                                                        display: "grid",
                                                        gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
                                                        gap: "6px",
                                                        marginTop: "8px",
                                                      }}
                                                    >
                                                      {[60, 90, 120, 180].map((seconds) => (
                                                        <button
                                                          key={seconds}
                                                          type="button"
                                                          onClick={() => updateSetForm(setFormKey, "rest_seconds", seconds)}
                                                          style={{ padding: "6px" }}
                                                        >
                                                          {formatTimer(seconds)}
                                                        </button>
                                                      ))}
                                                    </div>

                                                    <button
                                                      type="button"
                                                      onClick={() => removeExerciseRow(item, sourceSetNumber, displaySetNumber)}
                                                      style={{
                                                        width: "100%",
                                                        marginTop: "10px",
                                                        padding: "8px",
                                                        border: "1px solid #7f1d1d",
                                                        borderRadius: "6px",
                                                        background: "rgba(127, 29, 29, 0.18)",
                                                        color: "#fca5a5",
                                                        fontWeight: "bold",
                                                        cursor: "pointer",
                                                      }}
                                                    >
                                                      Remover série
                                                    </button>
                                                  </div>
                                                )}
                                              </div>

                                              <div style={{ position: "relative" }}>
                                                <button
                                                  type="button"
                                                  disabled={isCompleted}
                                                  onClick={() => toggleSetTypeMenu(setFormKey)}
                                                  title="Alterar tipo de série"
                                                  style={{
                                                    minWidth: "42px",
                                                    height: "32px",
                                                    borderRadius: "8px",
                                                    border: "1px solid #334155",
                                                    background: "rgba(15, 23, 42, 0.7)",
                                                    color: setTypeMeta.color,
                                                    fontWeight: "bold",
                                                    cursor: isCompleted ? "default" : "pointer",
                                                  }}
                                                >
                                                  {visibleSetLabel}
                                                </button>

                                                {openSetTypeMenuBySet[setFormKey] && !isCompleted && (
                                                  <div
                                                    style={{
                                                      position: "absolute",
                                                      top: "38px",
                                                      left: "0",
                                                      zIndex: 10,
                                                      minWidth: "150px",
                                                      padding: "8px",
                                                      border: "1px solid #555",
                                                      borderRadius: "8px",
                                                      background: "#111827",
                                                      boxShadow: "0 12px 30px rgba(0, 0, 0, 0.35)",
                                                    }}
                                                  >
                                                    {SET_TYPES.map((setType) => (
                                                      <button
                                                        key={setType.value}
                                                        type="button"
                                                        onClick={() => selectSetType(setFormKey, setType.value)}
                                                        style={{
                                                          display: "flex",
                                                          alignItems: "center",
                                                          gap: "8px",
                                                          width: "100%",
                                                          padding: "9px 10px",
                                                          border: "none",
                                                          borderRadius: "6px",
                                                          background:
                                                            rowSetType === setType.value
                                                              ? "rgba(148, 163, 184, 0.18)"
                                                              : "transparent",
                                                          color: "#e5e7eb",
                                                          fontWeight: "bold",
                                                          textAlign: "left",
                                                          cursor: "pointer",
                                                        }}
                                                      >
                                                        <span style={{ color: setType.color, minWidth: "22px" }}>
                                                          {setType.shortLabel}
                                                        </span>
                                                        {setType.label}
                                                      </button>
                                                    ))}
                                                  </div>
                                                )}
                                              </div>
                                            </div>
                                          </td>
                                          <td style={{ padding: "8px", color: "#777" }}>
                                            {formatPreviousSet(previousSet)}
                                          </td>
                                          <td style={{ padding: "8px" }}>
                                            <input
                                              type="number"
                                              step="0.1"
                                              value={weightValue}
                                              disabled={isCompleted}
                                              onChange={(e) => updateSetForm(setFormKey, "weight_used", e.target.value)}
                                              style={{ width: "90px" }}
                                            />
                                          </td>
                                          <td style={{ padding: "8px" }}>
                                            <input
                                              type="number"
                                              value={repsValue}
                                              disabled={isCompleted}
                                              onChange={(e) => updateSetForm(setFormKey, "reps_completed", e.target.value)}
                                              style={{ width: "78px" }}
                                            />
                                          </td>
                                          <td style={{ padding: "8px", textAlign: "center" }}>
                                            <div
                                              style={{
                                                position: "relative",
                                                display: "inline-flex",
                                                alignItems: "center",
                                                gap: "8px",
                                              }}
                                            >
                                              <button
                                                type="button"
                                                onClick={() => {
                                                  if (!isCompleted) {
                                                    toggleCompletionMenu(setFormKey);
                                                  }
                                                }}
                                                style={{
                                                  minWidth: "42px",
                                                  height: "34px",
                                                  borderRadius: "8px",
                                                  border: "1px solid #4b5563",
                                                  background: isCompleted ? "#16a34a" : "transparent",
                                                  color: isCompleted ? "#fff" : "#cbd5e1",
                                                  fontWeight: "bold",
                                                  cursor: isCompleted ? "default" : "pointer",
                                                }}
                                              >
                                                ✓
                                              </button>

                                              {effortMeta && (
                                                <span
                                                  style={{
                                                    color: effortMeta.color,
                                                    fontWeight: "bold",
                                                    whiteSpace: "nowrap",
                                                  }}
                                                >
                                                  {effortMeta.label}
                                                </span>
                                              )}

                                              {openCompletionMenuBySet[setFormKey] && !isCompleted && (
                                                <div
                                                  style={{
                                                    position: "absolute",
                                                    top: "40px",
                                                    right: "0",
                                                    zIndex: 10,
                                                    minWidth: "150px",
                                                    padding: "8px",
                                                    border: "1px solid #555",
                                                    borderRadius: "8px",
                                                    background: "#111827",
                                                    boxShadow: "0 12px 30px rgba(0, 0, 0, 0.35)",
                                                  }}
                                                >
                                                  {availableEffortOptions.map((option) => (
                                                    <button
                                                      key={option.value}
                                                      type="button"
                                                      onClick={() => saveSet(item, sourceSetNumber, displaySetNumber, option)}
                                                      style={{
                                                        display: "block",
                                                        width: "100%",
                                                        padding: "9px 10px",
                                                        border: "none",
                                                        borderRadius: "6px",
                                                        background: "transparent",
                                                        color: option.color,
                                                        fontWeight: "bold",
                                                        textAlign: "left",
                                                        cursor: "pointer",
                                                      }}
                                                    >
                                                      {option.label}
                                                    </button>
                                                  ))}
                                                </div>
                                              )}
                                            </div>
                                          </td>
                                        </tr>
                                      );
                                    })}
                                  </tbody>
                                </table>
                              </div>

                              <button onClick={() => addExerciseRow(item)} style={{ marginTop: "12px", width: "100%" }}>
                                + Adicionar Série
                              </button>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default App;
