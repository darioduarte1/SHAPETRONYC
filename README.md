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

### Frontend

```bash
cd frontend
npm run dev
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
- Backend: 14 testes a passar
- Frontend: lint a passar
- Frontend: build a passar
- Teste manual no browser integrado concluído com sucesso

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
- Timer de descanso
- Dropdowns por dia e por exercício
- Bloqueio dos restantes dias durante treino ativo
- Resumo simples da sessão em tempo real
- Recomendações para o próximo treino após terminar uma sessão

Em preparação:
- Dashboard completo
- Integração real com LLM
- Memória longitudinal do atleta

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

## Roadmap

### Sprint 12 - AI Coach

Objetivo:
Substituir progressivamente a simulação baseada em regras por uma camada de coach com LLM.

Possíveis integrações:
- OpenAI
- Claude
- Gemini

Funções esperadas:
- Interpretar histórico
- Interpretar fadiga
- Ajustar progressão
- Gerar feedback personalizado
- Explicar decisões de treino em linguagem natural

### Sprint 13 - Dashboard do Atleta

Objetivo:
Criar uma visão agregada da evolução do atleta.

Ideias:
- KPIs de volume
- Evolução de cargas
- Evolução de reps
- Frequência de treino
- Exercícios com melhor progressão
- Exercícios com estagnação

### Sprint 14 - Memória de Treino

Objetivo:
Criar contexto acumulado ao longo do tempo.

Ideias:
- Preferências do atleta
- Exercícios problemáticos
- Histórico de fadiga
- Tendências por grupo muscular
- Recomendações com base em múltiplas semanas

### Sprint 15 - Sistema Adaptativo Completo

Objetivo:
Permitir que o plano se ajuste automaticamente com base no histórico, recuperação e performance.

Ideias:
- Ajuste automático de volume
- Ajuste automático de carga
- Alteração de exercícios
- Deloads sugeridos
- Feedback semanal

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
