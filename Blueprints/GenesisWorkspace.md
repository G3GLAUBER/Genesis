# Blueprint — Genesis Workspace

**Versão:** 1.0

## Objetivo

Definir o Workspace como unidade organizacional principal do Gênesis. Nesta
fundação, cada missão criada pelo Companion pertence a exatamente um Workspace,
sem alterar o contrato público de `Mission` e sem persistência externa.

## Localização arquitetural

As regras de domínio pertencem a `Engines/Workspace/`. A apresentação web fica
em `Interfaces/Workspace/` e a composição com Mission, Planning e Execution
continua em `Interfaces/Companion/`.

```text
Companion → WorkspaceManager → WorkspaceEngine → Result[Workspace]
    ↓                                  ↓
MissionEngine                  coleção em memória
```

O Core e a CLI não conhecem Workspace. O Engine depende somente do contrato
estável `Core.result.Result`.

## Estruturas públicas

### WorkspaceStatus

Estados disponíveis: `ACTIVE` e `ARCHIVED`.

### Workspace

Estrutura imutável com:

- `id`: UUID textual único;
- `name`: nome normalizado;
- `description`: descrição normalizada;
- `created_at`: instante UTC com fuso horário;
- `status`: estado atual, inicialmente `ACTIVE`;
- `mission_ids`: tupla imutável de IDs de missões associadas.

### WorkspaceEngine

```python
engine.create(name=name, description=description)
engine.rename(workspace=workspace, name=name)
engine.archive(workspace=workspace)
engine.restore(workspace=workspace)
engine.add_mission(workspace=workspace, mission_id=mission_id)
engine.remove_mission(workspace=workspace, mission_id=mission_id)
```

Todas as operações retornam `Result`. Atualizações produzem um novo Workspace e
jamais modificam o objeto recebido.

### WorkspaceManager

Mantém a coleção em memória e é a fonte oficial de verdade durante a vida da
aplicação:

```python
manager.create(name=name, description=description)
manager.get(workspace_id)
manager.list(include_archived=False)
manager.delete(workspace_id)
manager.restore(workspace_id)
manager.search(name, include_archived=False)
```

O Manager também expõe `rename`, `add_mission` e `remove_mission` para atualizar
itens da coleção exclusivamente por meio do WorkspaceEngine. Nomes são únicos
sem distinção entre maiúsculas e minúsculas, inclusive entre itens arquivados.
Listagem e busca omitem arquivados por padrão e preservam a ordem de criação.

## Integração com o Companion

- a composição padrão cria um Workspace inicial ativo;
- o dashboard mostra Workspace ativo, quantidade total de Workspaces ativos e
  quantidade de missões associadas a eles;
- `/workspaces` lista e cria Workspaces;
- `/workspaces/{id}` abre um Workspace e mostra seus IDs de missão;
- `execute_mission(...)` mantém sua chamada anterior compatível e associa a
  nova missão ao Workspace ativo, ou ao `workspace_id` opcional informado;
- toda entrada fornecida pelo usuário é escapada na renderização.

## Validações

- `name` deve ser texto não vazio;
- `description` deve ser texto; vazio é permitido;
- IDs de missão devem ser textos não vazios;
- uma missão não pode ser adicionada duas vezes ao mesmo Workspace;
- remover associação inexistente retorna erro controlado;
- somente Workspaces ativos podem ser renomeados ou receber/remover missões;
- arquivar item arquivado e restaurar item ativo retornam erro controlado.

## Limites da versão

- persistência somente em memória;
- sem banco, arquivos, login, IA adicional ou atualização em tempo real;
- sem alteração de Core, CLI, AI, Mission, Planning ou Execution;
- sem migração de missões criadas fora do Companion;
- o Workspace ativo é compartilhado pela instância local do Companion.

## Critérios de conclusão

- [x] modelos e coleções imutáveis;
- [x] criação e nomes únicos;
- [x] renomeação, arquivamento e restauração;
- [x] associação e remoção de Mission IDs;
- [x] Manager em memória com busca e listagem;
- [x] página de Workspace e dashboard no Companion;
- [x] fluxo anterior do Companion preservado;
- [x] testes unitários, integração HTTP e fluxo completo;
- [x] suíte completa e Doctor executados;
- [x] nenhuma alteração no Core ou na CLI.
