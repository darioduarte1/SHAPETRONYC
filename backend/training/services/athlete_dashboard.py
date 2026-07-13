# =============================================================================
# athlete_dashboard.py
# -----------------------------------------------------------------------------
# Serviço que calcula os dados do dashboard do atleta.
# É usado para mostrar volume, séries, calibrações, últimas sessões, alertas e evolução geral.
# Resume dados de treino num formato motivador e fácil de ler no frontend.
# =============================================================================
from collections import defaultdict

from progression.models import SetLog
from training.models import ExerciseCalibration, WorkoutSession
from training.services.training_memory import refresh_training_memory


RECENT_SESSION_LIMIT = 6
WEEKLY_VOLUME_LIMIT = 8
EXERCISE_INSIGHT_LIMIT = 5
EXERCISE_DETAIL_LIMIT = 12
EXERCISE_DETAIL_SET_LIMIT = 8


def round_metric(value, digits=1):
    return round(float(value or 0), digits)


def set_volume(set_log):
    return float(set_log.weight_used or 0) * int(set_log.reps_completed or 0)


def calibration_set_volume(calibration_set):
    return float(calibration_set.get("weight_used") or 0) * int(calibration_set.get("reps_completed") or 0)


def calibration_volume(calibration):
    return sum(calibration_set_volume(calibration_set) for calibration_set in calibration.calibration_sets)


def average(values, digits=1):
    values = [value for value in values if value is not None]

    if not values:
        return None

    return round_metric(sum(values) / len(values), digits)


def serialize_set_log(set_log):
    return {
        "id": set_log.id,
        "set_number": set_log.set_number,
        "set_type": set_log.set_type,
        "planned_weight": round_metric(set_log.planned_weight) if set_log.planned_weight is not None else None,
        "weight_used": round_metric(set_log.weight_used),
        "target_min_reps": set_log.target_min_reps,
        "target_max_reps": set_log.target_max_reps,
        "reps_completed": set_log.reps_completed,
        "rir": set_log.rir,
        "reached_failure": set_log.reached_failure,
        "notes": set_log.notes,
        "created_at": set_log.created_at,
    }


def serialize_calibration_set(calibration_set, index):
    return {
        "id": f"calibration-{index}",
        "set_number": index,
        "set_type": "CALIBRATION",
        "weight_used": round_metric(calibration_set.get("weight_used")),
        "reps_completed": calibration_set.get("reps_completed"),
        "result_color": calibration_set.get("result_color", ""),
        "reached_failure": calibration_set.get("reached_failure", True),
    }


def serialize_session_exercises(set_logs, calibrations=None):
    exercises = {}

    for set_log in set_logs:
        exercise_id = set_log.exercise_id
        training_exercise = set_log.training_exercise
        item = exercises.setdefault(
            exercise_id,
            {
                "exercise_id": exercise_id,
                "training_exercise_id": set_log.training_exercise_id,
                "exercise_name": set_log.exercise.name,
                "order": training_exercise.order if training_exercise else 999,
                "target_min_reps": training_exercise.target_min_reps if training_exercise else set_log.target_min_reps,
                "target_max_reps": training_exercise.target_max_reps if training_exercise else set_log.target_max_reps,
                "target_rir": training_exercise.target_rir if training_exercise else None,
                "sets": [],
                "calibration": None,
            },
        )
        item["sets"].append(serialize_set_log(set_log))

    for calibration in calibrations or []:
        item = exercises.setdefault(
            calibration.exercise_id,
            {
                "exercise_id": calibration.exercise_id,
                "training_exercise_id": None,
                "exercise_name": calibration.exercise.name,
                "order": 999,
                "target_min_reps": calibration.target_reps,
                "target_max_reps": calibration.target_reps,
                "target_rir": calibration.target_rir,
                "sets": [],
                "calibration": None,
            },
        )
        item["calibration"] = {
            "status": calibration.status,
            "estimated_working_weight": round_metric(calibration.estimated_working_weight),
            "target_reps": calibration.target_reps,
            "target_rir": calibration.target_rir,
            "confidence": calibration.confidence,
            "sets": [
                serialize_calibration_set(calibration_set, index)
                for index, calibration_set in enumerate(calibration.calibration_sets or [], start=1)
            ],
        }

    return sorted(exercises.values(), key=lambda item: (item["order"], item["exercise_name"]))


def serialize_session_summary(session, set_logs, calibrations=None):
    session_sets = list(set_logs)
    session_calibrations = list(calibrations or [])
    rir_values = [set_log.rir for set_log in session_sets if set_log.rir is not None]
    calibration_sets = [
        calibration_set
        for calibration in session_calibrations
        for calibration_set in calibration.calibration_sets
    ]

    return {
        "id": session.id,
        "workout_name": session.workout.name,
        "completed_at": session.completed_at,
        "volume": round_metric(
            sum(set_volume(set_log) for set_log in session_sets)
            + sum(calibration_set_volume(calibration_set) for calibration_set in calibration_sets)
        ),
        "sets": len(session_sets) + len(calibration_sets),
        "working_sets": len(session_sets),
        "calibration_sets": len(calibration_sets),
        "calibrated_exercises": len(session_calibrations),
        "failure_count": len([set_log for set_log in session_sets if set_log.reached_failure]),
        "average_rir": average(rir_values),
        "exercises": serialize_session_exercises(session_sets, session_calibrations),
        "coach_feedback": {
            "headline": session.coach_feedback.get("headline", ""),
            "summary": session.coach_feedback.get("summary", ""),
            "focus_points": session.coach_feedback.get("focus_points", []),
            "exercise_feedback": session.coach_feedback.get("exercise_feedback", []),
            "next_session_strategy": session.coach_feedback.get("next_session_strategy", ""),
            "recovery_note": session.coach_feedback.get("recovery_note", ""),
            "metrics": session.coach_feedback.get("metrics", {}),
            "exercise_feedback_count": len(session.coach_feedback.get("exercise_feedback", [])),
            "source": session.coach_feedback_source,
            "status": session.coach_feedback_status,
            "model": session.coach_feedback_model,
        } if session.coach_feedback else None,
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


def build_weekly_calibration_volume(calibrations):
    weekly_volume = defaultdict(float)

    for calibration in calibrations:
        if not calibration.updated_at:
            continue

        year, week, _ = calibration.updated_at.isocalendar()
        key = f"{year}-W{week:02d}"
        weekly_volume[key] += calibration_volume(calibration)

    return weekly_volume


def merge_weekly_volume(set_logs, calibrations):
    weekly_volume = {
        item["week"]: float(item["volume"])
        for item in build_weekly_volume(set_logs)
    }

    for week, volume in build_weekly_calibration_volume(calibrations).items():
        weekly_volume[week] = weekly_volume.get(week, 0) + volume

    return [
        {
            "week": week,
            "volume": round_metric(volume),
        }
        for week, volume in sorted(weekly_volume.items())[-WEEKLY_VOLUME_LIMIT:]
    ]


def serialize_calibrated_exercise(calibration):
    calibration_sets = calibration.calibration_sets or []

    return {
        "exercise_id": calibration.exercise_id,
        "exercise_name": calibration.exercise.name,
        "estimated_working_weight": round_metric(calibration.estimated_working_weight),
        "target_reps": calibration.target_reps,
        "target_rir": calibration.target_rir,
        "confidence": calibration.confidence,
        "status": calibration.status,
        "set_count": len(calibration_sets),
        "volume": round_metric(calibration_volume(calibration)),
        "updated_at": calibration.updated_at,
    }


def serialize_calibration_summary(calibration):
    if not calibration:
        return None

    calibration_sets = calibration.calibration_sets or []

    return {
        "status": calibration.status,
        "estimated_working_weight": round_metric(calibration.estimated_working_weight),
        "target_reps": calibration.target_reps,
        "target_rir": calibration.target_rir,
        "confidence": calibration.confidence,
        "set_count": len(calibration_sets),
        "volume": round_metric(calibration_volume(calibration)),
        "updated_at": calibration.updated_at,
        "sets": [
            serialize_calibration_set(calibration_set, index)
            for index, calibration_set in enumerate(calibration_sets, start=1)
        ],
    }


def build_exercise_status(recent_working_sets, load_change):
    failures = len([set_log for set_log in recent_working_sets if set_log.reached_failure])
    low_rep_sets = len([
        set_log
        for set_log in recent_working_sets
        if set_log.reps_completed < (set_log.target_min_reps or 10)
    ])

    if failures or low_rep_sets:
        return {
            "status": "watch",
            "label": "A vigiar",
            "summary": "Há sinais recentes de fadiga, falha ou reps abaixo do alvo.",
        }

    if load_change and load_change > 0:
        return {
            "status": "progressing",
            "label": "A evoluir",
            "summary": "A carga de trabalho está a subir de forma positiva.",
        }

    return {
        "status": "stable",
        "label": "Estável",
        "summary": "Ainda precisamos de mais sessões para confirmar uma tendência forte.",
    }


def exercise_detail_sort_timestamp(item):
    calibration_updated_at = (item.get("calibration") or {}).get("updated_at")

    if calibration_updated_at:
        return calibration_updated_at.timestamp()

    if item.get("latest_sets"):
        created_at = item["latest_sets"][-1].get("created_at")

        if created_at:
            return created_at.timestamp()

    return 0


def build_exercise_details(set_logs_by_exercise, calibrations):
    details = {}

    for exercise_sets in set_logs_by_exercise.values():
        if not exercise_sets:
            continue

        exercise = exercise_sets[0].exercise
        details.setdefault(
            exercise.id,
            {
                "exercise_id": exercise.id,
                "exercise_name": exercise.name,
                "muscle_group": exercise.muscle_group,
                "equipment": exercise.equipment,
                "sessions": 0,
                "working_sets": 0,
                "total_volume": 0,
                "first_working_weight": None,
                "latest_working_weight": None,
                "load_change": 0,
                "latest_reps": None,
                "average_recent_rir": None,
                "failure_count": 0,
                "calibration": None,
                "latest_sets": [],
                "status": None,
            },
        )

    for calibration in calibrations:
        exercise = calibration.exercise
        details.setdefault(
            exercise.id,
            {
                "exercise_id": exercise.id,
                "exercise_name": exercise.name,
                "muscle_group": exercise.muscle_group,
                "equipment": exercise.equipment,
                "sessions": 0,
                "working_sets": 0,
                "total_volume": 0,
                "first_working_weight": None,
                "latest_working_weight": None,
                "load_change": 0,
                "latest_reps": None,
                "average_recent_rir": None,
                "failure_count": 0,
                "calibration": None,
                "latest_sets": [],
                "status": None,
            },
        )
        details[exercise.id]["calibration"] = serialize_calibration_summary(calibration)

    for exercise_id, item in details.items():
        exercise_sets = sorted(
            set_logs_by_exercise.get(exercise_id, []),
            key=lambda set_log: (
                set_log.workout_session.completed_at or set_log.created_at,
                set_log.set_number,
                set_log.created_at,
            ),
        )
        working_sets = [set_log for set_log in exercise_sets if set_log.set_type == "WORKING"]
        session_groups = defaultdict(list)

        for set_log in exercise_sets:
            session_groups[set_log.workout_session_id].append(set_log)

        first_sets = [
            first_working_set_for_session(session_sets)
            for session_sets in session_groups.values()
        ]
        first_sets = [set_log for set_log in first_sets if set_log]
        first_sets.sort(key=lambda set_log: set_log.workout_session.completed_at or set_log.created_at)
        recent_working_sets = working_sets[-4:]
        rir_values = [set_log.rir for set_log in recent_working_sets if set_log.rir is not None]
        load_change = (
            round_metric(first_sets[-1].weight_used - first_sets[0].weight_used)
            if len(first_sets) >= 2
            else 0
        )

        item["sessions"] = len(session_groups)
        item["working_sets"] = len(working_sets)
        item["total_volume"] = round_metric(sum(set_volume(set_log) for set_log in exercise_sets))
        item["first_working_weight"] = round_metric(first_sets[0].weight_used) if first_sets else None
        item["latest_working_weight"] = round_metric(first_sets[-1].weight_used) if first_sets else None
        item["load_change"] = load_change
        item["latest_reps"] = first_sets[-1].reps_completed if first_sets else None
        item["average_recent_rir"] = average(rir_values)
        item["failure_count"] = len([set_log for set_log in working_sets if set_log.reached_failure])
        item["latest_sets"] = [
            serialize_set_log(set_log)
            for set_log in exercise_sets[-EXERCISE_DETAIL_SET_LIMIT:]
        ]
        item["status"] = build_exercise_status(recent_working_sets, load_change)

    return sorted(
        details.values(),
        key=lambda item: (
            item["calibration"] is None,
            -exercise_detail_sort_timestamp(item),
            item["exercise_name"],
        ),
    )[:EXERCISE_DETAIL_LIMIT]


def build_athlete_dashboard(profile):
    training_memories = refresh_training_memory(profile)
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
        .select_related("exercise", "training_exercise", "workout_session__workout")
        .order_by("workout_session__completed_at", "set_number", "created_at")
    )
    calibrations = list(
        ExerciseCalibration.objects.filter(
            user=profile.user,
            status="CALIBRATED",
        )
        .select_related("exercise")
        .order_by("-updated_at")
    )
    sets_by_session = defaultdict(list)
    sets_by_exercise = defaultdict(list)
    calibrations_by_session = defaultdict(list)

    for set_log in set_logs:
        sets_by_session[set_log.workout_session_id].append(set_log)
        sets_by_exercise[set_log.exercise_id].append(set_log)

    for session in completed_sessions:
        for calibration in calibrations:
            if not session.started_at or not session.completed_at or not calibration.updated_at:
                continue

            if session.started_at <= calibration.updated_at <= session.completed_at:
                calibrations_by_session[session.id].append(calibration)

    total_volume = sum(set_volume(set_log) for set_log in set_logs)
    total_calibration_volume = sum(calibration_volume(calibration) for calibration in calibrations)
    total_calibration_sets = sum(len(calibration.calibration_sets or []) for calibration in calibrations)
    rir_values = [set_log.rir for set_log in set_logs if set_log.rir is not None]
    working_sets = [set_log for set_log in set_logs if set_log.set_type == "WORKING"]
    exercise_insights = build_exercise_progressions(sets_by_exercise)

    return {
        "profile_id": profile.id,
        "summary": {
            "completed_workouts": len(completed_sessions),
            "total_volume": round_metric(total_volume + total_calibration_volume),
            "training_volume": round_metric(total_volume),
            "calibration_volume": round_metric(total_calibration_volume),
            "total_sets": len(set_logs) + total_calibration_sets,
            "working_sets": len(working_sets),
            "calibration_sets": total_calibration_sets,
            "calibrated_exercises": len(calibrations),
            "failure_count": len([set_log for set_log in set_logs if set_log.reached_failure]),
            "average_rir": average(rir_values),
            "last_workout_at": completed_sessions[0].completed_at if completed_sessions else None,
        },
        "weekly_volume": merge_weekly_volume(set_logs, calibrations),
        "recent_sessions": [
            serialize_session_summary(
                session,
                sets_by_session[session.id],
                calibrations_by_session[session.id],
            )
            for session in completed_sessions[:RECENT_SESSION_LIMIT]
        ],
        "calibrated_exercises": [
            serialize_calibrated_exercise(calibration)
            for calibration in calibrations[:EXERCISE_INSIGHT_LIMIT]
        ],
        "exercise_details": build_exercise_details(sets_by_exercise, calibrations),
        "training_memories": training_memories,
        **exercise_insights,
    }
