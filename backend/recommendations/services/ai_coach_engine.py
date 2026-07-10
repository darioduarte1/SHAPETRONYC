import json
import urllib.error
import urllib.request

from django.conf import settings


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_TIMEOUT_SECONDS = 20


def _number_or_zero(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0


def _round_metric(value):
    return round(float(value), 1)


def _serialize_set_log(set_log):
    return {
        "exercise_name": set_log.training_exercise.exercise.name
        if set_log.training_exercise_id
        else set_log.exercise.name,
        "training_exercise": set_log.training_exercise_id,
        "set_number": set_log.set_number,
        "set_type": set_log.set_type,
        "weight_used": float(set_log.weight_used),
        "reps_completed": set_log.reps_completed,
        "rir": set_log.rir,
        "reached_failure": set_log.reached_failure,
        "notes": set_log.notes,
    }


def _serialize_calibration(calibration):
    calibration_sets = calibration.calibration_sets or []
    volume = sum(
        _number_or_zero(calibration_set.get("weight_used"))
        * _number_or_zero(calibration_set.get("reps_completed"))
        for calibration_set in calibration_sets
    )

    return {
        "exercise_name": calibration.exercise.name,
        "exercise": calibration.exercise_id,
        "status": calibration.status,
        "estimated_working_weight": calibration.estimated_working_weight,
        "target_reps": calibration.target_reps,
        "target_rir": calibration.target_rir,
        "confidence": calibration.confidence,
        "set_count": len(calibration_sets),
        "volume": _round_metric(volume),
        "sets": calibration_sets,
    }


def build_session_coach_context(workout, set_logs, workout_progression, notes="", calibrations=None):
    serialized_sets = [_serialize_set_log(set_log) for set_log in set_logs]
    serialized_calibrations = [
        _serialize_calibration(calibration)
        for calibration in calibrations or []
    ]
    exercise_map = {}

    for set_log in serialized_sets:
        exercise_key = set_log["training_exercise"] or set_log["exercise_name"]
        exercise_summary = exercise_map.setdefault(
            exercise_key,
            {
                "exercise_name": set_log["exercise_name"],
                "completed_sets": 0,
                "working_sets": 0,
                "warmup_sets": 0,
                "drop_sets": 0,
                "failures": 0,
                "volume": 0,
                "rir_values": [],
                "calibration": None,
            },
        )

        exercise_summary["completed_sets"] += 1
        exercise_summary["volume"] += _number_or_zero(set_log["weight_used"]) * _number_or_zero(
            set_log["reps_completed"]
        )

        if set_log["set_type"] == "WORKING":
            exercise_summary["working_sets"] += 1
        elif set_log["set_type"] == "WARMUP":
            exercise_summary["warmup_sets"] += 1
        elif set_log["set_type"] == "DROP":
            exercise_summary["drop_sets"] += 1

        if set_log["reached_failure"]:
            exercise_summary["failures"] += 1

        if set_log["rir"] is not None:
            exercise_summary["rir_values"].append(set_log["rir"])

    for calibration in serialized_calibrations:
        exercise_key = calibration["exercise"]
        exercise_summary = exercise_map.setdefault(
            exercise_key,
            {
                "exercise_name": calibration["exercise_name"],
                "completed_sets": 0,
                "working_sets": 0,
                "warmup_sets": 0,
                "drop_sets": 0,
                "failures": 0,
                "volume": 0,
                "rir_values": [],
                "calibration": None,
            },
        )
        exercise_summary["completed_sets"] += calibration["set_count"]
        exercise_summary["volume"] += calibration["volume"]
        exercise_summary["calibration"] = {
            "status": calibration["status"],
            "estimated_working_weight": calibration["estimated_working_weight"],
            "target_reps": calibration["target_reps"],
            "target_rir": calibration["target_rir"],
            "confidence": calibration["confidence"],
            "set_count": calibration["set_count"],
            "volume": calibration["volume"],
        }

    exercise_summaries = []
    total_volume = 0
    total_failures = 0
    calibration_set_count = sum(calibration["set_count"] for calibration in serialized_calibrations)
    calibration_volume = sum(calibration["volume"] for calibration in serialized_calibrations)

    for exercise_summary in exercise_map.values():
        total_volume += exercise_summary["volume"]
        total_failures += exercise_summary["failures"]
        rir_values = exercise_summary.pop("rir_values")
        exercise_summary["volume"] = _round_metric(exercise_summary["volume"])
        exercise_summary["average_rir"] = (
            _round_metric(sum(rir_values) / len(rir_values)) if rir_values else None
        )
        exercise_summaries.append(exercise_summary)

    return {
        "workout": {
            "id": workout.id,
            "name": workout.name,
            "order": workout.order,
        },
        "session": {
            "notes": notes,
            "training_sets": len(serialized_sets),
            "calibration_sets": calibration_set_count,
            "total_sets": len(serialized_sets) + calibration_set_count,
            "total_volume": _round_metric(total_volume),
            "calibration_volume": _round_metric(calibration_volume),
            "failure_count": total_failures,
            "exercise_count": len(exercise_summaries),
        },
        "exercises": exercise_summaries,
        "progression": {
            "summary": workout_progression.get("summary", {}),
            "recommendations": [
                {
                    "exercise_name": recommendation.get("exercise_name"),
                    "action": recommendation.get("action"),
                    "recommended_weight": recommendation.get("recommended_weight"),
                    "recommended_sets": recommendation.get("recommended_sets"),
                    "target_reps": recommendation.get("target_reps"),
                    "target_rir": recommendation.get("target_rir"),
                    "reason": recommendation.get("reason"),
                }
                for recommendation in workout_progression.get("recommendations", [])
            ],
        },
    }


def build_exercise_feedback(context):
    feedback = []

    for exercise in context.get("exercises", []):
        calibration = exercise.get("calibration")

        if calibration:
            weight = calibration.get("estimated_working_weight")
            confidence = calibration.get("confidence") or "baixa"
            feedback.append({
                "exercise_name": exercise["exercise_name"],
                "title": f"{exercise['exercise_name']}: base criada",
                "message": (
                    f"Foram registadas {calibration['set_count']} série(s) experimentais e o peso de trabalho "
                    f"ficou estimado em {weight}kg com confiança {confidence}. No próximo treino já há uma "
                    "primeira carga real para começar, sem adivinhar."
                ),
            })
            continue

        if exercise["working_sets"]:
            rir_text = (
                f"RIR médio {exercise['average_rir']}"
                if exercise["average_rir"] is not None
                else "sem RIR médio suficiente"
            )
            failure_text = (
                f" Teve {exercise['failures']} falha(s), por isso a próxima decisão deve ser prudente."
                if exercise["failures"]
                else " Sem falhas registadas, bom sinal para consolidar."
            )
            feedback.append({
                "exercise_name": exercise["exercise_name"],
                "title": f"{exercise['exercise_name']}: trabalho registado",
                "message": (
                    f"Completaste {exercise['working_sets']} série(s) normal(is), "
                    f"{exercise['volume']}kg de volume e {rir_text}.{failure_text}"
                ),
            })

    return feedback[:6]


def build_local_coach_summary(context):
    session = context["session"]
    action_counts = context["progression"]["summary"].get("action_counts", {})
    increase_count = action_counts.get("increase_load", 0)
    reduce_count = action_counts.get("reduce_volume", 0)
    maintain_count = action_counts.get("maintain_load", 0) + action_counts.get("maintain", 0)

    if session["total_sets"] == 0:
        headline = "Treino terminado sem séries registadas"
        summary = "Não há dados suficientes para analisar performance. No próximo treino, regista pelo menos as séries normais."
    elif session.get("training_sets", 0) == 0 and session.get("calibration_sets", 0) > 0:
        headline = "Calibração concluída: já temos uma base real"
        summary = "O treino experimental criou dados úteis para o próximo treino. A app já tem pesos de trabalho estimados por exercício calibrado."
    elif reduce_count or session["failure_count"] >= 2:
        headline = "Sessão exigente: protege a recuperação"
        summary = "O treino mostrou sinais de fadiga. A melhor decisão agora é consolidar técnica, descanso e volume antes de forçar progressão."
    elif increase_count:
        headline = "Boa sessão: há margem para progredir"
        summary = "A performance deixou sinais positivos. Algumas cargas podem subir mantendo o alvo de reps e uma margem de esforço controlada."
    else:
        headline = "Sessão consistente: consolida o plano"
        summary = "O treino ficou dentro do esperado. Mantém o foco em repetir boas séries antes de acelerar a progressão."

    focus_points = []

    if increase_count:
        focus_points.append(f"{increase_count} exercício(s) com margem para subir carga.")

    if reduce_count:
        focus_points.append(f"{reduce_count} exercício(s) pedem redução de volume ou carga.")

    if maintain_count:
        focus_points.append(f"{maintain_count} exercício(s) devem consolidar antes de subir.")

    if session["failure_count"]:
        focus_points.append(f"{session['failure_count']} série(s) chegaram à falha.")

    if session.get("calibration_sets"):
        focus_points.append(f"{session['calibration_sets']} série(s) experimentais transformadas em dados de treino.")

    if not focus_points:
        focus_points.append("Continua a registar carga, reps e esforço para melhorar a leitura do coach.")

    return {
        "headline": headline,
        "summary": summary,
        "focus_points": focus_points[:4],
        "exercise_feedback": build_exercise_feedback(context),
        "next_session_strategy": "Segue as recomendações por exercício e dá prioridade a séries limpas, com RIR controlado.",
        "recovery_note": "Se a sensação de fadiga continuar alta, mantém cargas e aumenta ligeiramente o descanso entre séries.",
        "metrics": session,
        "source": "local_coach_fallback",
        "status": "llm_disabled",
        "model": None,
    }


def _extract_response_text(response_data):
    if response_data.get("output_text"):
        return response_data["output_text"]

    text_parts = []

    for output_item in response_data.get("output", []):
        for content_item in output_item.get("content", []):
            text = content_item.get("text")

            if text:
                text_parts.append(text)

    return "\n".join(text_parts).strip()


def _normalize_ai_summary(summary, fallback_summary, model):
    if not isinstance(summary, dict):
        return fallback_summary

    return {
        "headline": str(summary.get("headline") or fallback_summary["headline"]),
        "summary": str(summary.get("summary") or fallback_summary["summary"]),
        "focus_points": [
            str(point)
            for point in summary.get("focus_points", fallback_summary["focus_points"])
            if point
        ][:4],
        "exercise_feedback": [
            {
                "exercise_name": str(item.get("exercise_name") or ""),
                "title": str(item.get("title") or item.get("exercise_name") or ""),
                "message": str(item.get("message") or ""),
            }
            for item in summary.get("exercise_feedback", fallback_summary.get("exercise_feedback", []))
            if isinstance(item, dict) and (item.get("message") or item.get("title"))
        ][:6],
        "next_session_strategy": str(
            summary.get("next_session_strategy") or fallback_summary["next_session_strategy"]
        ),
        "recovery_note": str(summary.get("recovery_note") or fallback_summary["recovery_note"]),
        "metrics": fallback_summary["metrics"],
        "source": "openai_responses_api",
        "status": "llm_enabled",
        "model": model,
    }


def _request_openai_coach_summary(context, api_key, model):
    payload = {
        "model": model,
        "instructions": (
            "És o AI Coach do SHAPETRONYC. Analisa uma sessão de treino e responde em português europeu. "
            "Não dês aconselhamento médico. Se houver dor ou fadiga forte, recomenda prudência, técnica e recuperação. "
            "Fala de forma dinâmica sobre cada exercício usando exercise_feedback. "
            "Devolve apenas JSON válido com estas chaves: headline, summary, focus_points, exercise_feedback, next_session_strategy, recovery_note. "
            "exercise_feedback deve ser uma lista de objetos com exercise_name, title e message."
        ),
        "input": json.dumps(context, ensure_ascii=False),
    }
    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
        response_data = json.loads(response.read().decode("utf-8"))

    response_text = _extract_response_text(response_data)
    return json.loads(response_text)


def generate_session_ai_coach_summary(workout, set_logs, workout_progression, notes="", calibrations=None):
    context = build_session_coach_context(workout, set_logs, workout_progression, notes, calibrations)
    fallback_summary = build_local_coach_summary(context)
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    model = getattr(settings, "AI_COACH_MODEL", "gpt-5.5")

    if not api_key:
        return fallback_summary

    try:
        ai_summary = _request_openai_coach_summary(context, api_key, model)
    except (json.JSONDecodeError, TimeoutError, urllib.error.URLError, urllib.error.HTTPError):
        return {
            **fallback_summary,
            "status": "llm_error",
            "model": model,
        }

    return _normalize_ai_summary(ai_summary, fallback_summary, model)
