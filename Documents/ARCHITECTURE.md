# Gênesis — Arquitetura Oficial

Versão: 1.1
Status: Canônico

## Objetivo

O Gênesis é um Sistema Operacional de Inteligência Modular. Engines, Agents e
Interfaces evoluem de forma desacoplada por meio de contratos e infraestrutura
comuns, preservando independência de fornecedores de IA.

## Princípios obrigatórios

- o Kernel nunca depende de Engines;
- Interfaces não contêm regras de domínio;
- cada responsabilidade possui uma única fonte oficial de verdade;
- componentes novos possuem Blueprint e testes;
- contratos públicos evoluem de forma compatível;
- simplicidade, coesão e substituibilidade prevalecem;
- SDKs, modelos e credenciais de fornecedores não entram no Core, CLI,
  Interfaces ou contratos de domínio.

## Estado implementado

O fluxo do Kernel é:

```text
Usuário → CLI → Context → Orchestrator → Registry → handler → Result/resposta
```

A comunicação local por eventos é:

```text
Event → EventBus → Dispatcher → listeners
```

O fluxo demonstrativo do Companion é:

```text
Browser → Companion → Application → Mission → Planning → Execution
                              └→ Workspace          └→ AI Orchestrator
                                                       └→ FakeProvider
```

O Companion é a primeira Interface operacional: oferece dashboard, Workspaces,
missões, memórias, execuções e timeline sobre os três Application Services, com
HTML e CSS próprios e estado exclusivamente volátil.

O indicador Application Health informa somente a disponibilidade local desses
Services. Ele não executa, representa nem substitui o Genesis Doctor oficial.

Chamadas diretas entre contratos públicos de Engines são permitidas quando um
Blueprint específico define a composição. O EventBus é usado para comunicação
desacoplada quando existe um evento semanticamente aprovado; ele não é uma
exigência para toda chamada síncrona. O ADR-002 substitui, nesse ponto, a
formulação absoluta do ADR histórico de eventos.

## Camadas e direção de dependências

```text
Interfaces → Application → Engines → Core
CLI        → Orchestrator/Registry → handlers
Agents     → contratos públicos de Application/Engines/Core
Core       ↛ Engines, Application, Agents, Interfaces ou fornecedores
```

### CLI e Interfaces

Recebem entrada, validam formato, criam contexto quando aplicável, chamam casos
de uso e apresentam resultados. Não compõem Engines nem se tornam fonte de
regras de domínio.

### Application

Camada oficial de casos de uso. Coordena contratos públicos dos Engines,
concentra a composição em um bootstrap isolado e retorna resultados estruturados
para qualquer Interface. Não contém regras de domínio, persistência ou estado
global.

### Core

Kernel pequeno e estável: Configuration, Context, Result, Registry,
Orchestrator, Event, EventBus, Dispatcher, Logger e Lifecycle.

### Engines

Capacidades internas especializadas. Atualmente há implementações funcionais de
AI, Mission, Planning, Execution, Workspace e Memory Foundation. Memory possui
contrato oficial e repository volátil em memória, sem persistência, embeddings
ou IA. Knowledge, Search, Storage e AIRouter são estruturas vazias ou planejadas.

### Agents

Compõem capacidades por contratos oficiais. Não acessam persistência diretamente
e não acoplam o Kernel a fornecedores. Ainda não há Agent funcional aprovado.

### Tests

Protegem contratos, comportamento e compatibilidade. Testes não substituem
Blueprints nem decisões arquiteturais.

## Conceitos planejados, não implementados

Persistência, Services de infraestrutura e Storage dependem de Blueprint e
review arquitetural antes da criação. A menção no Roadmap não autoriza sua
implementação nem estabelece antecipadamente seus contratos.

## Restrições atuais conhecidas

- Companion local, síncrono e sem autenticação;
- Workspace mantido em memória e compartilhado pela instância local;
- execução de missão sequencial, sem retry, retomada ou persistência;
- Memory isolada por Workspace, volátil e integrada ao Companion;
- apenas FakeProvider, sem rede ou credenciais;
- EventBus síncrono e em memória;

## Fluxo de evolução

```text
Missão → review arquitetural quando necessário → Blueprint → implementação
→ testes → review → Doctor → commit autorizado → push autorizado
```

## Fontes canônicas relacionadas

- Constituição: `Documents/GenesisConstitution.md`;
- autoridade documental: `Documents/ADR/ADR-002-Documentation-Authority.md`;
- roadmap: `Documents/ROADMAP.md`;
- contratos de componentes: `Blueprints/Genesis<Componente>.md`.
