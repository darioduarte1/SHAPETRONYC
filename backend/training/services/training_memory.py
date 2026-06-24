from collections import defaultdict

from progression.models import SetLog
from training.models import AthleteTrainingMemory, WorkoutSession


MEMORY_LIMIT = 8


def round_metric(value, digits=1):
    return round(float(value or 0), digits)


def first_working_set_for_session(set_logs):
    working_sets = [
        set_log
        for set_log in set_logs
        if set_log.set_type == "WORKING"
    ]

    if not working_sets:
        return None

    return sorted(working_sets, key=lambda set_log: (set_log.set_number, set_log.created_at))[0]


def confidence_from_sessions(session_count):
    if session_count >= 6:
        return "alta"

    if session_count >= 3:
        return "média"

    return "baixa"


def serialize_memory(memory):
    return {
        "id": memory.id,
        "exercise_id": memory.exercise_id,
        "exercise_name": memory.exercise.name,
        "memory_type": memory.memory_type,
        "title": memory.title,
        "summary": memory.summary,
        "evidence": memory.evidence,
        "confidence": memory.confidence,
        "severity": memory.severity,
        "last_seen_at": memory.last_seen_at,
        "updated_at": memory.updated_at,
    }


def upsert_memory(user, exercise, memory_type, title, summary, evidence, confidence, severity, last_seen_at):
    memory, _ = AthleteTrainingMemory.objects.update_or_create(
        user=user,
        exercise=exercise,
        memory_type=memory_type,
        defaults={
            "title": title,
            "summary": summary,
            "evidence": evidence,
            "confidence": confidence,
            "severity": severity,
            "last_seen_at": last_seen_at,
        },
    )

    return memory


def clear_memory(user, exercise, memory_type):
    AthleteTrainingMemory.objects.filter(
        user=user,
        exercise=exercise,
        memory_type=memory_type,
    ).delete()


def refresh_training_memory(profile):
    completed_sessions = WorkoutSession.objects.filter(
        user=profile.user,
        status="COMPLETED",
    ).values_list("id", flat=True)
    set_logs = list(
        SetLog.objects.filter(
            user=profile.user,
            workout_session_id__in=completed_sessions,
        )
        .select_related("exercise", "workout_session")
        .order_by("workout_session__completed_at", "set_number", "created_at")
    )
    sets_by_exercise = defaultdict(list)

    for set_log in set_logs:
        sets_by_exercise[set_log.exercise_id].append(set_log)

    for exercise_sets in sets_by_exercise.values():
        session_sets = defaultdict(list)

        for set_log in exercise_sets:
            session_sets[set_log.workout_session_id].append(set_log)

        first_sets = [
            first_working_set_for_session(session_group)
            for session_group in session_sets.values()
        ]
        first_sets = [set_log for set_log in first_sets if set_log]
        first_sets.sort(key=lambda set_log: set_log.workout_session.completed_at or set_log.created_at)

        if len(first_sets) < 2:
            continue

        exercise = first_sets[-1].exercise
        latest_set = first_sets[-1]
        earliest_set = first_sets[0]
        recent_sets = first_sets[-4:]
        load_change = round_metric(latest_set.weight_used - earliest_set.weight_used)
        failure_count = len([set_log for set_log in recent_sets if set_log.reached_failure])
        low_rep_count = len([
            set_log
            for set_log in recent_sets
            if set_log.reps_completed < (set_log.target_min_reps or 10)
        ])
        rir_values = [set_log.rir for set_log in recent_sets if set_log.rir is not None]
        average_rir = round_metric(sum(rir_values) / len(rir_values)) if rir_values else None
        confidence = confidence_from_sessions(len(first_sets))
        last_seen_at = latest_set.workout_session.completed_at or latest_set.created_at

        if load_change > 0 and failure_count == 0:
            upsert_memory(
                profile.user,
                exercise,
                "PROGRESSION",
                f"{exercise.name} está a progredir",
                f"A primeira série subiu {load_change}kg em {len(first_sets)} treino(s) sem falhas recentes.",
                [
                    f"Primeira carga registada: {round_metric(earliest_set.weight_used)}kg",
                    f"Carga mais recente: {round_metric(latest_set.weight_used)}kg",
                    f"RIR médio recente: {average_rir if average_rir is not None else '-'}",
                ],
                confidence,
                2,
                last_seen_at,
            )
        else:
            clear_memory(profile.user, exercise, "PROGRESSION")

        if failure_count or low_rep_count or load_change < 0:
            reasons = []

            if failure_count:
                reasons.append(f"{failure_count} falha(s) recente(s)")

            if low_rep_count:
                reasons.append("reps abaixo do alvo")

            if load_change < 0:
                reasons.append("carga recente desceu")

            upsert_memory(
                profile.user,
                exercise,
                "WATCHLIST",
                f"{exercise.name} precisa de atenção",
                ", ".join(reasons),
                [
                    f"Carga mais recente: {round_metric(latest_set.weight_used)}kg",
                    f"Reps mais recentes: {latest_set.reps_completed}",
                    f"Sessões analisadas: {len(first_sets)}",
                ],
                confidence,
                3,
                last_seen_at,
            )
        else:
            clear_memory(profile.user, exercise, "WATCHLIST")

        if average_rir is not None and average_rir <= 1.5 and failure_count == 0:
            upsert_memory(
                profile.user,
                exercise,
                "EFFORT_PATTERN",
                f"{exercise.name} tende a ficar perto da falha",
                "As séries recentes chegam perto do limite mesmo sem falhas registadas.",
                [
                    f"RIR médio recente: {average_rir}",
                    f"Sessões analisadas: {len(first_sets)}",
                ],
                confidence,
                2,
                last_seen_at,
            )
        else:
            clear_memory(profile.user, exercise, "EFFORT_PATTERN")

    return list_training_memories(profile)


def list_training_memories(profile, limit=MEMORY_LIMIT):
    memories = AthleteTrainingMemory.objects.filter(
        user=profile.user,
    ).select_related(
        "exercise",
    ).order_by(
        "-severity",
        "-updated_at",
    )[:limit]

    return [serialize_memory(memory) for memory in memories]
