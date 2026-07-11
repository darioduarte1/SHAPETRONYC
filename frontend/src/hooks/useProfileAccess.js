// =============================================================================
// useProfileAccess.js
// -----------------------------------------------------------------------------
// Hook responsável pelo acesso do atleta e gestão inicial do perfil.
// É usado pelo App.jsx para login, criação de perfil, exportação do histórico e
// limpeza de atletas experimentais durante testes.
// Mantém o onboarding separado da lógica de treino e renderização.
// =============================================================================
import { useState } from "react";
import * as accountsApi from "../api/accountsApi";
import * as trainingApi from "../api/trainingApi";

export const levelGuidance = {
  BEGINNER: {
    label: "Beginner",
    text: "Menos volume, foco em técnica e consistência.",
  },
  INTERMEDIATE: {
    label: "Intermediate",
    text: "Mais volume, maior frequência e progressão mais desafiante.",
  },
  ADVANCED: {
    label: "Advanced",
    text: "Mais especialização, maior fadiga e mais atenção à recuperação.",
  },
};

export const goalLabels = {
  HYPERTROPHY: "Gain muscle",
  STRENGTH: "Gain strength",
  FAT_LOSS: "Lose fat",
  RECOMPOSITION: "Recomposition",
  GENERAL_FITNESS: "General fitness",
};

export default function useProfileAccess({
  profileId,
  setProfileId,
  userId,
  setUserId,
  setStep,
  setProgram,
  setProgramError,
  setLatestWorkoutProgression,
  setLatestAiCoach,
  loadProgramPanels,
  resetAllTrainingState,
  resetAllAppState,
}) {
  const [loginUsername, setLoginUsername] = useState("");
  const [loginError, setLoginError] = useState("");
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const [isDeletingExperimentalUsers, setIsDeletingExperimentalUsers] = useState(false);
  const [deleteUsersMessage, setDeleteUsersMessage] = useState("");
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

  async function exportUserTrainingData() {
    if (!profileId) {
      alert("Não encontrei o perfil ativo para exportar.");
      return;
    }

    try {
      const blob = await accountsApi.exportProfileHistory(profileId);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      const timestamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");

      link.href = url;
      link.download = `shapetronyc-${form.username || "athlete"}-${timestamp}.json`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error(error);
      alert("Não consegui contactar o servidor para exportar o histórico.");
    }
  }

  async function loginExistingProfile(e) {
    e.preventDefault();

    const normalizedUsername = loginUsername.trim().toLowerCase();

    if (!normalizedUsername) {
      setLoginError("Escreve o username do atleta.");
      return;
    }

    setLoginError("");
    setProgramError("");
    setIsLoggingIn(true);

    try {
      const profilesData = await accountsApi.listProfiles();
      const profile = profilesData.find(
        (item) => item.username?.toLowerCase() === normalizedUsername
      );

      if (!profile) {
        setLoginError("Não encontrei nenhum atleta com esse username.");
        return;
      }

      setUserId(profile.user);
      setProfileId(profile.id);
      setForm({
        username: profile.username,
        gender: profile.gender,
        age: profile.age,
        height_cm: profile.height_cm,
        weight_kg: profile.weight_kg,
        goal: profile.goal,
        level: profile.level,
        training_experience: profile.training_experience,
        days_per_week: profile.days_per_week,
      });
      setLatestWorkoutProgression(null);
      setLatestAiCoach(null);
      resetAllTrainingState();

      try {
        const programData = await trainingApi.getProgram(profile.id);
        setProgram(programData);
      } catch (error) {
        setProgram(null);
        setProgramError("Perfil encontrado. Ainda não existe programa ativo para este atleta.");
        setStep(3);
        return;
      }

      loadProgramPanels(profile.id);
      setStep(4);
    } catch (error) {
      console.error(error);
      setLoginError("Não consegui contactar o servidor para entrar no perfil.");
    } finally {
      setIsLoggingIn(false);
    }
  }

  async function createProfile(e) {
    e.preventDefault();
    setProgramError("");

    let userData;

    try {
      userData = await accountsApi.createUser({ username: form.username });
    } catch (error) {
      console.error(error.data || error);
      alert("Erro ao criar utilizador. Confirma os dados e tenta novamente.");
      return;
    }

    setUserId(userData.id);

    try {
      const profileData = await accountsApi.createProfile({
        user: userData.id,
        gender: form.gender,
        age: Number(form.age),
        height_cm: Number(form.height_cm),
        weight_kg: Number(form.weight_kg),
        goal: form.goal,
        level: form.level,
        training_experience: form.training_experience,
        days_per_week: Number(form.days_per_week),
      });

      setProfileId(profileData.id);
      setStep(3);
    } catch (error) {
      console.error(error.data || error);
      alert("Erro ao criar perfil. Confirma os dados e tenta novamente.");
    }
  }

  async function deleteExperimentalUsers() {
    const confirmed = window.confirm(
      "Isto vai apagar todos os atletas experimentais e os dados associados. A biblioteca de exercícios fica preservada. Queres continuar?"
    );

    if (!confirmed) {
      return;
    }

    setDeleteUsersMessage("");
    setLoginError("");
    setProgramError("");
    setIsDeletingExperimentalUsers(true);

    try {
      const data = await accountsApi.deleteExperimentalUsers();

      setProfileId(null);
      setUserId(null);
      setLoginUsername("");
      resetAllAppState();
      setStep(1);
      setDeleteUsersMessage(`${data.deleted_users} atleta(s) experimental(is) apagado(s).`);
    } catch (error) {
      console.error(error);
      setDeleteUsersMessage("Erro de ligação ao apagar atletas experimentais.");
    } finally {
      setIsDeletingExperimentalUsers(false);
    }
  }

  return {
    profileId,
    setProfileId,
    userId,
    setUserId,
    form,
    setForm,
    levelGuidance,
    goalLabels,
    loginUsername,
    setLoginUsername,
    loginError,
    setLoginError,
    isLoggingIn,
    isDeletingExperimentalUsers,
    deleteUsersMessage,
    handleChange,
    exportUserTrainingData,
    loginExistingProfile,
    createProfile,
    deleteExperimentalUsers,
  };
}
