# ADR-001 — Arquitetura Orientada a Eventos

> **Identificador legado; parcialmente superseded pelo ADR-002.** A arquitetura
> orientada a eventos permanece aceita, mas a exigência absoluta de EventBus foi
> substituída: chamadas síncronas entre contratos públicos podem ser definidas
> por Blueprint; eventos são usados quando existir semântica aprovada.

## Status
Aceito

## Data
2026-08-01

## Contexto

O Projeto Gênesis será uma plataforma de conhecimento composta por diversos módulos e agentes.

Para evitar acoplamento entre os componentes e facilitar a evolução do sistema, toda comunicação interna será realizada por eventos.

## Decisão

Foi adotada uma arquitetura orientada a eventos (Event-Driven Architecture).

Todos os módulos deverão publicar e consumir eventos através do Event Bus.

Nenhum agente poderá chamar diretamente outro agente.

## Consequências

### Benefícios

- Baixo acoplamento
- Escalabilidade
- Facilidade para adicionar novos agentes
- Independência entre módulos
- Facilidade para testes

### Desvantagens

- Maior complexidade inicial
- Necessidade de monitoramento dos eventos

## Responsáveis

CEO do Projeto: Glauber

Arquiteto-Chefe: ChatGPT
