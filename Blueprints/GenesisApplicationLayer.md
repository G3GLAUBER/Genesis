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
- `WorkspaceApplicationService`: coordena criação, consulta, listagem,
  arquivamento, restauração, seleção ativa e associação de missões;
- `MemoryService`: coordena armazenamento, busca, histórico, exclusão e limpeza
  pelo contrato público do Memory Engine;
- `bootstrap_application()`: compõe Registry, FakeProvider, Engines, Manager e
  serviços em uma instância isolada;
- modelos imutáveis de aplicação existem apenas para resultados agregados que
  não pertencem a um único domínio.

## Compatibilidade

`CompanionApplication` permanece como fachada pública e preserva seu construtor,
seus métodos, suas rotas e seus modelos públicos anteriores, delegando os casos
de uso para a camada Application.

## Limites

- sem regras de domínio, persistência real ou estado global;
- sem provider real ou framework de injeção de dependência;
- sem alterações em Core ou CLI;
- sem mudanças nas APIs públicas dos Engines.

## Critérios de conclusão

- [x] bootstrap centralizado e isolado;
- [x] serviços reutilizam Engines existentes;
- [x] casos de uso de Mission e Workspace cobertos;
- [x] falhas propagadas como `Result` controlado;
- [x] Companion usa Application Layer;
- [x] API pública anterior do Companion preservada;
- [x] testes automatizados e validação HTTP.
