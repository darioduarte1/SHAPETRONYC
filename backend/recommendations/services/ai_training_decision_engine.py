# =============================================================================
# ai_training_decision_engine.py
# -----------------------------------------------------------------------------
# Motor de decisão para orientar a próxima série durante o treino.
# É usado após o registo de uma série para recomendar manter, subir, baixar carga ou ajustar o plano.
# Considera reps, RIR, falha, histórico e segurança antes de sugerir a próxima ação.
# =============================================================================
import json
import socket
import urllib.error
import urllib.request

from django.conf import settings

from exercises.services.weight_scale import get_exercise_weight_scale, snap_to_available_weight


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_TIMEOUT_SECONDS = 20
OLLAMA_TIMEOUT_SECONDS = 60
ALLOWED_NEXT_SET_TYPES = {"WARMUP", "WORKING", "DROP", "COMPLETE"}
ALLOWED_EXERCISE_STATUS = {"continue", "complete"}
ALLOWED_EXERCISE_STATES = {
    "CONTINUE",
    "ADJUST_LOAD",
    "BACKOFF",
    "FINAL_SET",
    "ADD_VOLUME",
    "END_EXERCISE",
    "SAFETY_STOP",
    "DELOAD_REQUIRED",
}
ALLOWED_ACTIONS = {
    "increase_weight",
    "maintain_weight",
    "decrease_weight",
    "add_set",
    "maintain_or_small_backoff",
    "small_backoff",
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
        "exercise_state": {"type": "string", "enum": sorted(ALLOWED_EXERCISE_STATES)},
        "target_reps": {"type": "string"},
        "target_rir": {"type": "integer"},
        "add_set": {"type": "boolean"},
        "stop_exercise": {"type": "boolean"},
        "do_backoff_set": {"type": "boolean"},
        "backoff_weight": {"type": ["string", "null"]},
        "fatigue_score": {"type": "integer"},
        "recovery_score": {"type": "integer"},
        "readiness_score": {"type": "integer"},
        "valid_working_sets": {"type": "integer"},
        "minimum_valid_sets": {"type": "integer"},
        "local_fatigue_score": {"type": "integer"},
        "global_fatigue_score": {"type": "integer"},
        "stimulus_score": {"type": "integer"},
        "fatigue_cost": {"type": "integer"},
        "recommended_rest_seconds": {"type": "integer"},
        "next_set_type": {"type": "string", "enum": ["WARMUP", "WORKING", "DROP", "COMPLETE"]},
        "exercise_status": {"type": "string", "enum": ["continue", "complete"]},
        "action": {"type": "string", "enum": sorted(ALLOWED_ACTIONS)},
        "reason": {"type": "string"},
        "guidance_title": {"type": "string"},
        "guidance_message": {"type": "string"},
        "confidence": {"type": "string", "enum": ["alta", "média", "baixa"]},
        "confidence_score": {"type": "number"},
        "decision_basis": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "recommended_weight",
        "exercise_state",
        "target_reps",
        "target_rir",
        "add_set",
        "stop_exercise",
        "do_backoff_set",
        "backoff_weight",
        "fatigue_score",
        "recovery_score",
        "readiness_score",
        "valid_working_sets",
        "minimum_valid_sets",
        "local_fatigue_score",
        "global_fatigue_score",
        "stimulus_score",
        "fatigue_cost",
        "recommended_rest_seconds",
        "next_set_type",
        "exercise_status",
        "action",
        "reason",
        "guidance_title",
        "guidance_message",
        "confidence",
        "confidence_score",
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
    set_type = set_log.get("set_type")

    return {
        "session_id": set_log.get("workout_session"),
        "date": set_log.get("created_at"),
        "set_number": set_log.get("set_number"),
        "set_type": set_type,
        "weight": set_log.get("weight_used"),
        "reps": set_log.get("reps_completed"),
        "rir": None if set_type == "WARMUP" else set_log.get("rir"),
        "failure": False if set_type == "WARMUP" else set_log.get("reached_failure"),
        "effort_tracking": "not_applicable" if set_type == "WARMUP" else "rir",
        "notes": str(set_log.get("notes", ""))[:160],
        "session_notes": str(set_log.get("session_notes", ""))[:160],
    }


def _compact_decision(local_decision):
    return {
        "exercise_state": local_decision.get("exercise_state"),
        "recommended_weight": local_decision.get("recommended_weight"),
        "target_reps": local_decision.get("target_reps"),
        "recommended_rest_seconds": local_decision.get("recommended_rest_seconds"),
        "next_set_type": local_decision.get("next_set_type"),
        "exercise_status": local_decision.get("exercise_status"),
        "action": local_decision.get("action"),
        "reason": local_decision.get("reason"),
        "confidence": local_decision.get("confidence"),
        "confidence_score": local_decision.get("confidence_score"),
        "readiness_score": local_decision.get("readiness_score"),
        "fatigue_score": local_decision.get("fatigue_score"),
        "local_fatigue_score": local_decision.get("local_fatigue_score"),
        "global_fatigue_score": local_decision.get("global_fatigue_score"),
        "stimulus_score": local_decision.get("stimulus_score"),
        "fatigue_cost": local_decision.get("fatigue_cost"),
        "recovery_score": local_decision.get("recovery_score"),
        "valid_working_sets": local_decision.get("valid_working_sets"),
        "minimum_valid_sets": local_decision.get("minimum_valid_sets"),
        "maximum_allowed_sets": local_decision.get("maximum_allowed_sets"),
        "decision_basis": local_decision.get("decision_basis", []),
        "context": local_decision.get("context", {}),
        "guardrails": local_decision.get("guardrails", {}),
    }


def _available_weights_from_context(exercise_context):
    scale = get_exercise_weight_scale(exercise_context)

    return {
        "configured": scale["configured"],
        "main_weight_options": scale["main_weight_options"],
        "micro_weight_options": scale["micro_weight_options"],
        "available_weights": scale["available_weights"],
    }


def _build_ai_permissions(local_decision, request_context):
    guardrails = local_decision.get("guardrails", {})
    context = local_decision.get("context", {})
    local_action = local_decision.get("action")
    exercise_status = local_decision.get("exercise_status")
    next_set_type = local_decision.get("next_set_type")
    failure_class = context.get("failure_class")
    working_set_count = context.get("working_set_count", 0)
    planned_sets = context.get("planned_sets", request_context.get("total_sets") or 3)
    may_increase = (
        local_action in {"increase_weight", "increase_volume"}
        and not guardrails.get("block_increase")
        and not guardrails.get("must_stop")
        and exercise_status != "complete"
    )
    may_stop = (
        exercise_status == "complete"
        or guardrails.get("must_stop")
        or not (
            failure_class in {"productive_failure", "acceptable_failure"}
            and working_set_count < planned_sets
        )
    )

    return {
        "can_change_message": True,
        "can_change_reason": True,
        "can_change_confidence": True,
        "can_change_rest_seconds": exercise_status != "complete",
        "can_change_weight": local_action in {
            "increase_weight",
            "decrease_weight",
            "maintain_or_small_backoff",
            "small_backoff",
            "do_backoff_set",
        } and not guardrails.get("must_stop"),
        "can_increase_weight": may_increase,
        "can_decrease_weight": not guardrails.get("must_stop") and exercise_status != "complete",
        "can_change_reps": exercise_status != "complete",
        "can_add_set": bool(local_decision.get("add_set")) and exercise_status != "complete",
        "can_stop_exercise": bool(may_stop),
        "can_change_next_set_type": not (
            next_set_type == "WARMUP"
            or exercise_status == "complete"
            or guardrails.get("must_stop")
        ),
        "must_preserve_local_stop": bool(exercise_status == "complete" or guardrails.get("must_stop")),
        "must_preserve_warmup": next_set_type == "WARMUP",
        "must_not_increase": bool(guardrails.get("block_increase") or not may_increase),
        "must_not_stop": bool(not may_stop),
    }


def _build_safety_constraints(local_decision, request_context):
    local_weight = _number_or_none(local_decision.get("recommended_weight"))
    exercise_context = request_context.get("exercise_context", {})
    weight_scale = _available_weights_from_context(exercise_context)
    permissions = _build_ai_permissions(local_decision, request_context)

    min_weight = local_weight
    max_weight = local_weight

    if local_weight is not None and permissions["can_decrease_weight"]:
        min_weight = 0

    if local_weight is not None and permissions["can_increase_weight"]:
        max_weight = max(weight_scale["available_weights"] or [local_weight])

    return {
        "weight_scale": weight_scale,
        "local_recommended_weight": local_decision.get("recommended_weight"),
        "min_weight": min_weight,
        "max_weight": max_weight,
        "target_reps": local_decision.get("target_reps"),
        "target_rir": local_decision.get("target_rir"),
        "next_set_type": local_decision.get("next_set_type"),
        "exercise_status": local_decision.get("exercise_status"),
        "allowed_actions": sorted(ALLOWED_ACTIONS),
        "allowed_next_set_types": sorted(ALLOWED_NEXT_SET_TYPES),
        "allowed_exercise_status": sorted(ALLOWED_EXERCISE_STATUS),
        "guardrails": local_decision.get("guardrails", {}),
    }


def _compact_ai_attempt(ai_decision):
    if not isinstance(ai_decision, dict):
        return None

    return {
        "recommended_weight": ai_decision.get("recommended_weight"),
        "target_reps": ai_decision.get("target_reps"),
        "target_rir": ai_decision.get("target_rir"),
        "recommended_rest_seconds": ai_decision.get("recommended_rest_seconds"),
        "next_set_type": ai_decision.get("next_set_type"),
        "exercise_status": ai_decision.get("exercise_status"),
        "exercise_state": ai_decision.get("exercise_state"),
        "action": ai_decision.get("action"),
        "add_set": ai_decision.get("add_set"),
        "stop_exercise": ai_decision.get("stop_exercise"),
        "do_backoff_set": ai_decision.get("do_backoff_set"),
        "reason": ai_decision.get("reason"),
        "guidance_title": ai_decision.get("guidance_title"),
        "guidance_message": ai_decision.get("guidance_message"),
        "confidence": ai_decision.get("confidence"),
        "decision_basis": ai_decision.get("decision_basis", []),
    }


def _build_decision_envelope(
    local_decision,
    request_context,
    final_decision,
    ai_decision=None,
    validation_status="local_only",
    validation_reasons=None,
):
    return {
        "strategy": "rules_decide_ai_adjusts_inside_rules",
        "local_decision": _compact_decision(local_decision),
        "ai_permissions": _build_ai_permissions(local_decision, request_context),
        "safety_constraints": _build_safety_constraints(local_decision, request_context),
        "ai_decision": _compact_ai_attempt(ai_decision),
        "final_decision": _compact_decision(final_decision),
        "validation": {
            "status": validation_status,
            "reasons": validation_reasons or [],
            "guardrail_applied": bool(final_decision.get("guardrail_applied")),
            "guardrail_reason": final_decision.get("guardrail_reason", ""),
        },
    }


def _with_decision_envelope(
    final_decision,
    local_decision,
    request_context,
    ai_decision=None,
    validation_status="local_only",
    validation_reasons=None,
):
    return {
        **final_decision,
        "decision_envelope": _build_decision_envelope(
            local_decision,
            request_context,
            final_decision,
            ai_decision,
            validation_status,
            validation_reasons,
        ),
    }


def _build_llm_context(local_decision, request_context):
    ai_permissions = _build_ai_permissions(local_decision, request_context)
    safety_constraints = _build_safety_constraints(local_decision, request_context)

    return {
        "local_safety_decision": _compact_decision(local_decision),
        "ai_permissions": ai_permissions,
        "safety_constraints": safety_constraints,
        "current_set_result": {
            "weight": request_context.get("weight"),
            "reps": request_context.get("reps"),
            "rir": None if request_context.get("set_type") == "WARMUP" else request_context.get("rir"),
            "is_failure": False if request_context.get("set_type") == "WARMUP" else request_context.get("is_failure"),
            "effort_tracking": "not_applicable" if request_context.get("set_type") == "WARMUP" else "rir",
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
            "warmup_sets_do_not_use_rir": True,
            "warmup_sets_assume_load_is_liftable": True,
            "progression_goal": "12 reps consistentes com RIR controlado; não perseguir carga",
            "increase_load_requires": [
                "12 reps na série normal",
                "RIR >= 3",
                "sem falha",
                "técnica boa e sem dor",
                "próximo peso disponível na escala registada do exercício",
                "se o salto de peso for superior a 10%, exigir RIR >= 4",
                "sem falhas recentes nesse próximo peso",
            ],
            "maintain_load_when": [
                "12 reps com RIR 1-2",
                "10-11 reps sem falha",
                "sem próximo peso registado na escala do exercício",
                "histórico recente bloqueia progressão",
            ],
            "request_weight_scale_when": (
                "a performance permitiria avaliar subida, mas a escala de pesos do exercício ainda não está preenchida"
            ),
            "decrease_or_stop_when": [
                "falha abaixo do mínimo de reps",
                "RIR 0",
                "queda de reps >= 30-35% face à melhor série do dia",
                "duas séries consecutivas abaixo do mínimo de reps",
                "dor, tontura, desconforto articular ou técnica má",
            ],
            "failure_classification": {
                "productive_failure": "falha no topo da faixa, sem dor, técnica boa e poucas séries feitas; continuar sem subir carga",
                "acceptable_failure": "falha dentro da faixa; continuar com cautela, mantendo ou fazendo pequeno backoff",
                "bad_failure": "falha abaixo do mínimo ou queda grande; baixar carga ou parar",
                "danger_failure": "dor, técnica má, tontura ou desconforto articular; parar exercício",
            },
            "must_not_stop_when": [
                "existem menos de 3 séries de trabalho válidas e não há risco de segurança",
                "reached_failure=true mas reps_completed >= target_max_reps",
                "falha no topo da faixa sem dor e ainda há séries úteis planeadas",
            ],
            "minimum_valid_working_sets": (
                "antes de 3 séries de trabalho válidas, adaptar peso para recuperar volume; "
                "não terminar salvo dor, tontura, risco técnico, execução perigosa ou pedido explícito do atleta"
            ),
            "extra_set_requires": "plano cumprido, todas as séries fortes, RIR alto, sem falha e histórico sem excesso de fadiga",
            "must_return_json": True,
            "exercise_state_values": sorted(ALLOWED_EXERCISE_STATES),
            "must_respect_complete_exercise_guardrail": (
                local_decision.get("exercise_status") == "complete"
            ),
            "block_increase": local_decision.get("guardrails", {}).get("block_increase", False),
            "must_stop": local_decision.get("guardrails", {}).get("must_stop", False),
            "ai_must_stay_within_permissions": ai_permissions,
            "safety_constraints": safety_constraints,
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
            "feedback manda. Séries de aquecimento não usam RIR nem falha; assume que a carga é levantável e decide "
            "aquecimento apenas por progressão de carga, técnica, histórico e distância até à primeira série normal. "
            "Regra central: antes de 3 séries de trabalho válidas, não termines o exercício salvo dor articular, tontura, "
            "risco técnico, execução perigosa, desconforto anormal ou pedido explícito para parar; se a carga falhar cedo, ajusta peso. "
            "Para séries normais, o objetivo é 12 reps consistentes com RIR controlado. Só podes subir carga quando "
            "existem 12 reps, RIR >= 3, sem falha, sem dor, técnica boa e próximo peso disponível na escala registada do exercício; se o "
            "salto for superior a 10%, exige RIR >= 4. 12 reps com RIR 1-2 mantém carga. Falha não significa parar: "
            "classifica a falha. Falha no topo da faixa, por exemplo 12 reps e falha na 12ª, é produtiva/aceitável: "
            "não subas carga e não termines automaticamente; mantém ou faz pequeno backoff. Só termina se a falha "
            "aconteceu abaixo do mínimo de reps, se há queda de reps >= 30-35%, dor, tontura, desconforto articular, "
            "técnica má ou fadiga acumulada que torne a próxima série improdutiva. Se a performance permitiria avaliar "
            "subida mas a escala do exercício ainda não está preenchida, mantém a carga e pede ao atleta para "
            "preencher placas e bolachas no menu Escala antes de decidir subir. Séries extra só quando o plano foi "
            "cumprido com margem clara e o histórico não mostra excesso de fadiga. "
            "Só podes escolher uma ação da lista permitida. Não dês aconselhamento médico. "
            "Devolve apenas JSON válido com estas chaves: recommended_weight, target_reps, recommended_rest_seconds, "
            "target_rir, add_set, stop_exercise, do_backoff_set, backoff_weight, fatigue_score, local_fatigue_score, "
            "global_fatigue_score, stimulus_score, fatigue_cost, recovery_score, readiness_score, valid_working_sets, "
            "minimum_valid_sets, next_set_type, exercise_status, exercise_state, action, reason, guidance_title, "
            "guidance_message, confidence, confidence_score, decision_basis."
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
                    "sobre progressão. Séries de aquecimento não usam RIR nem falha; assume que a carga é levantável "
                    "e decide aquecimento apenas por progressão de carga, técnica, histórico e distância até à primeira "
                    "série normal. Antes de 3 séries de trabalho válidas, não termines salvo dor, tontura, risco técnico, execução perigosa, "
                    "desconforto anormal ou pedido explícito para parar; falhar cedo significa ajustar carga. Para séries normais, sobe carga apenas com 12 reps, RIR >= 3, sem falha, sem dor, "
                    "técnica boa e próximo peso disponível na escala registada do exercício; saltos acima de 10% exigem RIR >= 4. 12 reps com RIR 1-2 "
                    "mantém carga. Falha não significa parar: falha no topo da faixa é produtiva/aceitável e deve continuar sem subir carga; "
                    "só termina com falha abaixo do mínimo de reps, queda de reps >= 30-35%, dor, tontura, desconforto articular, técnica má ou fadiga improdutiva. "
                    "Se a performance permitiria avaliar subida mas falta escala, mantém carga e pede ao atleta para preencher o menu Escala. "
                    "Séries extra exigem plano cumprido com margem clara e histórico sem fadiga excessiva. Só podes escolher uma ação da lista permitida. "
                    "Responde só com JSON válido com as chaves: recommended_weight, target_reps, "
                    "target_rir, add_set, stop_exercise, do_backoff_set, backoff_weight, fatigue_score, local_fatigue_score, "
                    "global_fatigue_score, stimulus_score, fatigue_cost, recovery_score, readiness_score, valid_working_sets, "
                    "minimum_valid_sets, recommended_rest_seconds, next_set_type, exercise_status, exercise_state, "
                    "action, reason, guidance_title, guidance_message, confidence, confidence_score, decision_basis."
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


def _normalize_ai_decision(ai_decision, local_decision, request_context, model, source):
    if not isinstance(ai_decision, dict):
        return _with_decision_envelope(
            local_decision,
            local_decision,
            request_context,
            ai_decision=None,
            validation_status="ai_invalid_fallback_to_local",
            validation_reasons=["A resposta da IA não tinha formato de objeto."],
        )

    next_set_type = ai_decision.get("next_set_type") or local_decision.get("next_set_type")
    exercise_status = ai_decision.get("exercise_status") or local_decision.get("exercise_status", "continue")
    exercise_state = ai_decision.get("exercise_state") or local_decision.get("exercise_state", "CONTINUE")
    action = ai_decision.get("action") or local_decision.get("action")
    guardrails = local_decision.get("guardrails", {})

    if next_set_type not in ALLOWED_NEXT_SET_TYPES:
        next_set_type = local_decision.get("next_set_type", "WORKING")

    if exercise_status not in ALLOWED_EXERCISE_STATUS:
        exercise_status = local_decision.get("exercise_status", "continue")

    if exercise_state not in ALLOWED_EXERCISE_STATES:
        exercise_state = local_decision.get("exercise_state", "CONTINUE")

    if action not in ALLOWED_ACTIONS:
        action = local_decision.get("action", "maintain_weight")
        if action not in ALLOWED_ACTIONS:
            action = "maintain_weight"

    # Safety guardrail: when the local engine decides the exercise should stop,
    # the LLM may explain it, but it cannot force more volume.
    if local_decision.get("exercise_status") == "complete" or guardrails.get("must_stop"):
        next_set_type = "COMPLETE"
        exercise_status = "complete"
        exercise_state = local_decision.get("exercise_state", "SAFETY_STOP" if guardrails.get("must_stop") else "END_EXERCISE")
        action = local_decision.get("action", "stop_exercise")

    recommended_weight = ai_decision.get("recommended_weight", local_decision.get("recommended_weight"))
    target_reps = ai_decision.get("target_reps", local_decision.get("target_reps"))
    guardrail_applied = False
    guardrail_reason = ""
    validation_reasons = []
    local_weight = _number_or_none(local_decision.get("recommended_weight"))
    ai_weight = _number_or_none(recommended_weight)
    local_context = local_decision.get("context", {})
    failure_class = local_context.get("failure_class")
    working_set_count = local_context.get("working_set_count", 0)
    planned_sets = local_context.get("planned_sets", request_context.get("total_sets") or 3)

    if (
        local_decision.get("next_set_type") == "WARMUP"
        and next_set_type == "WORKING"
        and (ai_weight is None or local_weight is None or ai_weight <= local_weight)
    ):
        next_set_type = "WARMUP"
        exercise_status = "continue"
        exercise_state = local_decision.get("exercise_state", "CONTINUE")
        recommended_weight = local_decision.get("recommended_weight")
        target_reps = local_decision.get("target_reps")
        guardrail_applied = True
        guardrail_reason = "A IA tentou transformar uma carga de aquecimento em série de trabalho."
        validation_reasons.append(guardrail_reason)

    if guardrails.get("block_increase") and (action == "increase_weight" or (ai_weight is not None and local_weight is not None and ai_weight > local_weight)):
        next_set_type = local_decision.get("next_set_type", "WORKING")
        exercise_status = local_decision.get("exercise_status", "continue")
        exercise_state = local_decision.get("exercise_state", "CONTINUE")
        recommended_weight = local_decision.get("recommended_weight")
        target_reps = local_decision.get("target_reps")
        action = local_decision.get("action", "maintain_weight")
        guardrail_applied = True
        guardrail_reason = "A IA tentou subir carga apesar de um bloqueio de segurança, fadiga ou feedback do utilizador."
        validation_reasons.append(guardrail_reason)

    local_action_allows_load_increase = local_decision.get("action") in {"increase_weight", "increase_volume"}
    ai_attempted_load_increase = action in {"increase_weight", "increase_volume"} or (
        ai_weight is not None
        and local_weight is not None
        and ai_weight > local_weight
    )

    if ai_attempted_load_increase and not local_action_allows_load_increase:
        next_set_type = local_decision.get("next_set_type", "WORKING")
        exercise_status = local_decision.get("exercise_status", "continue")
        exercise_state = local_decision.get("exercise_state", "CONTINUE")
        recommended_weight = local_decision.get("recommended_weight")
        target_reps = local_decision.get("target_reps")
        action = local_decision.get("action", "maintain_weight")
        guardrail_applied = True
        guardrail_reason = "A IA tentou subir carga sem cumprir as regras de 12 reps, RIR e escala disponível."
        validation_reasons.append(guardrail_reason)

    if (
        exercise_status == "complete"
        and failure_class in {"productive_failure", "acceptable_failure"}
        and working_set_count < planned_sets
    ):
        next_set_type = local_decision.get("next_set_type", "WORKING")
        exercise_status = "continue"
        exercise_state = local_decision.get("exercise_state", "CONTINUE")
        recommended_weight = local_decision.get("recommended_weight")
        target_reps = local_decision.get("target_reps")
        action = local_decision.get("action", "maintain_or_small_backoff")
        guardrail_applied = True
        guardrail_reason = "A IA tentou terminar o exercício apesar de a falha ter sido produtiva ou aceitável."
        validation_reasons.append(guardrail_reason)

    if next_set_type == "COMPLETE" or exercise_status == "complete":
        recommended_weight = ""
        target_reps = ""
    elif _number_or_none(recommended_weight) is None:
        recommended_weight = local_decision.get("recommended_weight")
    else:
        exercise_context = request_context.get("exercise_context", {})
        if get_exercise_weight_scale(exercise_context)["configured"]:
            recommended_weight = snap_to_available_weight(
                recommended_weight,
                exercise_context,
            )

    reason = ai_decision.get("reason") or local_decision.get("reason")
    guidance_title = ai_decision.get("guidance_title") or local_decision.get("guidance_title")
    guidance_message = ai_decision.get("guidance_message") or local_decision.get("guidance_message")

    if guardrail_applied:
        action = local_decision.get("action")
        exercise_state = local_decision.get("exercise_state", exercise_state)
        if action not in ALLOWED_ACTIONS:
            action = "maintain_weight"
        reason = local_decision.get("reason")
        guidance_title = local_decision.get("guidance_title")
        guidance_message = local_decision.get("guidance_message")

    final_decision = {
        **local_decision,
        "exercise_state": exercise_state,
        "recommended_weight": recommended_weight,
        "target_reps": target_reps,
        "target_reps_label": local_decision.get("target_reps_label"),
        "target_rir": _int_or_default(ai_decision.get("target_rir", local_decision.get("target_rir", 2)), 2),
        "add_set": bool(ai_decision.get("add_set", local_decision.get("add_set", False))) and exercise_status != "complete",
        "stop_exercise": bool(ai_decision.get("stop_exercise", local_decision.get("stop_exercise", False))) or exercise_status == "complete",
        "do_backoff_set": bool(ai_decision.get("do_backoff_set", local_decision.get("do_backoff_set", False))) and exercise_status != "complete",
        "backoff_weight": ai_decision.get("backoff_weight", local_decision.get("backoff_weight")),
        "fatigue_score": _int_or_default(ai_decision.get("fatigue_score", local_decision.get("fatigue_score", 0)), 0),
        "local_fatigue_score": _int_or_default(ai_decision.get("local_fatigue_score", local_decision.get("local_fatigue_score", local_decision.get("fatigue_score", 0))), 0),
        "global_fatigue_score": _int_or_default(ai_decision.get("global_fatigue_score", local_decision.get("global_fatigue_score", 0)), 0),
        "stimulus_score": _int_or_default(ai_decision.get("stimulus_score", local_decision.get("stimulus_score", 0)), 0),
        "fatigue_cost": _int_or_default(ai_decision.get("fatigue_cost", local_decision.get("fatigue_cost", 0)), 0),
        "recovery_score": _int_or_default(ai_decision.get("recovery_score", local_decision.get("recovery_score", 0)), 0),
        "readiness_score": _int_or_default(ai_decision.get("readiness_score", local_decision.get("readiness_score", 0)), 0),
        "valid_working_sets": _int_or_default(ai_decision.get("valid_working_sets", local_decision.get("valid_working_sets", 0)), 0),
        "minimum_valid_sets": _int_or_default(ai_decision.get("minimum_valid_sets", local_decision.get("minimum_valid_sets", 3)), 3),
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
        "confidence_score": float(ai_decision.get("confidence_score") or local_decision.get("confidence_score", 0.5)),
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

    return _with_decision_envelope(
        final_decision,
        local_decision,
        request_context,
        ai_decision=ai_decision,
        validation_status="guardrail_adjusted" if guardrail_applied else "ai_adjustment_accepted",
        validation_reasons=validation_reasons,
    )


def generate_ai_training_decision(local_decision, request_context):
    provider = getattr(settings, "AI_TRAINING_DECISION_PROVIDER", "local")
    provider = provider if provider in SUPPORTED_PROVIDERS else "local"
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    model = getattr(settings, "AI_TRAINING_DECISION_MODEL", getattr(settings, "AI_COACH_MODEL", "gpt-5.5"))

    if provider == "local":
        final_decision = {
            **local_decision,
            "llm_status": "llm_disabled",
            "llm_provider": "local",
            "model": None,
        }

        return _with_decision_envelope(
            final_decision,
            local_decision,
            request_context,
            validation_status="local_only",
            validation_reasons=["Provider configurado como local."],
        )

    context = _build_llm_context(local_decision, request_context)

    if provider == "ollama":
        ollama_model = getattr(settings, "OLLAMA_TRAINING_DECISION_MODEL", "qwen3:8b")
        base_url = getattr(settings, "OLLAMA_BASE_URL", "http://127.0.0.1:11434")

        try:
            ai_decision = _request_ollama_training_decision(context, base_url, ollama_model)
        except urllib.error.HTTPError as error:
            final_decision = {
                **local_decision,
                "llm_status": "llm_error",
                "llm_provider": "ollama",
                "llm_error_type": "http_error",
                "llm_error_detail": f"Ollama HTTP {error.code}",
                "model": ollama_model,
            }
            return _with_decision_envelope(
                final_decision,
                local_decision,
                request_context,
                validation_status="ai_error_fallback_to_local",
                validation_reasons=[final_decision["llm_error_detail"]],
            )
        except json.JSONDecodeError:
            final_decision = {
                **local_decision,
                "llm_status": "llm_error",
                "llm_provider": "ollama",
                "llm_error_type": "json_decode_error",
                "llm_error_detail": "Ollama response was not valid JSON",
                "model": ollama_model,
            }
            return _with_decision_envelope(
                final_decision,
                local_decision,
                request_context,
                validation_status="ai_error_fallback_to_local",
                validation_reasons=[final_decision["llm_error_detail"]],
            )
        except (TimeoutError, socket.timeout, urllib.error.URLError):
            final_decision = {
                **local_decision,
                "llm_status": "llm_error",
                "llm_provider": "ollama",
                "llm_error_type": "request_error",
                "llm_error_detail": "Ollama request failed",
                "model": ollama_model,
            }
            return _with_decision_envelope(
                final_decision,
                local_decision,
                request_context,
                validation_status="ai_error_fallback_to_local",
                validation_reasons=[final_decision["llm_error_detail"]],
            )

        return _normalize_ai_decision(ai_decision, local_decision, request_context, ollama_model, "ollama_training_decision")

    if not api_key:
        final_decision = {
            **local_decision,
            "llm_status": "llm_disabled",
            "llm_provider": "openai",
            "model": None,
        }
        return _with_decision_envelope(
            final_decision,
            local_decision,
            request_context,
            validation_status="local_only",
            validation_reasons=["OPENAI_API_KEY não configurada."],
        )

    try:
        ai_decision = _request_openai_training_decision(context, api_key, model)
    except urllib.error.HTTPError as error:
        final_decision = {
            **local_decision,
            "llm_status": "llm_error",
            "llm_provider": "openai",
            "llm_error_type": "http_error",
            "llm_error_detail": f"OpenAI HTTP {error.code}",
            "model": model,
        }
        return _with_decision_envelope(
            final_decision,
            local_decision,
            request_context,
            validation_status="ai_error_fallback_to_local",
            validation_reasons=[final_decision["llm_error_detail"]],
        )
    except json.JSONDecodeError:
        final_decision = {
            **local_decision,
            "llm_status": "llm_error",
            "llm_provider": "openai",
            "llm_error_type": "json_decode_error",
            "llm_error_detail": "OpenAI response was not valid JSON",
            "model": model,
        }
        return _with_decision_envelope(
            final_decision,
            local_decision,
            request_context,
            validation_status="ai_error_fallback_to_local",
            validation_reasons=[final_decision["llm_error_detail"]],
        )
    except (TimeoutError, socket.timeout, urllib.error.URLError):
        final_decision = {
            **local_decision,
            "llm_status": "llm_error",
            "llm_provider": "openai",
            "llm_error_type": "request_error",
            "llm_error_detail": "OpenAI request failed",
            "model": model,
        }
        return _with_decision_envelope(
            final_decision,
            local_decision,
            request_context,
            validation_status="ai_error_fallback_to_local",
            validation_reasons=[final_decision["llm_error_detail"]],
        )

    return _normalize_ai_decision(ai_decision, local_decision, request_context, model, "openai_training_decision")
