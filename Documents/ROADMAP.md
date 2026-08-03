# Gênesis — Roadmap Técnico Oficial

Status: Canônico
Atualizado na Sprint 0.3.1

Este documento define sequência e prioridade, não contratos. Cada componente ou
mudança arquitetural continua sujeito à Constituição, aos ADRs, à Architecture e
a Blueprint aprovado.

## Estado atual

Estão implementados e testados: fundação do Core, CLI/Doctor, AI Provider e AI
Orchestrator com FakeProvider, Mission, Planning, Execution, Companion local e
Workspace em memória. Memory é experimental; Knowledge, Search, persistência,
Agents e integrações reais ainda não são capacidades implementadas.

## Genesis 0.3 — Consolidação da fundação

- 0.3.1: estabelecer autoridade documental e fontes canônicas;
- definir por review a futura camada de aplicação/casos de uso;
- decidir o destino do protótipo Memory antes de evoluí-lo;
- padronizar contratos básicos, tempo e eventos sem quebrar APIs;
- instituir verificações arquiteturais, typing, lint e cobertura.

## Genesis 0.4 — Persistência e Memory

- aprovar Blueprints de persistência e Memory;
- definir ownership, repositories, transações e migrações;
- persistir Workspace, Mission, Plan e Execution de forma incremental;
- implementar Memory mínima, testável e independente de Interface;
- validar restart, integridade e concorrência.

## Genesis 0.5 — Knowledge e providers reais

- aprovar e implementar Knowledge Engine;
- introduzir proveniência, versionamento e busca textual;
- implementar um primeiro adapter real atrás de `AIProvider`;
- definir credenciais, timeout, erros, rate limit, retry e observabilidade;
- preservar a independência do Core e dos consumidores.

## Genesis 0.6 — API, Agents e plugins

- definir contratos de Agent, ferramentas, permissões e lifecycle;
- definir execução durável, cancelamento e retomada;
- criar API pública versionada sobre casos de uso compartilhados;
- definir manifest, namespaces, compatibilidade e confiança de plugins;
- introduzir identidade e ownership como fundação de multiusuário.

## Genesis 1.0 — Produto confiável

- isolamento multiusuário e autorização;
- clientes desktop e mobile consumindo contratos públicos/API;
- backup, restore e migrações testados;
- observabilidade, segurança, testes de carga e recuperação;
- política formal de releases e compatibilidade.

## Adiado até a fundação correspondente

Agentes autônomos, plugins dinâmicos, banco vetorial, execução paralela,
desktop, mobile e multiusuário não devem anteceder os contratos, persistência,
segurança e isolamento previstos nas fases anteriores.
