import json
import socket
import urllib.error
import urllib.request

from django.conf import settings


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_TIMEOUT_SECONDS = 20
OLLAMA_TIMEOUT_SECONDS = 60
ALLOWED_NEXT_SET_TYPES = {"WARMUP", "WORKING", "DROP", "COMPLETE"}
ALLOWED_EXERCISE_STATUS = {"continue", "complete"}
ALLOWED_ACTIONS = {
    "increase_weight",
    "maintain_weight",
    "decrease_weight",
    "add_set",
    "stop_exercise",
    "do_backoff_set",
    "skip_backoff_set",
    "deload",
    "reduce_volume",
    "increase_volume",
    "flag_pain_or_risk",
    "suggest_exercise_replacement",
}
SUPPORTED_PROVIDERS = {"openai", "ollama", "local"}
MAX_LLM_HISTORY_SETS = 60

TRAINING_DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "recommended_weight": {"type": "string"},
        "target_reps": {"type": "string"},
        "target_rir": {"type": "integer"},
        "add_set": {"type": "boolean"},
        "stop_exercise": {"type": "boolean"},
        "do_backoff_set": {"type": "boolean"},
        "backoff_weight": {"type": ["string", "null"]},
        "fatigue_score": {"type": "integer"},
        "recovery_score": {"type": "integer"},
        "readiness_score": {"type": "integer"},
        "recommended_rest_seconds": {"type": "integer"},
        "next_set_type": {"type": "string", "enum": ["WARMUP", "WORKING", "DROP", "COMPLETE"]},
        "exercise_status": {"type": "string", "enum": ["continue", "complete"]},
        "action": {"type": "string", "enum": sorted(ALLOWED_ACTIONS)},
        "reason": {"type": "string"},
        "guidance_title": {"type": "string"},
        "guidance_message": {"type": "string"},
        "confidence": {"type": "string", "enum": ["alta", "média", "baixa"]},
        "decision_basis": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "recommended_weight",
        "target_reps",
        "target_rir",
        "add_set",
        "stop_exercise",
        "do_backoff_set",
        "backoff_weight",
        "fatigue_score",
        "recovery_score",
        "readiness_score",
        "recommended_rest_seconds",
        "next_set_type",
        "exercise_status",
        "action",
        "reason",
        "guidance_title",
        "guidance_message",
        "confidence",
        "decision_basis",
    ],
    "additionalProperties": False,
}


def _number_or_none(value):
    if value in ("", None):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_default(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _compact_set(set_log):
    return {
        "session_id": set_log.get("workout_session"),
        "date": set_log.get("created_at"),
        "set_number": set_log.get("set_number"),
        "set_type": set_log.get("set_type"),
        "weight": set_log.get("weight_used"),
        "reps": set_log.get("reps_completed"),
        "rir": set_log.get("rir"),
        "failure": set_log.get("reached_failure"),
        "notes": str(set_log.get("notes", ""))[:160],
        "session_notes": str(set_log.get("session_notes", ""))[:160],
    }


def _compact_decision(local_decision):
    return {
        "recommended_weight": local_decision.get("recommended_weight"),
        "target_reps": local_decision.get("target_reps"),
        "recommended_rest_seconds": local_decision.get("recommended_rest_seconds"),
        "next_set_type": local_decision.get("next_set_type"),
        "exercise_status": local_decision.get("exercise_status"),
        "action": local_decision.get("action"),
        "reason": local_decision.get("reason"),
        "confidence": local_decision.get("confidence"),
        "readiness_score": local_decision.get("readiness_score"),
        "fatigue_score": local_decision.get("fatigue_score"),
        "recovery_score": local_decision.get("recovery_score"),
        "decision_basis": local_decision.get("decision_basis", []),
        "context": local_decision.get("context", {}),
        "guardrails": local_decision.get("guardrails", {}),
    }


def _build_llm_context(local_decision, request_context):
    return {
        "local_safety_decision": _compact_decision(local_decision),
        "current_set_result": {
            "weight": request_context.get("weight"),
            "reps": request_context.get("reps"),
            "rir": request_context.get("rir"),
            "is_failure": request_context.get("is_failure"),
            "notes": request_context.get("notes"),
            "set_type": request_context.get("set_type"),
            "set_number": request_context.get("set_number"),
            "total_sets": request_context.get("total_sets"),
        },
        "user": request_context.get("user_context", {}),
        "exercise": request_context.get("exercise_context", {}),
        "session": request_context.get("session_context", {}),
        "targets": {
            "target_min_reps": request_context.get("target_min_reps"),
            "target_max_reps": request_context.get("target_max_reps"),
            "target_rir": request_context.get("target_rir"),
            "planned_sets": request_context.get("total_sets"),
        },
        "current_sets": [
            _compact_set(set_log)
            for set_log in request_context.get("current_sets", [])
        ],
        "previous_session_sets": [
            _compact_set(set_log)
            for set_log in request_context.get("previous_sets", [])
        ],
        "recent_history_sets": [
            _compact_set(set_log)
            for set_log in request_context.get("history_sets", [])[:MAX_LLM_HISTORY_SETS]
        ],
        "rules": {
            "allowed_actions": sorted(ALLOWED_ACTIONS),
            "priorities": ["segurança", "técnica", "recuperação", "cumprimento do plano", "progressão"],
            "feedback_overrides_performance": True,
            "must_return_json": True,
            "must_respect_complete_exercise_guardrail": (
                local_decision.get("exercise_status") == "complete"
            ),
            "block_increase": local_decision.get("guardrails", {}).get("block_increase", False),
            "must_stop": local_decision.get("guardrails", {}).get("must_stop", False),
        },
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


def _request_openai_training_decision(context, api_key, model):
    payload = {
        "model": model,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "training_decision",
                "schema": TRAINING_DECISION_SCHEMA,
                "strict": True,
            },
        },
        "instructions": (
            "És o AI Training Coach do SHAPETRONYC. Estás a decidir a próxima ação durante um exercício, "
            "não no final do treino. Usa o histórico dos últimos 15 treinos, as séries já feitas hoje, o objetivo do "
            "utilizador, a faixa de reps, o RIR alvo, fadiga, recuperação e notas. Prioriza sempre segurança, técnica "
            "e recuperação antes de progressão. Se existir conflito entre performance e feedback do utilizador, o "
            "feedback manda. Só podes escolher uma ação da lista permitida. Não dês aconselhamento médico. "
            "Devolve apenas JSON válido com estas chaves: recommended_weight, target_reps, recommended_rest_seconds, "
            "target_rir, add_set, stop_exercise, do_backoff_set, backoff_weight, fatigue_score, recovery_score, "
            "readiness_score, next_set_type, exercise_status, action, reason, guidance_title, guidance_message, "
            "confidence, decision_basis."
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

    return json.loads(_extract_response_text(response_data))


def _request_ollama_training_decision(context, base_url, model):
    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "think": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 350,
        },
        "messages": [
            {
                "role": "system",
                "content": (
                    "És o AI Training Coach do SHAPETRONYC. Decide a próxima ação durante um exercício. "
                    "Usa o histórico dos últimos 15 treinos, as séries feitas hoje, objetivo do utilizador, faixa de "
                    "reps, RIR alvo, fadiga, recuperação e notas. Segurança, técnica e recuperação têm prioridade "
                    "sobre progressão. Só podes escolher uma ação da lista permitida. "
                    "Responde só com JSON válido com as chaves: recommended_weight, target_reps, "
                    "target_rir, add_set, stop_exercise, do_backoff_set, backoff_weight, fatigue_score, "
                    "recovery_score, readiness_score, recommended_rest_seconds, next_set_type, exercise_status, "
                    "action, reason, guidance_title, guidance_message, confidence, decision_basis."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(context, ensure_ascii=False),
            },
        ],
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
        response_data = json.loads(response.read().decode("utf-8"))

    content = response_data.get("message", {}).get("content", "")
    return json.loads(content)


def _normalize_ai_decision(ai_decision, local_decision, model, source):
    if not isinstance(ai_decision, dict):
        return local_decision

    next_set_type = ai_decision.get("next_set_type") or local_decision.get("next_set_type")
    exercise_status = ai_decision.get("exercise_status") or local_decision.get("exercise_status", "continue")
    action = ai_decision.get("action") or local_decision.get("action")
    guardrails = local_decision.get("guardrails", {})

    if next_set_type not in ALLOWED_NEXT_SET_TYPES:
        next_set_type = local_decision.get("next_set_type", "WORKING")

    if exercise_status not in ALLOWED_EXERCISE_STATUS:
        exercise_status = local_decision.get("exercise_status", "continue")

    if action not in ALLOWED_ACTIONS:
        action = local_decision.get("action", "maintain_weight")
        if action not in ALLOWED_ACTIONS:
            action = "maintain_weight"

    # Safety guardrail: when the local engine decides the exercise should stop,
    # the LLM may explain it, but it cannot force more volume.
    if local_decision.get("exercise_status") == "complete" or guardrails.get("must_stop"):
        next_set_type = "COMPLETE"
        exercise_status = "complete"
        action = local_decision.get("action", "stop_exercise")

    recommended_weight = ai_decision.get("recommended_weight", local_decision.get("recommended_weight"))
    target_reps = ai_decision.get("target_reps", local_decision.get("target_reps"))
    guardrail_applied = False
    guardrail_reason = ""
    local_weight = _number_or_none(local_decision.get("recommended_weight"))
    ai_weight = _number_or_none(recommended_weight)

    if (
        local_decision.get("next_set_type") == "WARMUP"
        and next_set_type == "WORKING"
        and (ai_weight is None or local_weight is None or ai_weight <= local_weight)
    ):
        next_set_type = "WARMUP"
        exercise_status = "continue"
        recommended_weight = local_decision.get("recommended_weight")
        target_reps = local_decision.get("target_reps")
        guardrail_applied = True
        guardrail_reason = "A IA tentou transformar uma carga de aquecimento em série de trabalho."

    if guardrails.get("block_increase") and (action == "increase_weight" or (ai_weight is not None and local_weight is not None and ai_weight > local_weight)):
        next_set_type = local_decision.get("next_set_type", "WORKING")
        exercise_status = local_decision.get("exercise_status", "continue")
        recommended_weight = local_decision.get("recommended_weight")
        target_reps = local_decision.get("target_reps")
        action = local_decision.get("action", "maintain_weight")
        guardrail_applied = True
        guardrail_reason = "A IA tentou subir carga apesar de um bloqueio de segurança, fadiga ou feedback do utilizador."

    if next_set_type == "COMPLETE" or exercise_status == "complete":
        recommended_weight = ""
        target_reps = ""
    elif _number_or_none(recommended_weight) is None:
        recommended_weight = local_decision.get("recommended_weight")

    reason = ai_decision.get("reason") or local_decision.get("reason")
    guidance_title = ai_decision.get("guidance_title") or local_decision.get("guidance_title")
    guidance_message = ai_decision.get("guidance_message") or local_decision.get("guidance_message")

    if guardrail_applied:
        action = local_decision.get("action")
        if action not in ALLOWED_ACTIONS:
            action = "maintain_weight"
        reason = local_decision.get("reason")
        guidance_title = local_decision.get("guidance_title")
        guidance_message = local_decision.get("guidance_message")

    return {
        **local_decision,
        "recommended_weight": recommended_weight,
        "target_reps": target_reps,
        "target_reps_label": local_decision.get("target_reps_label"),
        "target_rir": _int_or_default(ai_decision.get("target_rir", local_decision.get("target_rir", 2)), 2),
        "add_set": bool(ai_decision.get("add_set", local_decision.get("add_set", False))) and exercise_status != "complete",
        "stop_exercise": bool(ai_decision.get("stop_exercise", local_decision.get("stop_exercise", False))) or exercise_status == "complete",
        "do_backoff_set": bool(ai_decision.get("do_backoff_set", local_decision.get("do_backoff_set", False))) and exercise_status != "complete",
        "backoff_weight": ai_decision.get("backoff_weight", local_decision.get("backoff_weight")),
        "fatigue_score": _int_or_default(ai_decision.get("fatigue_score", local_decision.get("fatigue_score", 0)), 0),
        "recovery_score": _int_or_default(ai_decision.get("recovery_score", local_decision.get("recovery_score", 0)), 0),
        "readiness_score": _int_or_default(ai_decision.get("readiness_score", local_decision.get("readiness_score", 0)), 0),
        "recommended_rest_seconds": ai_decision.get(
            "recommended_rest_seconds",
            local_decision.get("recommended_rest_seconds"),
        ),
        "next_set_type": next_set_type,
        "exercise_status": exercise_status,
        "action": str(action),
        "reason": str(reason),
        "guidance_title": str(guidance_title),
        "guidance_message": str(guidance_message),
        "confidence": str(ai_decision.get("confidence") or local_decision.get("confidence")),
        "decision_basis": [
            str(item)
            for item in ai_decision.get("decision_basis", local_decision.get("decision_basis", []))
            if item
        ][:5],
        "source": source,
        "llm_status": "llm_enabled",
        "model": model,
        "guardrail_applied": guardrail_applied,
        "guardrail_reason": guardrail_reason,
    }


def generate_ai_training_decision(local_decision, request_context):
    provider = getattr(settings, "AI_TRAINING_DECISION_PROVIDER", "local")
    provider = provider if provider in SUPPORTED_PROVIDERS else "local"
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    model = getattr(settings, "AI_TRAINING_DECISION_MODEL", getattr(settings, "AI_COACH_MODEL", "gpt-5.5"))

    if provider == "local":
        return {
            **local_decision,
            "llm_status": "llm_disabled",
            "llm_provider": "local",
            "model": None,
        }

    context = _build_llm_context(local_decision, request_context)

    if provider == "ollama":
        ollama_model = getattr(settings, "OLLAMA_TRAINING_DECISION_MODEL", "qwen3:8b")
        base_url = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")

        try:
            ai_decision = _request_ollama_training_decision(context, base_url, ollama_model)
        except urllib.error.HTTPError as error:
            return {
                **local_decision,
                "llm_status": "llm_error",
                "llm_provider": "ollama",
                "llm_error_type": "http_error",
                "llm_error_detail": f"Ollama HTTP {error.code}",
                "model": ollama_model,
            }
        except json.JSONDecodeError:
            return {
                **local_decision,
                "llm_status": "llm_error",
                "llm_provider": "ollama",
                "llm_error_type": "json_decode_error",
                "llm_error_detail": "Ollama response was not valid JSON",
                "model": ollama_model,
            }
        except (TimeoutError, socket.timeout, urllib.error.URLError):
            return {
                **local_decision,
                "llm_status": "llm_error",
                "llm_provider": "ollama",
                "llm_error_type": "request_error",
                "llm_error_detail": "Ollama request failed",
                "model": ollama_model,
            }

        return _normalize_ai_decision(ai_decision, local_decision, ollama_model, "ollama_training_decision")

    if not api_key:
        return {
            **local_decision,
            "llm_status": "llm_disabled",
            "llm_provider": "openai",
            "model": None,
        }

    try:
        ai_decision = _request_openai_training_decision(context, api_key, model)
    except urllib.error.HTTPError as error:
        return {
            **local_decision,
            "llm_status": "llm_error",
            "llm_provider": "openai",
            "llm_error_type": "http_error",
            "llm_error_detail": f"OpenAI HTTP {error.code}",
            "model": model,
        }
    except json.JSONDecodeError:
        return {
            **local_decision,
            "llm_status": "llm_error",
            "llm_provider": "openai",
            "llm_error_type": "json_decode_error",
            "llm_error_detail": "OpenAI response was not valid JSON",
            "model": model,
        }
    except (TimeoutError, socket.timeout, urllib.error.URLError):
        return {
            **local_decision,
            "llm_status": "llm_error",
            "llm_provider": "openai",
            "llm_error_type": "request_error",
            "llm_error_detail": "OpenAI request failed",
            "model": model,
        }

    return _normalize_ai_decision(ai_decision, local_decision, model, "openai_training_decision")
