# Feedback Pós-Treino Por Exercício

## Nome

`post_workout_exercise_feedback`

## Objetivo

Dar ao atleta uma leitura clara e motivadora do que aconteceu em cada exercício quando finaliza o treino, incluindo treino experimental. A app deve explicar desempenho, estado do exercício e próximo passo, sem depender apenas de uma frase geral do coach.

## Fluxo Esperado

1. O atleta finaliza o treino.
2. O backend recolhe séries normais, séries de calibração, progressão e notas.
3. O motor local cria feedback estruturado por exercício.
4. O feedback fica guardado na `WorkoutSession`.
5. A IA externa, quando disponível, pode melhorar o texto sem alterar métricas e estados calculados localmente.
6. O frontend mostra cartões por exercício com estado, métricas e próximo passo.
7. O dashboard/histórico conseguem recuperar o resumo do coach depois de sair do ecrã.

## Dados Necessários

- Entrada do utilizador: séries, carga, reps, RIR/falha, notas e calibração.
- Histórico usado: progressão calculada para o próximo treino.
- Dados obrigatórios: treino/sessão e exercícios envolvidos.
- Dados opcionais: notas da sessão e resposta de IA externa.

## Regras Fixas

- Métricas e estado do exercício vêm do backend local.
- IA pode reescrever texto, mas não deve alterar métricas nem estado.
- Treino experimental deve gerar feedback útil mesmo sem séries normais.
- O próximo passo deve respeitar a recomendação de progressão já calculada.

## Papel Da IA

- O que a IA pode ajustar: tom, explicação e linguagem motivacional.
- O que a IA não pode alterar: volume, número de séries, falhas, RIR médio, estado e recomendação estrutural.
- Guardrails obrigatórios: não inventar histórico, não recomendar fora da escala e não ignorar sinais de recuperação.

## Backend

- Modelo: `WorkoutSession.coach_feedback`
- Serviço: `backend/recommendations/services/ai_coach_engine.py`
- Endpoint: `POST /api/training/finish-session/`
- Testes: `backend/recommendations/tests.py`

## Frontend

- Componente: `frontend/src/components/AiCoachSummaryPanel.jsx`
- Estilos: `frontend/src/index.css`
- Dados: `latestAiCoach.exercise_feedback`

## Critérios De Aceitação

- [x] Funciona com treino experimental/calibração.
- [x] Funciona com séries normais.
- [x] Mostra estado por exercício.
- [x] Mostra métricas por exercício.
- [x] Mostra próximo passo.
- [x] Guarda feedback na sessão.
- [x] Expõe feedback no histórico de sessões e no dashboard.
- [x] Não usa `alert()`.
- [x] `./scripts/check.sh` passa.
