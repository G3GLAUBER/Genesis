# Blueprint — Genesis Projects v1

**Versão:** 1.0

## Objetivo

Representar obras e projetos reais dentro de um Workspace, permitindo organizar
missões e acompanhar projetos operacionais sem persistência externa.

## Arquitetura

```text
Companion → ProjectService → ProjectEngine → ProjectRepository
                                             ├→ InMemoryProjectRepository
                                             └→ SQLiteProjectRepository
```

As regras e os modelos pertencem a `Engines/Projects/`. A camada Application
coordena o contrato e o Companion apenas traduz entradas e apresenta resultados.

## Modelos públicos

`Project` é imutável e contém `id`, `workspace_id`, `title`, `client`, `address`,
`description`, `status`, `created_at` e `mission_ids`.

`ProjectStatus` possui `PLANNING`, `ACTIVE`, `ON_HOLD`, `COMPLETED` e
`ARCHIVED`. Projetos novos começam em `PLANNING`; restaurar um projeto arquivado
o coloca em `ACTIVE`.

## Repository

`ProjectRepository` define armazenamento, consulta e listagem. A implementação
`InMemoryProjectRepository` mantém estado somente na própria instância. O
adapter SQLite oficial preserva a mesma ordem, isolamento e integridade de
Workspace.

## Engine

`ProjectEngine` valida entradas, cria e atualiza modelos imutáveis, delega ao
repository e retorna `Result`. Workspace, título, cliente e endereço são textos
obrigatórios; descrição pode ser vazia; IDs de missão são textos não vazios e
não podem ser associados duas vezes.

Projetos arquivados não aceitam novas missões. Arquivar ou restaurar em estado
incompatível retorna erro controlado.

## Application

`ProjectService` expõe `create`, `list`, `get`, `archive`, `restore` e
`attach_mission`, sem duplicar validações de domínio.

## Companion

- `GET /projects` lista projetos do Workspace ativo;
- `POST /projects` cria um projeto no Workspace informado ou ativo;
- o dashboard mostra projetos ativos, concluídos e os projetos mais recentes;
- APIs, rotas e construção pública anteriores permanecem compatíveis.

## Limites

- SQLite local por padrão e modo em memória explícito;
- sem login, autorização ou isolamento multiusuário;
- sem IA, providers, embeddings ou integrações externas;
- sem exclusão física, edição geral ou transição pública para todos os estados;
- sem estado global e sem alterações no Core ou na CLI.

## Critérios de conclusão

- [x] modelos imutáveis e estados explícitos;
- [x] repository abstrato e implementação em memória;
- [x] criação, listagem, consulta, arquivamento e restauração;
- [x] associação de missões sem duplicação;
- [x] ProjectService e bootstrap oficial;
- [x] dashboard e rotas do Companion;
- [x] compatibilidade pública preservada;
- [x] testes unitários, de integração e HTTP;
