from collections import defaultdict

from progression.models import SetLog
from training.models import WorkoutSession


RECENT_SESSION_LIMIT = 6
WEEKLY_VOLUME_LIMIT = 8
EXERCISE_INSIGHT_LIMIT = 5


def round_metric(value, digits=1):
    return round(float(value or 0), digits)


def set_volume(set_log):
    return float(set_log.weight_used or 0) * int(set_log.reps_completed or 0)


def average(values, digits=1):
    values = [value for value in values if value is not None]

    if not values:
        return None

    return round_metric(sum(values) / len(values), digits)


def serialize_session_summary(session, set_logs):
    session_sets = list(set_logs)
    rir_values = [set_log.rir for set_log in session_sets if set_log.rir is not None]

    return {
        "id": session.id,
        "workout_name": session.workout.name,
        "completed_at": session.completed_at,
        "volume": round_metric(sum(set_volume(set_log) for set_log in session_sets)),
        "sets": len(session_sets),
        "failure_count": len([set_log for set_log in session_sets if set_log.reached_failure]),
        "average_rir": average(rir_values),
    }


def first_working_set_for_session(set_logs):
    working_sets = [
        set_log
        for set_log in set_logs
        if set_log.set_type == "WORKING"
    ]

    if not working_sets:
        return None

    return sorted(working_sets, key=lambda set_log: (set_log.set_number, set_log.created_at))[0]


def build_exercise_progressions(set_logs_by_exercise):
    progressions = []
    watchlist = []

    for exercise_id, exercise_sets in set_logs_by_exercise.items():
        session_groups = defaultdict(list)

        for set_log in exercise_sets:
            session_groups[set_log.workout_session_id].append(set_log)

        first_sets = [
            first_working_set_for_session(session_sets)
            for session_sets in session_groups.values()
        ]
        first_sets = [set_log for set_log in first_sets if set_log]
        first_sets.sort(key=lambda set_log: set_log.workout_session.completed_at or set_log.created_at)

        if not first_sets:
            continue

        latest_set = first_sets[-1]
        earliest_set = first_sets[0]
        recent_sets = first_sets[-4:]
        load_change = round_metric(latest_set.weight_used - earliest_set.weight_used)
        latest_failures = len([set_log for set_log in recent_sets if set_log.reached_failure])
        latest_low_rep_sets = len([
            set_log
            for set_log in recent_sets
            if set_log.reps_completed < (set_log.target_min_reps or 10)
        ])
        latest_rir_values = [set_log.rir for set_log in recent_sets if set_log.rir is not None]
        exercise_name = latest_set.exercise.name

        if len(first_sets) >= 2 and load_change > 0:
            progressions.append({
                "exercise_id": exercise_id,
                "exercise_name": exercise_name,
                "sessions": len(first_sets),
                "first_weight": round_metric(earliest_set.weight_used),
                "latest_weight": round_metric(latest_set.weight_used),
                "load_change": load_change,
                "latest_reps": latest_set.reps_completed,
                "average_recent_rir": average(latest_rir_values),
            })

        if latest_failures or latest_low_rep_sets or load_change < 0:
            reasons = []

            if latest_failures:
                reasons.append(f"{latest_failures} falha(s) recente(s)")

            if latest_low_rep_sets:
                reasons.append("reps abaixo do alvo")

            if load_change < 0:
                reasons.append("carga recente desceu")

            watchlist.append({
                "exercise_id": exercise_id,
                "exercise_name": exercise_name,
                "sessions": len(first_sets),
                "latest_weight": round_metric(latest_set.weight_used),
                "latest_reps": latest_set.reps_completed,
                "reason": ", ".join(reasons),
                "risk_score": latest_failures * 2 + latest_low_rep_sets + (1 if load_change < 0 else 0),
            })

    progressions.sort(key=lambda item: item["load_change"], reverse=True)
    watchlist.sort(key=lambda item: item["risk_score"], reverse=True)

    return {
        "top_progressing_exercises": progressions[:EXERCISE_INSIGHT_LIMIT],
        "watchlist_exercises": watchlist[:EXERCISE_INSIGHT_LIMIT],
    }


def build_weekly_volume(set_logs):
    weekly_volume = defaultdict(float)

    for set_log in set_logs:
        completed_at = set_log.workout_session.completed_at

        if not completed_at:
            continue

        year, week, _ = completed_at.isocalendar()
        key = f"{year}-W{week:02d}"
        weekly_volume[key] += set_volume(set_log)

    return [
        {
            "week": week,
            "volume": round_metric(volume),
        }
        for week, volume in sorted(weekly_volume.items())[-WEEKLY_VOLUME_LIMIT:]
    ]


def build_athlete_dashboard(profile):
    completed_sessions = list(
        WorkoutSession.objects.filter(
            user=profile.user,
            status="COMPLETED",
        )
        .select_related("workout")
        .order_by("-completed_at", "-started_at")
    )
    completed_session_ids = [session.id for session in completed_sessions]
    set_logs = list(
        SetLog.objects.filter(
            user=profile.user,
            workout_session_id__in=completed_session_ids,
        )
        .select_related("exercise", "workout_session__workout")
        .order_by("workout_session__completed_at", "set_number", "created_at")
    )
    sets_by_session = defaultdict(list)
    sets_by_exercise = defaultdict(list)

    for set_log in set_logs:
        sets_by_session[set_log.workout_session_id].append(set_log)
        sets_by_exercise[set_log.exercise_id].append(set_log)

    total_volume = sum(set_volume(set_log) for set_log in set_logs)
    rir_values = [set_log.rir for set_log in set_logs if set_log.rir is not None]
    working_sets = [set_log for set_log in set_logs if set_log.set_type == "WORKING"]
    exercise_insights = build_exercise_progressions(sets_by_exercise)

    return {
        "profile_id": profile.id,
        "summary": {
            "completed_workouts": len(completed_sessions),
            "total_volume": round_metric(total_volume),
            "total_sets": len(set_logs),
            "working_sets": len(working_sets),
            "failure_count": len([set_log for set_log in set_logs if set_log.reached_failure]),
            "average_rir": average(rir_values),
            "last_workout_at": completed_sessions[0].completed_at if completed_sessions else None,
        },
        "weekly_volume": build_weekly_volume(set_logs),
        "recent_sessions": [
            serialize_session_summary(session, sets_by_session[session.id])
            for session in completed_sessions[:RECENT_SESSION_LIMIT]
        ],
        **exercise_insights,
    }
