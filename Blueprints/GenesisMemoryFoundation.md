# Blueprint — Genesis Memory Foundation

**Versão:** 1.0

## Objetivo

Definir o contrato oficial de memória do Genesis, isolado por Workspace,
independente de Interfaces, IA e persistência externa.

## Arquitetura

```text
Interface → MemoryService → MemoryEngine → MemoryRepository
                                             ├→ InMemoryRepository
                                             └→ SQLiteMemoryRepository
```

`MemoryEngine` contém validação de domínio. `MemoryService` coordena o caso de
uso sem duplicar regras. O repositório é uma porta substituível; nesta fundação,
o adapter em memória e o adapter SQLite implementam o mesmo contrato.

## Modelos públicos

- `MemoryRecord`: registro imutável com `id`, `workspace_id`, `mission_id`,
  `category`, `title`, `content`, `metadata` e `created_at`;
- `MemoryQuery`: consulta imutável por Workspace, com texto e filtros opcionais
  de missão, categoria e limite;
- `MemorySearchResult`: consulta, registros imutáveis e total encontrado.

Workspace é obrigatório. Mission e metadata são opcionais. Categorias são
textos livres não vazios. IDs são UUIDs textuais e datas são UTC.

## Repository

`MemoryRepository` define `store`, `search`, `list`, `delete` e `clear`.
`InMemoryRepository` mantém estado somente na própria instância, preserva
isolamento por Workspace e não escreve em arquivos ou serviços externos.

A busca v1 é textual, determinística e case-insensitive sobre título e conteúdo.
Resultados e histórico são apresentados do registro mais recente para o mais
antigo, com desempate pela ordem de inserção.

## Engine

`MemoryEngine` valida entradas, cria modelos imutáveis, delega armazenamento e
consulta ao repository e retorna `Core.result.Result`. Não conhece Application,
Interfaces, Companion, HTTP, providers ou persistência.

## Application

`MemoryService` expõe `store`, `search`, `history`, `delete` e `clear`, delegando
ao Engine. Interfaces devem usar somente este serviço.

## Legado experimental

O protótipo anterior não integra o contrato oficial: usa JSON, modelos mutáveis,
imports inválidos e não possui isolamento por Workspace. `database.py`,
`data/memory.json` e arquivos vazios antigos permanecem apenas como legado não
exportado. `record.py` e `memory.py` são shims de importação para os contratos
oficiais e não preservam persistência nem efeitos colaterais antigos.

## Limites

- persistência SQLite local, sem embeddings ou banco vetorial;
- sem IA, ranking semântico ou integração com Companion;
- sem paginação, atualização ou expiração;
- sem estado global;
- sem alterações em Core, CLI ou outros Engines.

## Critérios de conclusão

- [x] modelos e metadata imutáveis;
- [x] repository abstrato e implementação em memória;
- [x] store, search, history, delete e clear;
- [x] isolamento por Workspace e Mission opcional;
- [x] integração pelo MemoryService e bootstrap;
- [x] legado experimental fora da API oficial;
- [x] testes automatizados e compatibilidade do Companion.
