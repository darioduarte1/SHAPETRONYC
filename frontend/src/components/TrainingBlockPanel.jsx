export default function TrainingBlockPanel({
  trainingBlock,
  formatNumber,
  getPhaseLabel,
  getPhaseColor,
}) {
  if (!trainingBlock) {
    return null;
  }

  const phaseColor = getPhaseColor(trainingBlock.block?.phase);
  const weeklyVolume = trainingBlock.summary?.weekly_volume || [];
  const maxVolume = Math.max(...weeklyVolume.map((item) => Number(item.volume) || 0), 1);

  return (
    <section className="training-block-panel">
      <div className="panel-heading-row">
        <div>
          <div className="panel-kicker" style={{ color: phaseColor }}>
            Bloco de treino
          </div>
          <h3>{trainingBlock.block?.name || "Sem bloco ativo"}</h3>
          <p className="panel-copy">
            {trainingBlock.summary?.phase_recommendation?.message ||
              "Termina mais treinos para formar um bloco."}
          </p>
        </div>
        <span className="panel-source" style={{ color: phaseColor }}>
          {getPhaseLabel(trainingBlock.block?.phase)}
        </span>
      </div>

      <div className="training-block-metrics">
        <div>
          <strong>{trainingBlock.summary?.completed_sessions || 0}</strong>
          <p>treinos no bloco</p>
        </div>
        <div>
          <strong>{formatNumber(trainingBlock.summary?.total_volume || 0)} kg</strong>
          <p>volume do bloco</p>
        </div>
        <div>
          <strong>{trainingBlock.summary?.total_failures || 0}</strong>
          <p>falhas no bloco</p>
        </div>
        <div>
          <strong>{trainingBlock.summary?.average_rir ?? "-"}</strong>
          <p>RIR médio</p>
        </div>
      </div>

      {weeklyVolume.length > 0 && (
        <div
          className="training-block-volume-chart"
          style={{ gridTemplateColumns: `repeat(${weeklyVolume.length}, minmax(44px, 1fr))` }}
        >
          {weeklyVolume.map((week) => {
            const height = Math.max(8, (Number(week.volume) / maxVolume) * 82);

            return (
              <div key={week.week} className="weekly-volume-bar-wrap">
                <div
                  className="weekly-volume-bar"
                  title={`${week.week}: ${formatNumber(week.volume)} kg`}
                  style={{ height: `${height}px`, background: phaseColor }}
                />
                <span>{week.week.split("-")[1]}</span>
              </div>
            );
          })}
        </div>
      )}

      <div className="training-block-recommendation">
        <strong>{trainingBlock.summary?.phase_recommendation?.title}</strong>
        <p>{trainingBlock.summary?.phase_recommendation?.next_step}</p>
      </div>
    </section>
  );
}
