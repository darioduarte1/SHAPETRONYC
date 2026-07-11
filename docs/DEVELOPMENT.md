# Guia de Desenvolvimento

Este documento existe para tornar a evolução da SHAPETRONYC mais previsível. A app já tem muitas peças ligadas entre si: perfil, programa, treino ativo, calibração, escala da máquina, histórico, regras e IA. Antes de implementar uma feature, usa este guia para decidir onde mexer e como validar.

## Princípio Central

A app deve evoluir com esta divisão:

- Regras definem limites seguros e consistentes.
- IA ajusta dentro desses limites.
- Backend guarda a verdade dos dados.
- Frontend mostra o próximo passo com clareza e bloqueia ações perigosas.
- Testes protegem o comportamento já decidido.

## Mapa Do Projeto

### Backend

- `accounts`: utilizadores, perfis e exportação/limpeza de dados.
- `exercises`: biblioteca de exercícios e escala base das máquinas.
- `programs`: geração inicial de programas.
- `progression`: logs de séries e histórico por exercício.
- `recommendations`: motor de próxima série, regras de treino, IA e decisões híbridas.
- `training`: sessões, dashboard, memória, calibração, escalas por atleta/exercício, blocos e feedback semanal.

### Frontend

- `src/api`: chamadas ao backend.
- `src/hooks`: lógica de estado e ações da app.
- `src/components`: apresentação visual.
- `src/utils`: constantes, formatação e configuração.
- `src/App.jsx`: orquestração principal entre hooks e ecrãs.

## Como Implementar Uma Feature

### 1. Definir O Contrato

Antes de mexer no código, escreve a resposta desejada da app:

- Que problema do atleta resolve?
- Que dados precisa?
- Que dados guarda?
- Que decisão deve aparecer no ecrã?
- Que situações devem bloquear a ação?
- Que parte é regra fixa?
- Que parte pode ser ajustada pela IA?

Para features com IA, define sempre um envelope de decisão:

```json
{
  "action": "maintain_load",
  "recommendation": "36.6kg x 12 reps",
  "confidence": "medium",
  "reason": "A serie anterior ficou dentro do objetivo.",
  "guardrails": ["machine_scale_respected", "target_reps_respected"],
  "debug": {
    "rules": {},
    "ai": {}
  }
}
```

### 2. Backend Primeiro

Usa esta ordem:

1. Modelo, se for preciso guardar dados novos.
2. Migration.
3. Serviço em `services/`.
4. Serializer.
5. View/endpoint.
6. Testes.

Evita colocar regra complexa diretamente em `views.py`. Views recebem pedido, validam entrada simples e chamam serviços.

### 3. Frontend Depois

Usa esta ordem:

1. Função de API em `src/api`.
2. Hook em `src/hooks` para estado e ações.
3. Componente em `src/components`.
4. Ligação em `App.jsx` ou no componente de ecrã certo.
5. Mensagens internas com `useAppMessages`, nunca `alert()`.

O frontend deve bloquear ações quando os dados obrigatórios ainda não existem. Exemplo: calibração sem escala da máquina.

### 4. Regras Do Motor De Treino

Quando a feature mexe com treino, respeita estes limites:

- Pesos recomendados têm de existir na escala real da máquina.
- A primeira série normal vem do histórico/calibração anterior.
- Séries seguintes dependem do desempenho atual e do histórico.
- Falha não significa parar automaticamente.
- Falha abaixo do objetivo, dor, técnica má ou queda forte podem parar.
- Aquecimento não deve apagar nem recalcular a série 1 baseada no histórico.
- Desfazer uma série deve apagar decisões dependentes dessa série.

### 5. IA Dentro Das Regras

A IA pode:

- escolher entre manter, subir, baixar, backoff ou terminar;
- explicar a decisão de forma humana;
- adaptar a recomendação ao contexto do atleta;
- analisar padrões recentes.

A IA não pode:

- recomendar peso fora da escala da máquina;
- ignorar bloqueios de segurança;
- inventar histórico que não existe;
- desbloquear treino normal sem calibração obrigatória;
- transformar aquecimento em série normal.

## Checklist Antes De Commit

Corre sempre:

```bash
./scripts/check.sh
```

Este comando valida:

- lint do frontend;
- build do frontend;
- configuração Django;
- migrations em falta;
- testes principais do backend.

## Checklist De Feature

Antes de considerar uma feature pronta:

- O dado tem dono claro no backend.
- O frontend não duplica regra crítica do backend sem necessidade.
- Estados vazios estão tratados.
- Erros aparecem por mensagem interna da app.
- A escala da máquina é respeitada quando há pesos.
- Existe teste para a regra principal.
- README ou docs foram atualizados se o fluxo mudou.
- `./scripts/check.sh` passa.

## Onde Colocar Novas Coisas

### Nova decisão de treino

- Backend: `backend/recommendations/services/`
- Testes: `backend/recommendations/tests.py`
- Frontend: `useSetLogging`, `useExerciseGuidance`, `ExerciseGuidanceCard`

### Novo dado do atleta

- Backend: `accounts` se for perfil base.
- Backend: `training` se for memória, sessão, feedback ou calibração.
- Frontend: `useProfileAccess`, `useProgramData` ou hook específico.

### Nova visualização analítica

- Backend: serviço em `training/services/`.
- Frontend: componente próprio em `src/components`.
- API: `frontend/src/api/trainingApi.js`.

### Nova ação durante treino

- Backend: normalmente `progression` ou `recommendations`.
- Frontend: `useSetLogging`, `useSetControls`, `ExerciseSetTable`.

## Decisão Sobre Regras Vs IA

Usa esta pergunta:

> Se a IA falhar ou estiver desligada, a app ainda consegue proteger o atleta?

Se a resposta for não, a lógica tem de ser regra/backend.

Se a resposta for sim, a IA pode melhorar a explicação e ajustar a recomendação dentro dos limites.

