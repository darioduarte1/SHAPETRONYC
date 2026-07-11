// =============================================================================
// ProgramHeader.jsx
// -----------------------------------------------------------------------------
// Componente visual do cabeçalho do programa.
// É usado no ecrã principal para mostrar o nome do programa ativo e o botão de exportar histórico.
// Mantém esse topo separado do App.jsx para reduzir ruído no ficheiro principal.
// =============================================================================
export default function ProgramHeader({ programName, exportUserTrainingData }) {
  return (
    <div className="program-header-row">
      <h2>{programName}</h2>
      <button
        type="button"
        className="export-user-button"
        onClick={exportUserTrainingData}
      >
        Exportar histórico
      </button>
    </div>
  );
}
