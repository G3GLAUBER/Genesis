# Blueprint — Genesis Workflow Engine v0.1

**Versão:** 0.1

## Objetivo

Avaliar deterministicamente a continuidade de um Project e indicar a próxima
ação compreensível, sem executar trabalho, alterar estados de domínio ou criar
persistência.

## Arquitetura

```text
Companion → WorkflowApplicationService → WorkflowEngine
                         ├→ ProjectService
                         ├→ MissionApplicationService
                         ├→ MissionCopilotApplicationService
                         └→ RemodelingApplicationService
```

O Workflow Engine é uma capacidade nova e isolada em `Engines/Workflow/`. Ele
recebe uma observação imutável composta pela Application Layer e não acessa
repositories, Interfaces, rede ou outros Engines diretamente.

## Modelos públicos

### WorkflowStage

Estados ordenados da orientação: `PROJECT_CREATED`, `MISSION_CREATED`,
`MISSION_COMPLETED`, `PROPOSAL_PENDING`, `PROPOSAL_APPROVED`,
`PLANNING_PENDING`, `EXECUTION_PENDING` e `COMPLETED`.

### WorkflowRecommendation

Recomendação imutável com título, descrição, prioridade, destino e razão. O
destino apenas navega para uma experiência existente; nunca dispara a ação.

### WorkflowState

Estado imutável com Project, etapa atual, progresso, próxima ação,
recomendação, motivo, bloqueios e instante UTC de avaliação.

### WorkflowObservation

Evidência imutável do estado já implementado: existência de Missions, resultado
do Mission Copilot, Proposal e seu estado, Planning e Execution. A observação
não cria fatos ausentes nem persiste inferências.

## Regras determinísticas

1. Project sem Mission recomenda criar a primeira Mission;
2. Mission existente recomenda continuar no Mission Copilot;
3. resultado do Mission Copilot recomenda preparar uma Proposal;
4. Proposal não aprovada recomenda Review;
5. Proposal aprovada recomenda preparar Planning;
6. Planning disponível recomenda iniciar Execution;
7. Execution pendente recomenda continuar a execução;
8. Execution concluída apresenta o Project como concluído no Workflow.

Estados mais avançados prevalecem sobre os anteriores. Bloqueios observados
mantêm a recomendação, explicam o impedimento e elevam sua prioridade.

## Progresso

O progresso v0.1 é uma escala simples e estável por etapa: 10, 25, 40, 50, 60,
70, 85 e 100. Ele comunica posição no fluxo, não mede esforço, prazo ou valor
económico.

## Application

`WorkflowApplicationService.evaluate_project(project_id)` reúne apenas dados
disponíveis pelos serviços públicos existentes, cria uma `WorkflowObservation`
e delega toda regra de avaliação ao Engine.

`list_for_workspace(workspace_id)` preserva a ordem oficial de Projects.

### Limitação observável de Planning na v0.1

`WorkflowObservation` possui o campo `planning_ready` para representar uma
evidência de Planning quando ela existir. Na arquitetura atual, porém, o
`Planner` é chamado pelo `MissionApplicationService` durante o fluxo de
execução e não há uma consulta pública para listar ou recuperar um `Plan` sem
uma `MissionExecution` correspondente. Portanto, `WorkflowApplicationService`
deve enviar `planning_ready=False` na v0.1 e nunca inferir Planning a partir de
uma Proposal aprovada ou de uma Execution existente.

As etapas `PLANNING_PENDING` e a recomendação de iniciar Execution continuam
suportadas pelo `WorkflowEngine` para observações que tragam evidência explícita
(por exemplo, uma composição futura com contrato de Planning). A Application
só poderá preencher `planning_ready=True` após existir esse contrato público;
até lá, o fluxo real avança de Proposal aprovada somente quando houver uma
Execution observável, sem fabricar uma transição de Planning.

Uma Execution observável é derivada dos registros públicos de
`MissionApplicationService`: qualquer registro não concluído mantém
`execution_pending=True`; somente quando todos os registros relacionados estão
concluídos `execution_completed=True`. Um registro parcial nunca pode ser
considerado Project concluído.

## Companion

- Command Center apresenta a primeira orientação de Workflow como “Próxima
  ação”;
- Projects mostra status, progresso, etapa e próxima ação;
- recomendações são links para destinos existentes e não executam mudanças;
- APIs e rotas anteriores permanecem compatíveis.

## Limites

- sem persistência de Workflow;
- sem IA, rede, provider ou dependência externa;
- sem criação de Proposal, Planning ou Execution;
- sem transições automáticas de Project ou Mission;
- sem alteração em Core, CLI, Infrastructure ou Engines existentes;
- o estado é recalculado a partir das evidências voláteis disponíveis.

## Critérios de conclusão

- [x] modelos imutáveis e estágios explícitos;
- [x] avaliação determinística e progresso estável;
- [x] recomendação, motivo, prioridade e destino compreensíveis;
- [x] nenhuma ação automática ou chamada externa;
- [x] integração aditiva com Application e Companion;
- [x] Command Center e Projects mostram próxima ação;
- [x] APIs e rotas anteriores preservadas;
- [x] testes específicos e HTTP aprovados; suíte completa validada no review.
