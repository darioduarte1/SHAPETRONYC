export default function HomeScreen({
  loginUsername,
  setLoginUsername,
  loginError,
  isLoggingIn,
  loginExistingProfile,
  goToProfileSetup,
  deleteExperimentalUsers,
  isDeletingExperimentalUsers,
  deleteUsersMessage,
}) {
  return (
    <div className="home-landing">
      <section className="home-hero-panel">
        <span className="profile-kicker">Adaptive training system</span>
        <h2>Adaptive training built around you</h2>
        <p>
          Create a new athlete profile or enter an existing one to continue training with history,
          memory, weekly feedback and adaptive planning.
        </p>
        <div className="home-signal-grid">
          <div>
            <strong>AI Coach</strong>
            <span>set-by-set guidance</span>
          </div>
          <div>
            <strong>Memory</strong>
            <span>patterns by exercise</span>
          </div>
          <div>
            <strong>Blocks</strong>
            <span>periodization review</span>
          </div>
        </div>
      </section>

      <section className="home-action-grid">
        <article className="home-action-card primary">
          <div>
            <span className="profile-kicker">New athlete</span>
            <h2>Create a new profile</h2>
            <p>Start from baseline data and let SHAPETRONYC generate the first adaptive program.</p>
          </div>
          <button type="button" className="home-primary-button" onClick={goToProfileSetup}>
            Create new profile
          </button>
        </article>

        <form className="home-action-card" onSubmit={loginExistingProfile}>
          <div>
            <span className="profile-kicker">Existing athlete</span>
            <h2>Login</h2>
            <p>
              Enter the athlete username to continue from the saved program, dashboard and training
              history.
            </p>
          </div>
          <label className="profile-field">
            <span>Username</span>
            <input
              value={loginUsername}
              onChange={(event) => setLoginUsername(event.target.value)}
              placeholder="e.g. beatriz"
            />
          </label>
          {loginError && <p className="home-error">{loginError}</p>}
          <button type="submit" className="home-secondary-button" disabled={isLoggingIn}>
            {isLoggingIn ? "Entering..." : "Enter profile"}
          </button>
        </form>
      </section>

      <section className="home-experimental-panel">
        <div>
          <span className="profile-kicker">Experimental</span>
          <h2>Limpar atletas de teste</h2>
          <p>
            Apaga os atletas criados durante testes e todos os dados associados: perfis, programas,
            sessões, séries, calibrações, memórias e escalas.
          </p>
        </div>
        <button
          type="button"
          className="home-danger-button"
          onClick={deleteExperimentalUsers}
          disabled={isDeletingExperimentalUsers}
        >
          {isDeletingExperimentalUsers ? "A apagar..." : "Apagar atletas experimentais"}
        </button>
        {deleteUsersMessage && <p className="home-delete-message">{deleteUsersMessage}</p>}
      </section>
    </div>
  );
}
