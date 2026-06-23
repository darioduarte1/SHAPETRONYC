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


def calculate_training_coach_decision(
    weight,
    reps,
    rir=None,
    is_failure=False,
    notes="",
    set_type="WORKING",
):
    if set_type == "WARMUP":
        return {
            "recommended_weight": "",
            "target_reps": TARGET_REPS,
            "recommended_rest_seconds": 90,
            "next_set_type": "WORKING",
            "action": "prepare_working_set",
            "reason": "Aquecimento registado. A próxima decisão deve aproximar o user da série normal.",
            "guidance_title": "Prepara a primeira série normal",
            "guidance_message": "Usa o aquecimento como referência técnica, não como progressão de carga.",
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
            "source": "training_coach_engine",
        }

    if reps < TARGET_REPS:
        return {
            "recommended_weight": max(weight - WEIGHT_STEP, 0),
            "target_reps": TARGET_REPS,
            "recommended_rest_seconds": 150,
            "next_set_type": "WORKING",
            "action": "reduce_load",
            "reason": "Não chegaste às 12 reps. Assumimos falha e reduzimos a carga para voltar ao alvo.",
            "guidance_title": "Reduz a carga na próxima série",
            "guidance_message": "O objectivo continua a ser completar 12 reps com execução limpa.",
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
            "source": "training_coach_engine",
        }

    if not is_failure and rir is not None and rir >= 2:
        return {
            "recommended_weight": weight + WEIGHT_STEP,
            "target_reps": TARGET_REPS,
            "recommended_rest_seconds": 120,
            "next_set_type": "WORKING",
            "action": "increase_load",
            "reason": "Fizeste 12 reps com margem. Aumentamos a carga na próxima série.",
            "guidance_title": "Sobe a carga",
            "guidance_message": "Mantém o alvo nas 12 reps e confirma se a nova carga ainda fica controlada.",
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
        "source": "training_coach_engine",
    }
