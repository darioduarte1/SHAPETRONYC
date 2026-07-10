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
