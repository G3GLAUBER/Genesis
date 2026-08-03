# Blueprint — Genesis Persistence Foundation v1

## Objetivo

Persistir Workspaces, Projects e Memories localmente em SQLite, preservando os
contratos dos Engines e preservando o modo em memória como padrão compatível.

## Arquitetura

```text
Interfaces → Application → Engines → Repository contracts → SQLite adapters
```

SQL, migrations e conexões pertencem a `Infrastructure/Persistence/`. Engines e
Application Services não conhecem SQL. O banco padrão é `Data/genesis.db` e o
caminho é configurável no bootstrap.

## Contrato

`bootstrap_application()` preserva adapters isolados em memória.
`persistent=True` usa SQLite e `database_path` também ativa SQLite
implicitamente. O ponto de entrada operacional do Companion seleciona
persistência explicitamente.
Migrations versionadas em `schema_migrations` são determinísticas, idempotentes
e executadas antes da composição dos repositories.

Escritas usam transações explícitas e queries parametrizadas. Metadata de Memory
usa JSON determinístico; pickle e dependências externas são proibidos.

## Limites

- sem ORM, PostgreSQL, nuvem ou banco vetorial;
- Mission, Plan e Execution permanecem voláteis;
- sem transações distribuídas entre Engines;
- sem autenticação ou multiusuário.
