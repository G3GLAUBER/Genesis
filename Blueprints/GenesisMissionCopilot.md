# Blueprint — Genesis Mission Copilot v1

**Versão:** 1.0

## Objetivo

Transformar uma missão explícita em um pedido contextual para Intelligence em
modo `FREE_ONLY`, com revisão humana por Manual Handoff e resultado estruturado
opcionalmente armazenado como Memory.

## Arquitetura

```text
Companion → MissionCopilotApplicationService
                         ├→ MissionApplicationService
                         ├→ IntelligenceApplicationService
                         ├→ WorkspaceApplicationService
                         ├→ ProjectService
                         └→ MemoryService
```

O Mission Copilot é um caso de uso de Application. Ele coordena contratos
públicos existentes e não move nem duplica validações de Mission,
Intelligence, Projects, Workspace ou Memory. Core e CLI permanecem inalterados.

## Fluxo

1. validar Workspace e Project informados;
2. criar a Mission pelo serviço oficial e associá-la ao Workspace e ao Project;
3. reunir contexto real disponível no mesmo Workspace;
4. montar um prompt explícito com contrato JSON;
5. solicitar decisão determinística de Intelligence em `FREE_ONLY`;
6. criar Manual Handoff para o provider recomendado;
7. receber resposta manual, sem rede ou automação externa;
8. validar o JSON e criar `MissionCopilotResult` imutável;
9. permitir armazenamento opcional como Memory.

Nenhuma ação sugerida é executada automaticamente.

## Modelos de aplicação

### MissionCopilotContext

Contexto imutável com Workspace, Project opcional, constraints, Memories do
mesmo Workspace e resultado esperado. Campos ausentes continuam ausentes.

### MissionCopilotRequest

Agregado imutável com Mission, contexto, prompt, decisão de roteamento e data de
criação.

### MissionCopilotResult

Resultado volátil e imutável com identificador, relações de Mission, Workspace
e Project, provider, modo, prompt, resposta bruta, resumo, ações sugeridas,
riscos, premissas e timestamp UTC.

## Contrato da resposta manual

O corpo deve ser um objeto JSON. Todos os campos são opcionais:

```json
{
  "summary": "Resumo objetivo",
  "suggested_actions": ["Ação apenas sugerida"],
  "risks": ["Risco identificado"],
  "assumptions": ["Premissa declarada"]
}
```

Campos presentes precisam respeitar os tipos documentados. JSON inválido,
objeto inválido ou valores incompatíveis retornam `Result.error`. A resposta
bruta é preservada. O parser usa somente `json.loads`, nunca executa conteúdo.

## API de Application

- `create_mission_copilot_request(...)`;
- `create_handoff(mission_id)`;
- `complete_handoff(mission_id, handoff_id, response=...)`;
- `build_result(mission_id, handoff_id)`;
- `save_result_as_memory(result_id)`;
- `get_result(result_id)`.

Consultas aditivas de request e handoff podem ser expostas para apresentação.

## Rotas do Companion

- `POST /missions` preserva o fluxo legado e aceita o fluxo Copilot por campo
  explícito;
- `GET /missions/{id}`;
- `POST /missions/{id}/copilot`;
- `POST /missions/{id}/handoffs/{handoff_id}/complete`;
- `POST /missions/{id}/results/{result_id}/memory`.

## Segurança e limites

- sem provider pago em `FREE_ONLY`;
- sem API real, scraping, browser automation ou chamada externa;
- sem `eval`, execução de código ou ações autônomas;
- requests, handoffs e resultados voláteis nesta versão;
- Memory é criada somente por confirmação explícita;
- sugestões, riscos e premissas são informação para revisão humana;
- APIs e rotas anteriores permanecem compatíveis.

## Critérios de conclusão

- [x] contexto contém apenas dados reais disponíveis;
- [x] decisão usa exclusivamente `FREE_ONLY`;
- [x] Manual Handoff preserva prompt e resposta;
- [x] JSON válido produz resultado imutável e JSON inválido falha com clareza;
- [x] Project e Workspace recebem a associação da Mission;
- [x] Memory é opcional e explicitamente solicitada;
- [x] nenhuma ação sugerida é executada;
- [x] nenhuma chamada externa ou dependência nova;
- [x] rotas HTTP e compatibilidade cobertas por testes;
- [x] Core e CLI inalterados.
