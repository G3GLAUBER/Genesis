# Blueprint — Genesis Mission Execution

**Versão:** 1.0

## Objetivo

Executar sequencialmente um `Plan` pertencente a uma `Mission`, transformando
cada `PlanStep` em `AIRequest` e consolidando respostas e falhas em um relatório
imutável.

## Arquitetura

O componente pertence a `Engines/Execution/` e coordena somente contratos
públicos já existentes:

```text
Mission + Plan
      ↓
MissionExecutionEngine
      ↓
PlanStep → AIRequest → AIOrchestrator → AIResponse
      ↓
StepExecutionResult → MissionExecutionReport → Result
```

O Kernel não depende deste Engine. Não há conhecimento de providers, Registry,
rede ou SDKs externos.

## Estruturas públicas

### ExecutionStatus

Estados: `PENDING`, `RUNNING`, `COMPLETED`, `FAILED` e `SKIPPED`.

### StepExecutionResult

Resultado imutável com `step_id`, `status`, `provider_id`, `content`, `error`,
`started_at` e `completed_at`. Etapas ignoradas não possuem `started_at`.

### MissionExecutionReport

Relatório imutável com `mission_id`, `plan_id`, `status`, `step_results`,
`started_at` e `completed_at`.

### MissionExecutionFailure

Falha imutável de validação com `code`, `message`, `mission_id` e `plan_id`.
É usada quando não há dados válidos suficientes para construir um relatório.

### MissionExecutionEngine

```python
engine = MissionExecutionEngine(ai_orchestrator)
result = engine.execute(mission=mission, plan=plan)
```

Sucesso retorna `Result.success` com `MissionExecutionReport`. Falha de etapa
retorna `Result.error` com o relatório parcial e falhas de entrada retornam
`Result.error` com `MissionExecutionFailure`.

## Política sequencial

- etapas são ordenadas crescentemente por `order`;
- uma etapa é executada por vez;
- todas as dependências devem estar `COMPLETED` antes da execução;
- o prompt combina título e descrição da etapa;
- `PlanStep.capability` é copiada para `AIRequest.capability`;
- o primeiro erro interrompe novas chamadas ao AI Orchestrator;
- etapas restantes são registradas como `SKIPPED`;
- todas as etapas concluídas produzem relatório `COMPLETED`;
- qualquer falha produz relatório `FAILED`.

## Tratamento de falhas

São convertidos em dados controlados:

- tipos inválidos de Mission e Plan;
- plano incompatível com a missão ou sem etapas;
- etapas sem capability;
- dependências ainda não concluídas;
- `Result.error` do AI Orchestrator;
- exceções inesperadas, registrando apenas o tipo da exceção;
- retornos fora do contrato e `AIResponse` inválida.

## Decisão sobre EventBus

O EventBus não é usado na v1. O `EventType` atual não define eventos de
execução, e reaproveitar eventos semânticos não relacionados ou alterar o
Kernel seria inadequado. Eventos poderão ser adicionados após um contrato
próprio e revisão arquitetural.

## Limites da v1

- sem paralelismo, retry ou retomada;
- sem persistência;
- sem aprovação humana;
- sem alteração do estado original de Mission, Plan ou PlanStep;
- sem integração com CLI ou providers reais.

## Evolução futura

Versões futuras poderão adicionar eventos tipados, persistência, cancelamento,
retomada, retry e execução paralela por política, preservando `execute()` e os
modelos de relatório.

## Critérios de conclusão

- [x] execução sequencial e determinística;
- [x] dependências respeitadas;
- [x] integração exclusiva via AI Orchestrator;
- [x] falha interrompe execução e marca restantes como `SKIPPED`;
- [x] resultados e falhas estruturados e imutáveis;
- [x] nenhuma entrada é modificada;
- [x] testes automatizados;
- [x] nenhuma alteração em Core, CLI ou AI Orchestrator.
