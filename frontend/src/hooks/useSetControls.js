// =============================================================================
// useSetControls.js
// -----------------------------------------------------------------------------
// Hook responsável pelo estado local dos controlos da tabela de séries.
// É usado pelo App.jsx para editar campos de série, abrir/fechar menus,
// escolher tipo de série e controlar linhas removidas antes de serem guardadas.
// Mantém a interação da tabela fora do componente principal.
// =============================================================================
import { useState } from "react";
import { DEFAULT_REST_SECONDS } from "../utils/trainingConstants";

export default function useSetControls() {
  const [setForms, setSetForms] = useState({});
  const [openCompletionMenuBySet, setOpenCompletionMenuBySet] = useState({});
  const [openRestMenuBySet, setOpenRestMenuBySet] = useState({});
  const [openSetTypeMenuBySet, setOpenSetTypeMenuBySet] = useState({});
  const [removedSetByKey, setRemovedSetByKey] = useState({});

  function updateSetForm(setFormKey, field, value) {
    setSetForms({
      ...setForms,
      [setFormKey]: {
        ...setForms[setFormKey],
        [field]: value,
      },
    });
  }

  function getRestSecondsForRow(setFormKey) {
    return Number(setForms[setFormKey]?.rest_seconds || DEFAULT_REST_SECONDS);
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

  function toggleSetTypeMenu(setFormKey) {
    setOpenSetTypeMenuBySet({
      ...openSetTypeMenuBySet,
      [setFormKey]: !openSetTypeMenuBySet[setFormKey],
    });
  }

  function selectSetType(setFormKey, setType) {
    setSetForms((currentSetForms) => ({
      ...currentSetForms,
      [setFormKey]: {
        ...currentSetForms[setFormKey],
        set_type: setType,
        set_type_source: "manual",
      },
    }));
    setOpenSetTypeMenuBySet({
      ...openSetTypeMenuBySet,
      [setFormKey]: false,
    });
  }

  return {
    setForms,
    setSetForms,
    openCompletionMenuBySet,
    setOpenCompletionMenuBySet,
    openRestMenuBySet,
    setOpenRestMenuBySet,
    openSetTypeMenuBySet,
    setOpenSetTypeMenuBySet,
    removedSetByKey,
    setRemovedSetByKey,
    updateSetForm,
    getRestSecondsForRow,
    toggleCompletionMenu,
    toggleRestMenu,
    toggleSetTypeMenu,
    selectSetType,
  };
}
