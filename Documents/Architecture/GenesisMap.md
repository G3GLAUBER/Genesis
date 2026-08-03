> **Status: Superseded.** Este mapa representa uma visão planejada antiga. A
> arquitetura e o estado atual canônicos estão em `Documents/ARCHITECTURE.md`.

# Mapa histórico do Gênesis

```mermaid
flowchart TD

    G[Genesis]

    G --> Core
    G --> Services
    G --> Agents
    G --> Interfaces
    G --> Data
    G --> Documents
    G --> Tests

    Core --> EventBus
    Core --> Registry
    Core --> Dispatcher
    Core --> Lifecycle

    Services --> Memory
    Services --> Knowledge
    Services --> Search
    Services --> Storage
    Services --> AIRouter

    Interfaces --> Companion
    Interfaces --> Browser
    Interfaces --> CLI
    Interfaces --> API

    Agents --> CEO
    Agents --> CTO
    Agents --> CKO
    Agents --> CFO

    EventBus --> Memory
    EventBus --> Knowledge
    EventBus --> AIRouter

    Memory --> Data
    Knowledge --> Data

```
