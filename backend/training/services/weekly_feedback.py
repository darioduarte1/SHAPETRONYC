# =============================================================================
# weekly_feedback.py
# -----------------------------------------------------------------------------
# Serviço que calcula feedback semanal do atleta.
# É usado para avaliar tendência de volume, falhas recentes, necessidade de deload e estado geral do bloco.
# Transforma dados acumulados em recomendações semanais claras.
# =============================================================================
from training.services.athlete_dashboard import build_athlete_dashboard


DELOAD_VOLUME_MULTIPLIER = 0.7
DELOAD_TARGET_RIR = 3
RECENT_SESSION_COUNT = 4


def average(values, digits=1):
    values = [value for value in values if value is not None]

    if not values:
        return None

    return round(sum(values) / len(values), digits)


def volume_trend_from_weeks(weekly_volume):
    if len(weekly_volume) < 2:
        return {
            "direction": "insufficient_data",
            "latest_volume": weekly_volume[-1]["volume"] if weekly_volume else 0,
            "previous_average": 0,
            "change_percent": 0,
        }

    latest_volume = float(weekly_volume[-1]["volume"] or 0)
    previous_weeks = weekly_volume[:-1][-3:]
    previous_average = sum(float(week["volume"] or 0) for week in previous_weeks) / len(previous_weeks)

    if previous_average <= 0:
        change_percent = 0
    else:
        change_percent = round(((latest_volume - previous_average) / previous_average) * 100, 1)

    if change_percent >= 12:
        direction = "up"
    elif change_percent <= -12:
        direction = "down"
    else:
        direction = "stable"

    return {
        "direction": direction,
        "latest_volume": round(latest_volume, 1),
        "previous_average": round(previous_average, 1),
        "change_percent": change_percent,
    }


def build_deload_reasons(watchlist_exercises, watchlist_memories, effort_memories, recent_failure_count):
    reasons = []
    highest_risk_score = max(
        [exercise.get("risk_score", 0) for exercise in watchlist_exercises],
        default=0,
    )

    if highest_risk_score >= 4:
        reasons.append("watchlist com risco elevado")

    if len(watchlist_exercises) >= 2:
        reasons.append("vários exercícios a vigiar")

    if len(watchlist_memories) >= 2:
        reasons.append("memórias persistentes de atenção")

    if len(effort_memories) >= 2:
        reasons.append("padrão de esforço perto da falha")

    if recent_failure_count >= 2:
        reasons.append("falhas recentes acumuladas")

    return reasons


def build_weekly_feedback(profile):
    dashboard = build_athlete_dashboard(profile)
    recent_sessions = dashboard.get("recent_sessions", [])[:RECENT_SESSION_COUNT]
    training_memories = dashboard.get("training_memories", [])
    watchlist_exercises = dashboard.get("watchlist_exercises", [])
    watchlist_memories = [
        memory for memory in training_memories if memory["memory_type"] == "WATCHLIST"
    ]
    effort_memories = [
        memory for memory in training_memories if memory["memory_type"] == "EFFORT_PATTERN"
    ]
    recent_failure_count = sum(session["failure_count"] for session in recent_sessions)
    recent_average_rir = average([session["average_rir"] for session in recent_sessions])
    volume_trend = volume_trend_from_weeks(dashboard.get("weekly_volume", []))
    deload_reasons = build_deload_reasons(
        watchlist_exercises,
        watchlist_memories,
        effort_memories,
        recent_failure_count,
    )
    should_deload = bool(deload_reasons)

    if should_deload:
        status = "deload_recommended"
        title = "Deload recomendado"
        summary = "A semana deve reduzir carga total e aumentar margem para recuperar qualidade técnica."
    elif watchlist_exercises or effort_memories:
        status = "monitor"
        title = "Monitorizar recuperação"
        summary = "Há sinais a acompanhar, mas ainda não justificam uma semana de deload completa."
    else:
        status = "progressing"
        title = "Progressão saudável"
        summary = "O histórico recente permite continuar o plano com progressão controlada."

    feedback = []

    if volume_trend["direction"] == "up":
        feedback.append(f"Volume semanal subiu {volume_trend['change_percent']}% face à média recente.")
    elif volume_trend["direction"] == "down":
        feedback.append(f"Volume semanal desceu {abs(volume_trend['change_percent'])}% face à média recente.")
    elif volume_trend["direction"] == "stable":
        feedback.append("Volume semanal está estável face à média recente.")
    else:
        feedback.append("Ainda há poucas semanas concluídas para avaliar tendência de volume.")

    if recent_average_rir is not None:
        feedback.append(f"RIR médio recente: {recent_average_rir}.")

    if recent_failure_count:
        feedback.append(f"Falhas recentes nos últimos {len(recent_sessions)} treinos: {recent_failure_count}.")

    if watchlist_exercises:
        feedback.append(f"{len(watchlist_exercises)} exercício(s) em watchlist.")

    return {
        "profile_id": profile.id,
        "status": status,
        "title": title,
        "summary": summary,
        "signals": {
            "completed_workouts": dashboard["summary"]["completed_workouts"],
            "recent_session_count": len(recent_sessions),
            "recent_failure_count": recent_failure_count,
            "recent_average_rir": recent_average_rir,
            "watchlist_count": len(watchlist_exercises),
            "watchlist_memory_count": len(watchlist_memories),
            "effort_memory_count": len(effort_memories),
            "volume_trend": volume_trend,
        },
        "deload": {
            "recommended": should_deload,
            "duration": "1 semana",
            "volume_multiplier": DELOAD_VOLUME_MULTIPLIER,
            "target_rir": DELOAD_TARGET_RIR,
            "reasons": deload_reasons,
            "protocol": [
                "reduzir volume total para cerca de 70%",
                "manter RIR alvo em 3 ou mais",
                "evitar falha muscular",
                "retomar progressão só quando reps e técnica estabilizarem",
            ] if should_deload else [],
        },
        "feedback": feedback,
        "watchlist_exercises": watchlist_exercises,
    }
