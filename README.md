# SHAPETRONYC

SHAPETRONYC é uma aplicação de treino adaptativo que gera programas, acompanha sessões em tempo real, regista séries e usa o histórico do atleta para recomendar progressões.

O objetivo do projeto é evoluir de um sistema baseado em regras para um coach inteligente com memória de treino, análise de fadiga e recomendações personalizadas.

## Stack

### Backend
- Django
- Django REST Framework
- SQLite em desenvolvimento

### Frontend
- React
- Vite

## Como correr localmente

### Backend

```bash
cd backend
./venv/bin/python manage.py runserver 127.0.0.1:8000
```

Para usar IA local gratuita durante o treino com Ollama:

```bash
ollama pull qwen3:8b
export AI_TRAINING_DECISION_PROVIDER="ollama"
export OLLAMA_TRAINING_DECISION_MODEL="qwen3:8b"
./venv/bin/python manage.py runserver 127.0.0.1:8000
```

O Ollama deve estar aberto em `http://127.0.0.1:11434`.

### Frontend

```bash
cd frontend
npm run dev
```

Para apontar o frontend para uma porta de backend diferente:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8001 npm run dev
```

No browser, usar:

```text
http://localhost:5173/
```

Nota: no browser integrado do Codex, `localhost:5173` funcionou melhor do que `127.0.0.1:5173`.

## Validação

### Backend

```bash
cd backend
./venv/bin/python manage.py test
```

### Frontend

```bash
cd frontend
npm run lint
npm run build
```

Última validação feita:
- Backend: 46 testes a passar
- Frontend: lint a passar
- Frontend: build a passar
- Teste manual no browser integrado concluído com sucesso, incluindo dashboard, histórico por exercício, ramp-up progressivo de aquecimento, memória do atleta, plano adaptativo e decisões adaptativas da Beatriz

## Estado Atual

Implementado:
- Criação de utilizadores
- Perfis de atleta
- Geração automática de programas
- Base de dados de exercícios
- Sessões de treino
- Registo de séries
- Tipos de série: aquecimento, normal e drop
- Histórico por exercício
- Recomendações para a próxima série
- Recomendações iniciais baseadas nos últimos 15 treinos
- Aquecimento calculado a partir da primeira série normal prevista
- Ramp-up progressivo com múltiplos aquecimentos quando a carga e o exercício justificam
- AI Coach série a série com ações fechadas e guardrails
- Scores de fadiga, recuperação e prontidão
- Interpretação de feedback do utilizador durante o treino
- Timer de descanso
- Dropdowns por dia e por exercício
- Bloqueio dos restantes dias durante treino ativo
- Resumo simples da sessão em tempo real
- Memória persistente por atleta/exercício
- Painel de memória do atleta no dashboard
- Plano adaptativo com recomendações por exercício
- Ações adaptativas fechadas: proteger recuperação, aumentar margem, progredir carga e manter plano
- Endpoint de plano adaptativo baseado na memória do atleta, dashboard e programa ativo
- Aplicação controlada de recomendações adaptativas ao plano
- Histórico auditável de decisões adaptativas aplicadas, adiadas e ignoradas
- Feedback semanal com leitura de fadiga, watchlist, RIR recente e tendência de volume
- Sugestão de deload quando há sinais persistentes de recuperação
- Protocolo de deload com volume reduzido, RIR alvo e motivos visíveis
- Blocos de treino com fase atual, volume semanal, RIR médio e recomendação de periodização
- Histórico persistente de blocos de treino por atleta
- Demo visual da Beatriz com 45 treinos completos em `frontend/public/beatriz-evolution-demo.html`
- Recomendações para o próximo treino após terminar uma sessão
- AI Coach pós-treino com fallback local quando não há chave OpenAI
- IA externa opcional para decisões durante o treino com OpenAI ou Ollama
- Demo visual do Sprint 12 em `frontend/public/sprint12-ai-demo.html`

Em preparação:
- Memória longitudinal do atleta para além da janela recente de 15 treinos
- Aplicação controlada do deload ao plano
- Polimento da experiência visual do dashboard e análise semanal

## Fluxo Principal

1. Criar perfil do atleta
2. Gerar programa automático
3. Abrir um dia de treino
4. Iniciar sessão
5. Registar séries por exercício
6. Receber recomendações durante o treino
7. Terminar sessão
8. Ver recomendações para o próximo treino

## Endpoints Principais

### Accounts
- `POST /api/accounts/create-user/`
- `GET /api/accounts/profiles/`
- `POST /api/accounts/profiles/`

### Training
- `POST /api/training/generate-program/`
- `GET /api/training/program/<profile_id>/`
- `GET /api/training/dashboard/<profile_id>/`
- `GET /api/training/adaptive-plan/<profile_id>/`
- `GET /api/training/adaptive-plan/decisions/<profile_id>/`
- `POST /api/training/adaptive-plan/apply/`
- `GET /api/training/weekly-feedback/<profile_id>/`
- `GET /api/training/training-blocks/<profile_id>/`
- `POST /api/training/start-session/`
- `POST /api/training/finish-session/`
- `GET /api/training/sessions/<profile_id>/`

### Progression
- `GET /api/progression/set-logs/`
- `POST /api/progression/set-logs/`
- `GET /api/progression/exercise-history/`

### Recommendations
- `POST /api/recommendations/next-set/`

## Sprints Concluídas

### Sprint 1 - Fundações do Sistema

Objetivo:
Criar a base da aplicação e permitir o registo de utilizadores.

Entregue:
- Projeto Django
- Projeto React com Vite
- Django REST Framework configurado
- App `accounts`
- Modelo `UserProfile`
- Criação de utilizador
- Criação de perfil
- Formulário inicial no frontend
- Ligação frontend/backend

Campos principais do perfil:
- Género
- Idade
- Altura
- Peso
- Objetivo
- Nível
- Experiência de treino
- Dias por semana

### Sprint 2 - Gerador de Programas

Objetivo:
Gerar automaticamente um programa de treino com base no perfil do atleta.

Entregue:
- App `training`
- App `exercises`
- Modelos `TrainingProgram`, `TrainingWorkout` e `TrainingWorkoutExercise`
- Modelo `Exercise`
- Serviço `training/services/training_generator.py`
- Endpoint de geração de programa

Estruturas suportadas:
- Full Body
- Upper / Lower
- Push / Pull / Legs
- Divisões híbridas para frequências diferentes

### Sprint 3 - Visualização do Programa

Objetivo:
Mostrar o programa completo no frontend.

Entregue:
- Renderização dos dias de treino
- Renderização dos exercícios por dia
- Séries planeadas
- Reps alvo
- RIR alvo
- Ordem dos treinos e exercícios

### Sprint 4 - Base de Exercícios

Objetivo:
Criar a base de dados inicial de exercícios.

Entregue:
- Modelo `Exercise`
- Dados de exercícios
- Grupo muscular
- Equipamento
- Dificuldade
- Identificação de exercícios compostos
- Comando de seed para popular exercícios

### Sprint 5 - Registo de Séries e Primeiro Motor de Recomendações

Objetivo:
Guardar o desempenho real do atleta e gerar a primeira recomendação baseada em regras.

Entregue:
- App `progression`
- Modelo `SetLog`
- Registo de peso usado
- Registo de reps concluídas
- Registo de RIR
- Registo de falha
- Notas por série
- Endpoint de criação/listagem de séries
- App `recommendations`
- Endpoint `next-set`
- Primeiro motor de progressão

Entrada do motor:
- Peso
- Reps
- RIR
- Falha
- Observações

Saída do motor:
- Carga recomendada
- Reps alvo
- Motivo da recomendação

### Sprint 6 - Workout Sessions

Objetivo:
Permitir controlar início e fim de uma sessão de treino.

Entregue:
- Modelo `WorkoutSession`
- Estados `IN_PROGRESS`, `COMPLETED` e `CANCELLED`
- Iniciar treino
- Terminar treino
- Histórico de sessões
- Ligação entre `SetLog` e `WorkoutSession`
- Notas finais da sessão

Fluxo:

```text
Workout
↓
WorkoutSession
↓
SetLogs
↓
Finish Workout
```

### Sprint 7 - Hybrid Recommendation Engine

Objetivo:
Preparar o sistema para comportamento de coach, usando performance e feedback qualitativo.

Entregue:
- Interpretação de notas do utilizador
- Deteção simples de fadiga/desconforto
- Simulação de decisão inteligente
- Bloqueio de progressão quando o feedback indica baixa disponibilidade
- Recomendações mais conservadoras quando há sinais negativos

Exemplos de feedback interpretado:
- "Estou cansado"
- "Dormi mal"
- "Sem energia"
- "Muito pesado"
- "Dor"

### Sprint 8 - Workout Day UX

Objetivo:
Melhorar a navegação entre dias de treino.

Entregue:
- Dias de treino em dropdown
- Todos os dias fechados inicialmente
- Apenas um dia aberto de cada vez
- Ao iniciar treino, só o dia ativo fica visível
- Os restantes dias ficam inacessíveis durante a sessão
- Ao terminar treino, todos os dias voltam a aparecer fechados
- Exercícios também organizados em dropdowns

### Sprint 9 - Live Exercise History

Objetivo:
Mostrar histórico por exercício e tornar o registo da sessão mais útil em tempo real.

Entregue:
- Endpoint de histórico por exercício
- Última sessão anterior por exercício
- Séries anteriores visíveis na tabela
- Recomendações iniciais por série
- Registo em tempo real da série atual
- Tipos de série:
  - Aquecimento
  - Normal
  - Drop
- Seleção de esforço ao concluir série:
  - FALHA
  - RIR 0/1
  - RIR 2/3
  - RIR 4+
- Timer de descanso configurável
- Ajuste rápido de descanso
- Remoção de séries ainda não concluídas
- Renumeração automática das séries

### Sprint 10 - Session Summary

Objetivo:
Começar a dar feedback de sessão ao utilizador enquanto o treino está ativo.

Entregue:
- Volume total da sessão em tempo real
- Número de séries concluídas
- Notas finais do treino
- Preparação da resposta de fim de sessão para incluir análise adicional

Ainda pode evoluir:
- Duração total do treino
- Média de RIR
- Número total de falhas
- Número de exercícios concluídos
- Resumo pós-treino mais completo

### Sprint 11 - Workout Progression

Objetivo:
Gerar recomendações para o próximo treino depois de concluir uma sessão.

Entregue:
- Serviço `recommendations/services/workout_progression_engine.py`
- Recomendações por exercício após `Finish Workout`
- Painel "Próximo treino" no frontend
- Subir carga quando as séries normais chegam às 12 reps com margem
- Manter carga quando ainda falta consolidar reps
- Reduzir volume quando há falhas repetidas ou fadiga forte
- Ajustar RIR alvo quando o atleta chega ao alvo mas demasiado perto da falha
- Manter plano quando não há dados suficientes
- Testes do motor de progressão

Exemplo validado no browser:

```text
Chest Press Machine
Subir carga
52.5kg | 3 séries | 12 reps | RIR 2
```

### Sprint 12 - AI Coach

Objetivo:
Transformar o sistema de recomendações num coach de treino em tempo real, capaz de decidir a próxima ação série a série com base no histórico, no desempenho atual, na recuperação e no feedback do atleta.

Entregue:
- Serviço `recommendations/services/ai_coach_engine.py`
- Serviço `recommendations/services/training_coach_engine.py`
- Serviço `recommendations/services/ai_training_decision_engine.py`
- Contexto estruturado da sessão para análise do coach
- Integração opcional com OpenAI Responses API via `OPENAI_API_KEY`
- Integração opcional com Ollama para decisões locais durante o treino
- Fallback local determinístico quando a chave não está configurada
- Resumo "AI Coach" depois de terminar uma sessão
- Métricas pós-treino no painel do coach
- Endpoint `POST /api/recommendations/next-set/` enriquecido com:
  - contexto do utilizador
  - contexto do exercício
  - contexto da sessão
  - séries anteriores
  - séries atuais
  - histórico recente
- Motor local com ações fechadas:
  - manter carga
  - subir carga
  - descer carga
  - repetir
  - fazer mais um aquecimento
  - avançar para séries normais
  - fazer drop set
  - parar exercício
- Guardrails para impedir subidas perigosas, progressão a partir de aquecimento e decisões incoerentes com dor/fadiga
- Scores de fadiga, recuperação e prontidão
- Recomendações iniciais por exercício com base nos últimos 15 treinos
- Cálculo automático de aquecimento proporcional à primeira série normal prevista
- Correção do alinhamento visual do histórico: a linha `W` mostra apenas aquecimentos anteriores e a série `1` mostra a primeira série normal anterior
- Página demo `sprint12-ai-demo.html` para visualizar o 16.º treino depois de 15 treinos históricos
- Testes do motor local, fallback local, guardrails e histórico

Configuração opcional:

```bash
export OPENAI_API_KEY="..."
export AI_COACH_MODEL="gpt-5.5"
export AI_TRAINING_DECISION_PROVIDER="openai"
export AI_TRAINING_DECISION_MODEL="gpt-5.5"
```

Configuração opcional com Ollama:

```bash
ollama pull qwen3:8b
export AI_TRAINING_DECISION_PROVIDER="ollama"
export OLLAMA_TRAINING_DECISION_MODEL="qwen3:8b"
```

Sem `OPENAI_API_KEY` e sem Ollama, o sistema continua funcional e mostra decisões locais determinísticas.

Exemplo validado no browser integrado:

```text
Histórico: 15 treinos anteriores
Treino atual: 16.º treino
Linha W: anterior "-" | recomendado 30kg x 10
Série 1: anterior 62.5kg x 12 | recomendado 60kg x 12
Decisão do coach: subir carga quando a prontidão permite e os guardrails aprovam
```

### Sprint 13 - Dashboard do Atleta

Objetivo:
Criar uma visão agregada da evolução do atleta para acompanhar progresso, consistência e sinais de atenção ao longo do tempo.

Entregue:
- Serviço `training/services/athlete_dashboard.py`
- Endpoint `GET /api/training/dashboard/<profile_id>/`
- KPIs globais:
  - treinos concluídos
  - volume total
  - séries totais
  - séries normais
  - falhas
  - RIR médio
  - último treino concluído
- Volume semanal agregado
- Lista dos últimos treinos com volume, séries, falhas e RIR médio
- Exercícios com melhor progressão de carga
- Exercícios a vigiar por falhas recentes, reps abaixo do alvo ou descida de carga
- Painel "Dashboard" no topo do programa no frontend
- Atualização automática do dashboard ao gerar programa, iniciar treino e terminar treino
- Testes do serviço e do endpoint
- Regra de aquecimento progressivo:
  - exercícios leves ou simples mantêm 1 aquecimento
  - exercícios compostos/moderados podem criar 2 aquecimentos
  - exercícios pesados podem criar 3 ou 4 aquecimentos
  - reps descem à medida que a carga se aproxima da primeira série normal
- Testes da regra de ramp-up e validação visual no browser integrado

### Sprint 14 - Memória de Treino

Objetivo:
Criar contexto acumulado ao longo do tempo para que a app reconheça padrões por atleta e por exercício, em vez de depender apenas da sessão atual.

Entregue:
- Modelo `AthleteTrainingMemory`
- Migration `training/migrations/0003_athletetrainingmemory.py`
- Serviço `training/services/training_memory.py`
- Memórias persistentes por utilizador, exercício e tipo:
  - progressão
  - watchlist
  - padrão de esforço
- Atualização automática da memória ao consultar o dashboard
- Atualização automática da memória ao terminar uma sessão
- Inclusão de `training_memories` na resposta do dashboard
- Painel "Memória do atleta" no frontend
- Evidências por memória para explicar o motivo do sinal
- Confiança por memória com base no número de sessões analisadas
- Testes de criação, persistência e exposição das memórias no dashboard

### Sprint 15 - Sistema Adaptativo Completo

Objetivo:
Criar a primeira camada de adaptação do plano com base no programa ativo, dashboard do atleta e memória persistente por exercício.

Entregue:
- Serviço `training/services/adaptive_plan.py`
- Endpoint `GET /api/training/adaptive-plan/<profile_id>/`
- Recomendações adaptativas por exercício do programa ativo
- Leitura direta da memória de treino:
  - `PROGRESSION` gera sugestão de progressão controlada de carga
  - `WATCHLIST` gera proteção de recuperação, mais margem e possível redução de volume
  - `EFFORT_PATTERN` gera aumento de margem antes de nova progressão
- Resumo por plano com contagem de ações e prioridades altas
- Painel "Plano adaptativo" no frontend
- Evidência visível por recomendação para explicar o motivo da decisão
- Primeira fase sem mutação automática do plano: a app recomenda, mostra o motivo e mantém o controlo explícito
- Modelo `AdaptivePlanDecision`
- Migration `training/migrations/0004_adaptiveplandecision.py`
- Endpoint `POST /api/training/adaptive-plan/apply/`
- Endpoint `GET /api/training/adaptive-plan/decisions/<profile_id>/`
- Botões no frontend para aplicar, adiar ou ignorar recomendações
- Aplicação controlada de séries e RIR alvo ao exercício selecionado
- Registo auditável do ajuste de carga sugerido para o próximo treino
- Histórico "Últimas decisões" no painel do plano adaptativo
- Testes do serviço adaptativo, endpoints e decisões aplicadas/adiadas
- Demo visual da Beatriz com 15 Upper, 15 Lower e 15 Full Body

### Sprint 16 - Deload e Feedback Semanal

Objetivo:
Transformar sinais persistentes de fadiga, watchlist e consistência em deloads sugeridos e feedback semanal.

Entregue:
- Serviço `training/services/weekly_feedback.py`
- Endpoint `GET /api/training/weekly-feedback/<profile_id>/`
- Feedback semanal calculado a partir do dashboard, memória e sessões recentes
- Estados semanais:
  - progressão saudável
  - monitorizar recuperação
  - deload recomendado
- Detecção de sinais de deload:
  - falhas recentes acumuladas
  - exercício em watchlist com risco elevado
  - várias memórias persistentes de atenção
  - padrão de esforço perto da falha
- Protocolo sugerido de deload:
  - 1 semana
  - volume total a cerca de 70%
  - RIR alvo 3+
  - evitar falha muscular
- Painel "Feedback semanal" no frontend
- Testes do serviço e endpoint

Próximos passos:
- Aplicar deload sugerido ao plano com confirmação explícita
- Guardar histórico de semanas de deload
- Melhorar a visualização semanal no dashboard

### Sprint 17 - Blocos de Treino e Periodização

Objetivo:
Organizar a evolução do atleta em blocos, com revisão de semanas de carga, deload e retorno à progressão.

Entregue:
- Modelo `TrainingBlock`
- Migration `training/migrations/0005_trainingblock.py`
- Serviço `training/services/training_blocks.py`
- Endpoint `GET /api/training/training-blocks/<profile_id>/`
- Criação/atualização automática do bloco ativo a partir dos treinos recentes
- Janela inicial de bloco com 4 semanas
- Fases de bloco:
  - `BUILD`
  - `DELOAD`
  - `RETURN`
- Resumo do bloco:
  - treinos concluídos
  - volume total
  - séries totais
  - falhas
  - RIR médio
  - volume semanal
- Recomendação de periodização por fase
- Integração com o feedback semanal para mudar fase quando há deload recomendado
- Painel "Bloco de treino" no frontend
- Testes do serviço e endpoint

Adicional entregue no Sprint 17:
- Catálogo expandido de exercícios com nome localizado em português e imagem associada
- Migrations `exercises/migrations/0003_exercise_image_localized_name.py` e `exercises/migrations/0004_exercise_crop_image_urls.py`
- Campos `localized_name` e `image_url` no modelo `Exercise`
- Imagens dos exercícios guardadas em `frontend/public/exercise-screens/` e recortes em `frontend/public/exercise-crops/`
- Endpoint `GET /api/training/exercise-substitutions/<training_exercise_id>/`
- Endpoint `POST /api/training/replace-exercise/`
- Serviço `training/services/exercise_substitution.py`
- Substituição de exercício limitada ao mesmo grupo muscular
- Bloqueio de trocas depois de existirem séries registadas nesse exercício durante a sessão
- Foto do exercício apresentada na linha do treino
- Painel de alternativas no frontend com imagem, nome, equipamento e padrão de movimento
- Testes para alternativas por grupo muscular, troca válida e rejeição de troca inválida
- Ecrã inicial atualizado com entrada em perfil existente por username
- Ecrã de criação de perfil redesenhado com seleção visual de género, nível e dias por semana
- Preservação da estrutura de aquecimento entre treinos repetidos
- Correção para impedir que W2/W3 sejam convertidas em séries normais no treino seguinte
- Separação entre tipo de série escolhido manualmente e tipo sugerido automaticamente pelo coach, evitando que sugestões automáticas substituam W2/W3 preservadas
- Séries de aquecimento sem RIR e sem falha registada
- API limpa automaticamente RIR/falha em séries `WARMUP`
- IA local e contexto enviado ao modelo tratam aquecimento sem RIR, usando carga, técnica, histórico e distância até à primeira série normal
- Check direto em séries de aquecimento no frontend, sem menu de esforço
- Testes para estrutura de aquecimento preservada e remoção de RIR em `WARMUP`
- Configuração de escala de pesos por exercício, com placas principais e bolachas/extras
- Recomendações de carga, aquecimento, backoff e progressão ajustadas aos pesos realmente disponíveis na máquina
- Contexto da IA atualizado com escala de carga do exercício
- Endpoint de detalhe de exercício para atualizar escala de pesos
- Botão temporário "Exportar histórico" no programa do atleta
- Export JSON do atleta com perfil, programas, treinos, exercícios, sessões, séries, memórias, decisões adaptativas e blocos de treino

Próximos passos do Sprint 17:
- Guardar blocos concluídos quando um novo bloco começa
- Comparar bloco atual com bloco anterior
- Aplicar semana de deload ao plano e medir retorno pós-deload
- Criar recomendações de novo bloco com base na resposta do atleta
- Rever/substituir imagens dos exercícios quando forem enviadas versões finais

## Roadmap

### Sprint 18 - Periodização Aplicada

Objetivo:
Transformar blocos e feedback semanal em alterações aplicáveis ao plano ao longo de ciclos completos.

Ideias:
- Encerrar bloco e abrir novo bloco
- Comparação pré e pós-deload
- Ajustes por bloco para volume, carga e RIR
- Revisão de resposta individual por exercício

## Estrutura do Projeto

```text
SHAPETRONYC/
├── backend/
│   ├── accounts/
│   ├── config/
│   ├── exercises/
│   ├── progression/
│   ├── recommendations/
│   ├── training/
│   └── manage.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   └── package.json
└── README.md
```

## Notas de Produto

Decisões atuais:
- O alvo principal de progressão é 12 reps.
- O incremento padrão de carga é 2.5kg.
- Séries abaixo de 12 reps em série normal são tratadas como sinal de falha ou fadiga.
- Séries de aquecimento não devem gerar progressão direta de carga.
- Drop sets são registadas, mas não são usadas como base principal para progressão do próximo treino.

Princípio do sistema:
SHAPETRONYC deve proteger consistência, execução e recuperação antes de forçar progressão de carga.
