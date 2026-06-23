TARGET_REPS = 12
WEIGHT_STEP = 2.5

NEGATIVE_FEEDBACK_KEYWORDS = [
    "cansado",
    "cansaço",
    "sem energia",
    "dormi mal",
    "dor",
    "dores",
    "desmotivado",
    "quero desistir",
    "não quero subir",
    "muito pesado",
]


def has_negative_feedback(notes):
    normalized_notes = notes.lower().strip()

    return any(keyword in normalized_notes for keyword in NEGATIVE_FEEDBACK_KEYWORDS)


def number_or_none(value):
    if value in ("", None):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_working_set(set_log):
    return set_log.get("set_type", "WORKING") == "WORKING"


def set_reached_failure(set_log):
    reps = number_or_none(set_log.get("reps_completed"))

    return bool(set_log.get("reached_failure")) or reps is not None and reps < TARGET_REPS


def set_has_reserve(set_log):
    rir = number_or_none(set_log.get("rir"))
    reps = number_or_none(set_log.get("reps_completed"))

    return reps is not None and reps >= TARGET_REPS and rir is not None and rir >= 2


def build_exercise_context(current_sets):
    working_sets = [set_log for set_log in current_sets if is_working_set(set_log)]
    consecutive_working_misses = 0

    for set_log in reversed(working_sets):
        if set_reached_failure(set_log):
            consecutive_working_misses += 1
        else:
            break

    return {
        "completed_set_count": len(current_sets),
        "working_set_count": len(working_sets),
        "consecutive_working_misses": consecutive_working_misses,
        "previous_working_set": working_sets[-2] if len(working_sets) >= 2 else None,
        "last_two_working_sets": working_sets[-2:],
    }


def calculate_training_coach_decision(
    weight,
    reps,
    rir=None,
    is_failure=False,
    notes="",
    set_type="WORKING",
    set_number=None,
    total_sets=None,
    current_sets=None,
    previous_sets=None,
):
    current_sets = current_sets or []
    previous_sets = previous_sets or []
    context = build_exercise_context(current_sets)

    if set_type == "WARMUP":
        completed_warmups = len([set_log for set_log in current_sets if set_log.get("set_type") == "WARMUP"])
        guidance_message = (
            "Aquecimento registado. Se a técnica está estável, aproxima-te da primeira série normal."
            if completed_warmups <= 1
            else "Aquecimentos registados. Mantém só o necessário antes de começares as séries normais."
        )

        return {
            "recommended_weight": "",
            "target_reps": TARGET_REPS,
            "recommended_rest_seconds": 90,
            "next_set_type": "WORKING",
            "action": "prepare_working_set",
            "reason": "Aquecimento registado. A próxima decisão deve aproximar o user da série normal.",
            "guidance_title": "Prepara a primeira série normal",
            "guidance_message": guidance_message,
            "context": {
                "completed_set_count": context["completed_set_count"],
                "working_set_count": context["working_set_count"],
                "previous_history_count": len(previous_sets),
            },
            "source": "training_coach_engine",
        }

    if set_type == "DROP":
        return {
            "recommended_weight": weight,
            "target_reps": TARGET_REPS,
            "recommended_rest_seconds": 120,
            "next_set_type": "WORKING",
            "action": "recover_after_drop",
            "reason": "Drop set registada. Mantemos a carga de referência e priorizamos recuperação.",
            "guidance_title": "Recupera depois da drop set",
            "guidance_message": "A próxima decisão deve proteger execução e fadiga acumulada.",
            "context": {
                "completed_set_count": context["completed_set_count"],
                "working_set_count": context["working_set_count"],
                "previous_history_count": len(previous_sets),
            },
            "source": "training_coach_engine",
        }

    if reps < TARGET_REPS:
        if context["consecutive_working_misses"] >= 2:
            return {
                "recommended_weight": max(weight - WEIGHT_STEP * 2, 0),
                "target_reps": TARGET_REPS,
                "recommended_rest_seconds": 180,
                "next_set_type": "WORKING",
                "action": "reduce_load_for_fatigue",
                "reason": "Duas séries de trabalho seguidas ficaram abaixo das 12 reps. Reduzimos mais a carga e damos mais descanso.",
                "guidance_title": "Baixa a carga e recupera",
                "guidance_message": "O padrão do exercício mostra fadiga acumulada. A próxima série deve voltar a 12 reps limpas.",
                "context": {
                    "completed_set_count": context["completed_set_count"],
                    "working_set_count": context["working_set_count"],
                    "consecutive_working_misses": context["consecutive_working_misses"],
                    "previous_history_count": len(previous_sets),
                },
                "source": "training_coach_engine",
            }

        return {
            "recommended_weight": max(weight - WEIGHT_STEP, 0),
            "target_reps": TARGET_REPS,
            "recommended_rest_seconds": 150,
            "next_set_type": "WORKING",
            "action": "reduce_load",
            "reason": "Não chegaste às 12 reps. Assumimos falha e reduzimos a carga para voltar ao alvo.",
            "guidance_title": "Reduz a carga na próxima série",
            "guidance_message": "O objectivo continua a ser completar 12 reps com execução limpa.",
            "context": {
                "completed_set_count": context["completed_set_count"],
                "working_set_count": context["working_set_count"],
                "consecutive_working_misses": context["consecutive_working_misses"],
                "previous_history_count": len(previous_sets),
            },
            "source": "training_coach_engine",
        }

    if has_negative_feedback(notes):
        return {
            "recommended_weight": weight,
            "target_reps": TARGET_REPS,
            "recommended_rest_seconds": 150,
            "next_set_type": "WORKING",
            "action": "maintain",
            "reason": (
                "Apesar da performance permitir progressão, o feedback indica fadiga, desconforto ou baixa disponibilidade. "
                "Mantemos a carga para proteger performance e aderência ao treino."
            ),
            "guidance_title": "Mantém a carga",
            "guidance_message": "A prioridade agora é repetir 12 reps com controlo e boa sensação.",
            "context": {
                "completed_set_count": context["completed_set_count"],
                "working_set_count": context["working_set_count"],
                "previous_history_count": len(previous_sets),
            },
            "source": "training_coach_engine",
        }

    previous_working_set = context["previous_working_set"]

    if previous_working_set and set_reached_failure(previous_working_set) and rir is not None and rir >= 2:
        return {
            "recommended_weight": weight,
            "target_reps": TARGET_REPS,
            "recommended_rest_seconds": 150,
            "next_set_type": "WORKING",
            "action": "stabilize_after_miss",
            "reason": "A série anterior deste exercício falhou o alvo. Apesar da melhoria agora, mantemos a carga para estabilizar.",
            "guidance_title": "Estabiliza a carga",
            "guidance_message": "Repete 12 reps com a mesma carga antes de subires peso.",
            "context": {
                "completed_set_count": context["completed_set_count"],
                "working_set_count": context["working_set_count"],
                "previous_history_count": len(previous_sets),
            },
            "source": "training_coach_engine",
        }

    if not is_failure and rir is not None and rir >= 2:
        last_two_have_reserve = (
            len(context["last_two_working_sets"]) == 2
            and all(set_has_reserve(set_log) for set_log in context["last_two_working_sets"])
        )

        return {
            "recommended_weight": weight + WEIGHT_STEP,
            "target_reps": TARGET_REPS,
            "recommended_rest_seconds": 120,
            "next_set_type": "WORKING",
            "action": "increase_load",
            "reason": "Fizeste 12 reps com margem. Aumentamos a carga na próxima série.",
            "guidance_title": "Sobe a carga",
            "guidance_message": (
                "Duas séries recentes ficaram nas 12 reps com margem. A subida de carga está bem sustentada."
                if last_two_have_reserve
                else "Mantém o alvo nas 12 reps e confirma se a nova carga ainda fica controlada."
            ),
            "context": {
                "completed_set_count": context["completed_set_count"],
                "working_set_count": context["working_set_count"],
                "previous_history_count": len(previous_sets),
            },
            "source": "training_coach_engine",
        }

    return {
        "recommended_weight": weight,
        "target_reps": TARGET_REPS,
        "recommended_rest_seconds": 120,
        "next_set_type": "WORKING",
        "action": "maintain",
        "reason": "Chegaste às 12 reps, mas sem margem clara. Mantemos a carga.",
        "guidance_title": "Repete a carga",
        "guidance_message": "Procura completar novamente 12 reps antes de subir peso.",
        "context": {
            "completed_set_count": context["completed_set_count"],
            "working_set_count": context["working_set_count"],
            "previous_history_count": len(previous_sets),
        },
        "source": "training_coach_engine",
    }
