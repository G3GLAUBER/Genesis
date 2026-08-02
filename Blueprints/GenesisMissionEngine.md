# Blueprint — Genesis Mission Engine

**Versão:** 1.0

## Objetivo

Transformar uma intenção explícita em uma missão estruturada, validada e
imutável, sem persistência e sem dependência de provedores de inteligência.

## Localização arquitetural

O componente pertence a `Engines/Mission/`. Ele contém regras de domínio de
missões e depende apenas do contrato estável `Core.result.Result`. O Kernel não
depende deste Engine.

## Estruturas públicas

### MissionStatus

Estados disponíveis: `DRAFT`, `READY`, `ACTIVE`, `PAUSED`, `COMPLETED`,
`FAILED` e `CANCELLED`.

### Mission

Estrutura imutável com:

- `id`: UUID textual único;
- `title`: título normalizado;
- `objective`: objetivo normalizado;
- `status`: estado atual, inicialmente `DRAFT`;
- `created_at`: instante UTC com fuso horário;
- `constraints`: tupla imutável de restrições;
- `success_criteria`: tupla imutável de critérios de sucesso;
- `source`: origem normalizada da intenção.

### MissionEngine

`MissionEngine.create(...)` valida e normaliza entradas simples. Em sucesso,
retorna `Result.success` com uma `Mission` em `data`. Em erro de entrada,
retorna `Result.error` sem criar estado parcial.

## Validações

- `title`, `objective` e `source` devem ser textos não vazios;
- espaços externos são removidos dos textos;
- `constraints` e `success_criteria` aceitam texto único ou coleção de textos;
- itens das coleções devem ser textos não vazios;
- identificadores são UUIDs novos a cada criação;
- o timestamp é criado em UTC.

## Limites da versão

- sem persistência;
- sem transições de estado;
- sem geração por IA;
- sem integração com CLI, Registry, EventBus ou Context.

## Evolução futura

Persistência, transições de estado e criação assistida deverão ser adicionadas
por contratos próprios, preservando `Mission` como representação de domínio e
sem introduzir dependência de fornecedor.

## Critérios de conclusão

- [x] missão e coleções imutáveis;
- [x] estados iniciais explícitos;
- [x] criação validada e normalizada;
- [x] UUID único e timestamp UTC;
- [x] retorno padronizado com `Result`;
- [x] testes automatizados;
- [x] nenhuma alteração no Kernel ou na CLI.
