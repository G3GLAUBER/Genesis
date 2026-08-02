# Blueprint — Genesis Planner

**Versão:** 1.0

## Objetivo

Transformar uma missão válida e etapas fornecidas explicitamente em um plano
imutável, ordenado e estruturalmente consistente.

## Localização arquitetural

O componente pertence a `Engines/Planning/`. Ele depende do contrato de missão
em `Engines/Mission/` e de `Core.result.Result`. Não contém integração com IA,
persistência ou interface.

## Estruturas públicas

### StepStatus

Estados disponíveis: `PENDING`, `READY`, `IN_PROGRESS`, `COMPLETED`, `FAILED`,
`SKIPPED` e `CANCELLED`. Uma nova etapa começa em `PENDING`.

### PlanStatus

Estados disponíveis: `READY`, `ACTIVE`, `COMPLETED`, `FAILED` e `CANCELLED`.
Um plano validado começa em `READY`.

### PlanStep

Estrutura imutável com `id`, `title`, `description`, `order`, `status`,
`dependencies` e `capability`. `PlanStep.create(...)` gera um UUID, normaliza
textos e converte dependências para tupla.

### Plan

Estrutura imutável com `id`, `mission_id`, `status`, `created_at` e `steps`.
As etapas são armazenadas em uma tupla ordenada.

### Planner

`Planner.create_plan(mission, steps)` retorna `Result.success` com `Plan` em
`data`, ou `Result.error` quando a missão ou as etapas forem inválidas.

## Validações

- `mission` deve ser uma `Mission`;
- deve existir ao menos uma etapa;
- cada item deve ser um `PlanStep` válido;
- IDs e ordens devem ser únicos;
- ordens devem ser inteiros positivos;
- títulos e descrições não podem ser vazios;
- toda dependência deve apontar para uma etapa do mesmo plano;
- auto-dependências e ciclos são rejeitados;
- `capability`, quando presente, deve ser texto não vazio.

A ordenação é crescente por `order` e não modifica as etapas recebidas.

## Limites da versão

- etapas são sempre fornecidas pelo consumidor;
- sem geração automática ou uso de IA;
- sem execução, replanejamento ou transições de estado;
- sem persistência, paralelismo ou integração com CLI.

## Evolução futura

Geração assistida, execução, políticas de replanejamento e persistência poderão
ser adicionadas sobre os contratos públicos, mantendo separadas a definição do
plano e sua execução.

## Critérios de conclusão

- [x] plano e etapas imutáveis;
- [x] referência à missão preservada;
- [x] ordem determinística;
- [x] dependências validadas, inclusive ciclos;
- [x] retorno padronizado com `Result`;
- [x] testes automatizados;
- [x] nenhuma alteração no Kernel, AI Orchestrator ou CLI.
