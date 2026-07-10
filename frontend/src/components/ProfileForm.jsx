// =============================================================================
// ProfileForm.jsx
// -----------------------------------------------------------------------------
// Componente visual do formulário de criação de perfil.
// É usado pelo App.jsx no onboarding para recolher username, género, idade, altura, peso, objetivo, nível e disponibilidade.
// Envia os dados através da função createProfile recebida por props.
// =============================================================================
export default function ProfileForm({
  form,
  setForm,
  handleChange,
  createProfile,
  goalLabels,
  levelGuidance,
}) {
  return (
    <div className="profile-onboarding">
      <section className="profile-intro-panel">
        <div>
          <span className="profile-kicker">Athlete setup</span>
          <h2>Create Profile</h2>
          <p>
            Define the athlete baseline so the training plan starts with the right volume,
            frequency and progression speed.
          </p>
        </div>

        <div className="profile-preview-card">
          <span>Current setup</span>
          <strong>{goalLabels[form.goal]}</strong>
          <div className="profile-preview-grid">
            <div>
              <span>Level</span>
              <strong>{levelGuidance[form.level].label}</strong>
            </div>
            <div>
              <span>Days</span>
              <strong>{form.days_per_week}/week</strong>
            </div>
            <div>
              <span>Body</span>
              <strong>{form.weight_kg}kg</strong>
            </div>
            <div>
              <span>Age</span>
              <strong>{form.age}</strong>
            </div>
          </div>
        </div>
      </section>

      <form className="profile-form-card" onSubmit={createProfile}>
        <div className="profile-form-header">
          <div>
            <span className="profile-kicker">New athlete</span>
            <h2>Build the profile</h2>
          </div>
          <button type="submit" className="profile-submit-button">Create Profile</button>
        </div>

        <div className="profile-section">
          <h3>Identity</h3>
          <div className="profile-grid two">
            <label className="profile-field">
              <span>Username</span>
              <input
                name="username"
                value={form.username}
                onChange={handleChange}
                required
                placeholder="e.g. beatriz"
              />
            </label>

            <div className="profile-field">
              <span>Gender</span>
              <div className="profile-segmented">
                {[
                  ["MALE", "Male"],
                  ["FEMALE", "Female"],
                ].map(([value, label]) => (
                  <button
                    key={value}
                    type="button"
                    className={form.gender === value ? "active" : ""}
                    onClick={() => setForm({ ...form, gender: value })}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="profile-section">
          <h3>Body metrics</h3>
          <div className="profile-grid three">
            <label className="profile-field">
              <span>Age</span>
              <input name="age" type="number" value={form.age} onChange={handleChange} />
            </label>

            <label className="profile-field">
              <span>Height</span>
              <div className="profile-input-unit">
                <input
                  name="height_cm"
                  type="number"
                  value={form.height_cm}
                  onChange={handleChange}
                />
                <small>cm</small>
              </div>
            </label>

            <label className="profile-field">
              <span>Weight</span>
              <div className="profile-input-unit">
                <input
                  name="weight_kg"
                  type="number"
                  value={form.weight_kg}
                  onChange={handleChange}
                />
                <small>kg</small>
              </div>
            </label>
          </div>
        </div>

        <div className="profile-section">
          <h3>Training direction</h3>
          <div className="profile-grid two">
            <label className="profile-field">
              <span>Goal</span>
              <select name="goal" value={form.goal} onChange={handleChange}>
                <option value="HYPERTROPHY">Gain muscle</option>
                <option value="STRENGTH">Gain strength</option>
                <option value="FAT_LOSS">Lose fat</option>
                <option value="RECOMPOSITION">Recomposition</option>
                <option value="GENERAL_FITNESS">General fitness</option>
              </select>
            </label>

            <label className="profile-field">
              <span>Level</span>
              <select name="level" value={form.level} onChange={handleChange}>
                <option value="BEGINNER">Beginner</option>
                <option value="INTERMEDIATE">Intermediate</option>
                <option value="ADVANCED">Advanced</option>
              </select>
            </label>
          </div>

          <div className="profile-level-note">
            <strong>{levelGuidance[form.level].label}</strong>
            <span>{levelGuidance[form.level].text}</span>
          </div>
        </div>

        <div className="profile-section">
          <h3>Availability</h3>
          <div className="profile-grid two">
            <label className="profile-field">
              <span>Training Experience</span>
              <select
                name="training_experience"
                value={form.training_experience}
                onChange={handleChange}
              >
                <option value="LESS_THAN_1">Less than 1 year</option>
                <option value="ONE_TO_THREE">1-3 years</option>
                <option value="THREE_TO_FIVE">3-5 years</option>
                <option value="MORE_THAN_FIVE">More than 5 years</option>
              </select>
            </label>

            <div className="profile-field">
              <span>Days per week</span>
              <div className="profile-day-picker">
                {[2, 3, 4, 5, 6, 7].map((day) => (
                  <button
                    key={day}
                    type="button"
                    className={Number(form.days_per_week) === day ? "active" : ""}
                    onClick={() => setForm({ ...form, days_per_week: day })}
                  >
                    {day}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        <button type="submit" className="profile-submit-button mobile">Create Profile</button>
      </form>
    </div>
  );
}
