# =============================================================================
# training_blocks.py
# -----------------------------------------------------------------------------
# Serviço de blocos de treino e periodização.
# É usado para acompanhar fases como build, deload e retorno ao progresso.
# Ajuda a app a tomar decisões semanais com base em volume, falhas e fadiga acumulada.
# =============================================================================
from collections import defaultdict
from datetime import timedelta

from progression.models import SetLog
from training.models import TrainingBlock, TrainingProgram, WorkoutSession
from training.services.weekly_feedback import build_weekly_feedback


BLOCK_WEEKS = 4


def round_metric(value, digits=1):
    return round(float(value or 0), digits)


def set_volume(set_log):
    return float(set_log.weight_used or 0) * int(set_log.reps_completed or 0)


def average(values, digits=1):
    values = [value for value in values if value is not None]

    if not values:
        return None

    return round_metric(sum(values) / len(values), digits)


def serialize_weekly_block_volume(set_logs):
    weekly = defaultdict(lambda: {"volume": 0.0, "sets": 0, "failures": 0, "rir_values": []})

    for set_log in set_logs:
        completed_at = set_log.workout_session.completed_at

        if not completed_at:
            continue

        year, week, _ = completed_at.isocalendar()
        key = f"{year}-W{week:02d}"
        weekly[key]["volume"] += set_volume(set_log)
        weekly[key]["sets"] += 1
        weekly[key]["failures"] += 1 if set_log.reached_failure else 0

        if set_log.rir is not None:
            weekly[key]["rir_values"].append(set_log.rir)

    return [
        {
            "week": week,
            "volume": round_metric(values["volume"]),
            "sets": values["sets"],
            "failures": values["failures"],
            "average_rir": average(values["rir_values"]),
        }
        for week, values in sorted(weekly.items())
    ]


def choose_block_phase(weekly_feedback, week_count):
    if weekly_feedback["deload"]["recommended"]:
        return "DELOAD"

    if week_count <= 1:
        return "BUILD"

    if weekly_feedback["status"] == "progressing":
        return "BUILD"

    return "RETURN"


def phase_recommendation(phase):
    if phase == "DELOAD":
        return {
            "title": "Executar deload",
            "message": "Reduz volume e mantém margem alta antes de voltar a perseguir progressão.",
            "next_step": "Aplicar uma semana leve e reavaliar após o próximo treino completo.",
        }

    if phase == "RETURN":
        return {
            "title": "Consolidar retorno",
            "message": "Mantém cargas estáveis e usa a próxima semana para confirmar técnica, reps e RIR.",
            "next_step": "Só voltar a subir carga quando watchlist e falhas estabilizarem.",
        }

    return {
        "title": "Continuar build",
        "message": "O bloco está em boa condição para continuar a acumular volume e progressão controlada.",
        "next_step": "Manter progressão gradual e rever novamente no fim da semana.",
    }


def active_program_for_profile(profile):
    return TrainingProgram.objects.filter(
        user=profile.user,
        is_active=True,
    ).first()


def block_window_from_sessions(sessions):
    if not sessions:
        return None, None

    latest_date = sessions[0].completed_at.date()
    start_date = latest_date - timedelta(weeks=BLOCK_WEEKS - 1, days=6)

    return start_date, latest_date


def get_block_sessions(profile, start_date, end_date):
    if not start_date or not end_date:
        return WorkoutSession.objects.none()

    return WorkoutSession.objects.filter(
        user=profile.user,
        status="COMPLETED",
        completed_at__date__gte=start_date,
        completed_at__date__lte=end_date,
    ).select_related("workout").order_by("-completed_at", "-started_at")


def build_training_block(profile):
    completed_sessions = list(
        WorkoutSession.objects.filter(
            user=profile.user,
            status="COMPLETED",
            completed_at__isnull=False,
        ).select_related("workout").order_by("-completed_at", "-started_at")
    )
    start_date, end_date = block_window_from_sessions(completed_sessions)
    block_sessions = list(get_block_sessions(profile, start_date, end_date))
    session_ids = [session.id for session in block_sessions]
    set_logs = list(
        SetLog.objects.filter(
            user=profile.user,
            workout_session_id__in=session_ids,
        ).select_related("workout_session", "exercise")
    )
    weekly_volume = serialize_weekly_block_volume(set_logs)
    total_volume = round_metric(sum(set_volume(set_log) for set_log in set_logs))
    total_failures = len([set_log for set_log in set_logs if set_log.reached_failure])
    average_rir = average([set_log.rir for set_log in set_logs if set_log.rir is not None])
    weekly_feedback = build_weekly_feedback(profile)
    phase = choose_block_phase(weekly_feedback, len(weekly_volume))
    recommendation = phase_recommendation(phase)
    program = active_program_for_profile(profile)
    name = f"Bloco {start_date.isoformat() if start_date else 'sem histórico'}"
    summary = {
        "total_volume": total_volume,
        "completed_sessions": len(block_sessions),
        "total_sets": len(set_logs),
        "total_failures": total_failures,
        "average_rir": average_rir,
        "weekly_volume": weekly_volume,
        "phase_recommendation": recommendation,
        "weekly_feedback_status": weekly_feedback["status"],
    }

    if start_date:
        block, _ = TrainingBlock.objects.update_or_create(
            user=profile.user,
            status="ACTIVE",
            defaults={
                "program": program,
                "name": name,
                "phase": phase,
                "start_date": start_date,
                "end_date": end_date,
                "planned_weeks": BLOCK_WEEKS,
                "summary": summary,
            },
        )
    else:
        block = None

    return {
        "profile_id": profile.id,
        "block": {
            "id": block.id if block else None,
            "name": name,
            "status": "ACTIVE" if block else "EMPTY",
            "phase": phase,
            "start_date": start_date,
            "end_date": end_date,
            "planned_weeks": BLOCK_WEEKS,
        },
        "summary": summary,
        "weekly_feedback": weekly_feedback,
    }


def list_training_blocks(profile, limit=6):
    blocks = TrainingBlock.objects.filter(
        user=profile.user,
    ).order_by("-start_date", "-created_at")[:limit]

    return [
        {
            "id": block.id,
            "name": block.name,
            "status": block.status,
            "phase": block.phase,
            "start_date": block.start_date,
            "end_date": block.end_date,
            "planned_weeks": block.planned_weeks,
            "summary": block.summary,
        }
        for block in blocks
    ]
