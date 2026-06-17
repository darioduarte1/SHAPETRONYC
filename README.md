# SHAPETRONYC

## Sprint 1 - Base Project Setup

### Backend
- Django criado
- Django REST Framework configurado
- Estrutura inicial do projeto criada

### Frontend
- React criado com Vite
- Ligação frontend ↔ backend configurada
- Testes iniciais de comunicação API

---

## Sprint 2 - User Profiles

### Implementado
- Criação de utilizadores
- Criação de perfis
- Objetivos de treino
- Nível de treino
- Experiência de treino
- Dias de treino por semana

### Modelos
- UserProfile

---

## Sprint 3 - Program Generator

### Implementado
- Geração automática de programas
- Estruturas baseadas em frequência semanal

### Modelos
- TrainingProgram
- TrainingWorkout
- TrainingWorkoutExercise

### Estruturas suportadas
- Full Body
- Upper / Lower
- Push / Pull / Legs
- Híbridos

---

## Sprint 4 - Exercise Database

### Implementado
- Base de dados de exercícios

### Modelo
- Exercise

### Dados armazenados
- Nome
- Grupo muscular
- Equipamento

---

## Sprint 5 - Set Tracking & Recommendation Engine

### Implementado
- Registo de séries
- Registo de carga utilizada
- Registo de repetições
- Registo de RIR
- Registo de falha
- Registo de observações

### Modelo
- SetLog

### Recommendation Engine
Entrada:
- Peso
- Repetições
- RIR
- Falha

Saída:
- Subir carga
- Manter carga
- Descer carga

---

## Sprint 6 - Workout Sessions

### Implementado
- Iniciar treino
- Terminar treino
- Histórico de sessões
- Ligação entre SetLogs e treino

### Modelo
- WorkoutSession

### Estados
- IN_PROGRESS
- COMPLETED
- CANCELLED

### Fluxo

Workout
↓
WorkoutSession
↓
SetLogs

---

## Sprint 7 - Hybrid Recommendation Engine

### Implementado
- Integração de observações do utilizador
- Interpretação de fadiga
- Simulação de comportamento IA

### Entrada adicional
- Notes

### Exemplos
- "Estou cansado"
- "Dormi mal"
- "Sem energia"

### Comportamento
O sistema pode:
- Ignorar progressão
- Manter carga
- Reduzir carga

mesmo quando a performance permitir aumento.

---

# Estado Atual

Implementado:

✅ Utilizadores

✅ Perfis

✅ Programas automáticos

✅ Exercícios

✅ Sessões de treino

✅ Registo de séries

✅ Motor de recomendações

✅ Notas e feedback do utilizador

---

# Próximos Sprints

## Sprint 8 - Session Summary

Objetivo:
Gerar análise automática do treino.

Métricas:
- Volume total
- Número de séries
- Número de exercícios
- Duração do treino
- Média de RIR
- Número de falhas

---

## Sprint 9 - Exercise History

Objetivo:
Mostrar evolução por exercício.

Métricas:
- Progressão de carga
- Progressão de repetições
- Volume acumulado

---

## Sprint 10 - Workout Progression

Objetivo:
Gerar recomendações para o próximo treino.

Exemplos:
- Subir carga
- Manter carga
- Reduzir volume
- Alterar RIR alvo

---

## Sprint 11 - AI Coach

Objetivo:
Substituir a simulação atual por um LLM.

Possíveis integrações:
- OpenAI
- Claude
- Gemini

Funções:
- Interpretar histórico
- Interpretar fadiga
- Ajustar progressão
- Gerar feedback personalizado
