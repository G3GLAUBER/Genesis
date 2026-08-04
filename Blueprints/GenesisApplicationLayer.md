# Blueprint — Genesis Application Layer v1

**Versão:** 1.0

## Objetivo

Definir a camada oficial de casos de uso entre Interfaces e Engines, sem mover
ou duplicar regras de domínio.

## Arquitetura

```text
Interfaces → Application → Engines → Core
```

`Application/` coordena contratos públicos existentes. Interfaces traduzem
entrada e saída; Engines permanecem como fontes oficiais das regras de domínio.

## Componentes

- `MissionApplicationService`: cria missão, cria o plano demonstrativo, executa
  a missão, opcionalmente a associa a um Workspace e mantém histórico volátil
  de missões e execuções da instância;
- `MissionCopilotApplicationService`: coordena Mission, contexto de Workspace e
  Project, decisão `FREE_ONLY`, Manual Handoff, resultado estruturado volátil e
  armazenamento opcional em Memory, sem executar sugestões;
- `WorkspaceApplicationService`: coordena criação, consulta, listagem,
  arquivamento, restauração, seleção ativa e associação de missões;
- `MemoryService`: coordena armazenamento, busca, histórico, exclusão e limpeza
  pelo contrato público do Memory Engine;
- `ProjectService`: coordena criação, consulta, listagem, arquivamento,
  restauração e associação de missões pelo contrato de Projects;
- `IntelligenceApplicationService`: coordena catálogo, roteamento, handoffs,
  execução automática pelo AIOrchestrator e integração opcional com Memory;
- `RemodelingApplicationService`: coordena briefs e propostas voláteis com
  Intelligence, Mission, Projects e Memory, exigindo aprovação antes de aplicar;
- `bootstrap_application()`: compõe Registry, FakeProvider, Engines, repositories
  e serviços; preserva memória por padrão e permite SQLite explicitamente;
- modelos imutáveis de aplicação existem apenas para resultados agregados que
  não pertencem a um único domínio.

## Compatibilidade

`CompanionApplication` permanece como fachada pública e preserva seu construtor,
seus métodos, suas rotas e seus modelos públicos anteriores, delegando os casos
de uso para a camada Application.

## Limites

- sem regras de domínio, queries SQL ou estado global;
- requests e resultados do Mission Copilot permanecem voláteis;
- sem provider real ou framework de injeção de dependência;
- sem alterações em Core ou CLI;
- sem mudanças nas APIs públicas dos Engines.

## Critérios de conclusão

- [x] bootstrap centralizado e isolado;
- [x] serviços reutilizam Engines existentes;
- [x] casos de uso de Mission e Workspace cobertos;
- [x] caso de uso Mission Copilot com revisão humana e Memory opcional;
- [x] falhas propagadas como `Result` controlado;
- [x] Companion usa Application Layer;
- [x] API pública anterior do Companion preservada;
- [x] testes automatizados e validação HTTP.
