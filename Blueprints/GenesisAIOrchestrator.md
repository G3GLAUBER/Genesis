# Blueprint — Genesis AI Orchestrator

**Versão:** 1.0

## Objetivo

Ser o único ponto de entrada para geração de inteligência no Gênesis. Nenhum
consumidor deve localizar ou executar um `AIProvider` diretamente.

## Localização arquitetural

O `AIOrchestrator` pertence a `Engines/AI/`. Ele coordena contratos do próprio
Engine e reutiliza `Registry` e `Result` do Core sem criar dependências do Core
para Engines.

```text
Consumidor
    ↓
AIOrchestrator
    ↓
Registry → AIProvider → Result[AIResponse]
```

O AI Orchestrator é distinto do Orchestrator do Kernel. O primeiro coordena
geração de inteligência dentro do Engine; o segundo coordena comandos gerais do
sistema e não conhece provedores.

## Configuração

Nesta versão, o construtor recebe:

- o `Registry` compartilhado;
- um único `provider_id` configurado explicitamente.

Não há seleção dinâmica. O identificador apenas determina qual provider será
resolvido para todas as solicitações dessa instância.

## Interface pública

```python
orchestrator = AIOrchestrator(
    registry=registry,
    provider_id="fake",
)

result = orchestrator.generate(request)
```

`generate()` deve:

1. receber um `AIRequest`;
2. localizar o item configurado no `Registry`;
3. validar que o item implementa `AIProvider`;
4. validar que `provider.provider_id` corresponde à chave configurada;
5. validar que o provider suporta `request.capability`;
6. executar `provider.generate(request)`;
7. devolver o `Result` produzido pelo provider.

Em caso de sucesso, `Result.data` contém `AIResponse`. Falhas esperadas de
resolução e validação retornam `Result.error`. Falhas controladas do provider
são propagadas sem alteração.

## Responsabilidades

- ocultar providers dos consumidores;
- resolver o provider configurado;
- validar contrato e capacidade antes da execução;
- manter retorno padronizado com `Result`;
- permanecer independente de SDKs e rede.

## Fora do escopo

- múltiplos providers por instância;
- fallback;
- retentativas;
- execução paralela;
- seleção automática por capacidade, custo ou qualidade;
- rede e integrações reais;
- alterações no Kernel ou na CLI.

## Evolução futura

O método público `generate(request)` deve permanecer estável. Estratégias de
seleção, fallback e execução poderão ser adicionadas atrás dessa fachada por
meio de contratos específicos, após Blueprint e revisão arquitetural, sem
expor providers aos consumidores.

## Critérios de conclusão

- [x] fachada única para consumidores;
- [x] resolução pelo Registry;
- [x] validação do contrato AIProvider;
- [x] validação da identidade do provider;
- [x] validação de capacidade;
- [x] delegação de geração;
- [x] retorno padronizado com Result;
- [x] testes automatizados;
- [x] nenhuma alteração no Kernel ou na CLI.
