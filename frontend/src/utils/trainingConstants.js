// =============================================================================
// trainingConstants.js
// -----------------------------------------------------------------------------
// Constantes partilhadas do treino no frontend.
// É usado por App.jsx e hooks para manter valores como reps alvo, descanso,
// tipos de série e opções de esforço num único local.
// Evita duplicação e reduz ruído no componente principal.
// =============================================================================
export const DEFAULT_REST_SECONDS = 120;
export const TARGET_REPS = 12;

export const SET_TYPES = [
  { value: "WARMUP", label: "Aquecimento", shortLabel: "W", color: "#eab308" },
  { value: "WORKING", label: "Normal", shortLabel: "N", color: "#f8fafc" },
  { value: "DROP", label: "Drop", shortLabel: "D", color: "#ef4444" },
];

export const EFFORT_OPTIONS = [
  { value: "FAILURE", label: "FALHA", color: "#ef4444", reachedFailure: true, rir: null },
  { value: "RIR_0_1", label: "RIR 0/1", color: "#f97316", reachedFailure: false, rir: 1 },
  { value: "RIR_2_3", label: "RIR 2/3", color: "#eab308", reachedFailure: false, rir: 2 },
  { value: "RIR_4_PLUS", label: "RIR 4+", color: "#22c55e", reachedFailure: false, rir: 4 },
];

export const WARMUP_EFFORT = {
  value: "WARMUP_DONE",
  label: "Feita",
  reachedFailure: false,
  rir: null,
};
