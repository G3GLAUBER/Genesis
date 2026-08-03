# Blueprint — Genesis AI Orchestrator

**Versão:** 2.0

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
Ordem de prioridade
    ↓
Registry → AIProvider compatível → Result[AIResponse]
```

O AI Orchestrator é distinto do Orchestrator do Kernel. O primeiro coordena
geração de inteligência dentro do Engine; o segundo coordena comandos gerais do
sistema e não conhece provedores.

## Configuração e prioridade

O construtor recebe o `Registry` compartilhado e uma ordem explícita de
providers. A ordem é determinística e definida pela composição do sistema, não
pelo usuário nem pelo `AIRequest`:

```python
orchestrator = AIOrchestrator(
    registry=registry,
    provider_ids=("primary", "secondary"),
)
```

O primeiro provider compatível que retornar sucesso vence. Não há pontuação,
custo, benchmark ou decisão baseada em IA.

### Compatibilidade com v1

O argumento `provider_id` continua aceito para o uso antigo com um único
provider:

```python
orchestrator = AIOrchestrator(
    registry=registry,
    provider_id="fake",
)
```

`provider_id` e `provider_ids` são mutuamente exclusivos.

## Interface pública

```python
orchestrator = AIOrchestrator(
    registry=registry,
    provider_ids=("primary", "secondary"),
)

result = orchestrator.generate(request)
```

O método aditivo `generate_with_order(request, provider_ids)` reutiliza o mesmo
pipeline de execução para uma ordem produzida pelo Intelligence Router. Ele não
altera a ordem configurada nem a compatibilidade de `generate(request)`.

`generate()` deve:

1. receber um `AIRequest`;
2. percorrer os providers na ordem configurada;
3. ignorar providers que não suportem `request.capability`;
4. validar tipo e identidade de cada item encontrado;
5. executar `provider.generate(request)` nos compatíveis;
6. retornar imediatamente no primeiro `Result.success` válido;
7. continuar após `Result.error` ou exceção inesperada;
8. retornar `Result.error` estruturado se nenhum provider tiver sucesso.

Em caso de sucesso, `Result.data` contém `AIResponse` e seu `provider_id`
identifica o provider vencedor.

## Seleção por capacidade

Somente providers que declarem `request.capability` em `capabilities` são
executados. Providers incompatíveis são ignorados e não contam como tentativa
de geração.

## Fallback

O fallback é sequencial e determinístico:

- `Result.success`: encerra imediatamente;
- `Result.error`: registra a tentativa e continua;
- exceção inesperada: registra somente o tipo da exceção e continua;
- retorno fora do contrato: registra falha de contrato e continua.

Nenhum provider posterior é executado depois de um sucesso.

## Falha total

Falhas totais usam `Result.error` com `AIOrchestrationFailure` em `data`.
Essa estrutura contém a capacidade solicitada e uma tupla ordenada de
`AIProviderAttempt`. Cada tentativa registra:

- `provider_id`;
- `outcome` controlado;
- `error_type` apenas para exceções inesperadas.

Mensagens brutas de exceções e dados internos do provider não entram no
histórico, evitando exposição acidental de segredos.

## Responsabilidades

- ocultar providers dos consumidores;
- resolver providers na prioridade configurada;
- selecionar somente providers compatíveis;
- validar contrato e capacidade antes da execução;
- executar fallback sequencial;
- produzir histórico seguro de falhas;
- manter retorno padronizado com `Result`;
- permanecer independente de SDKs e rede.

## Fora do escopo

- retentativas;
- execução paralela;
- seleção automática por custo, latência ou qualidade;
- rede e integrações reais;
- alterações no Kernel ou na CLI.

## Evolução futura

O método público `generate(request)` deve permanecer estável. Se a seleção
passar a considerar custo, latência, qualidade ou saúde, a ordenação poderá ser
extraída para uma política injetável. Paralelismo exigirá contrato assíncrono e
regra de agregação. Nenhuma dessas abstrações é necessária nesta versão.

## Critérios de conclusão

- [x] fachada única para consumidores;
- [x] múltiplos providers pelo Registry;
- [x] prioridade explícita e determinística;
- [x] seleção por capacidade;
- [x] fallback sequencial;
- [x] exceções convertidas em falhas controladas;
- [x] histórico estruturado de tentativas;
- [x] compatibilidade com provider_id da v1;
- [x] validação do contrato AIProvider;
- [x] validação da identidade do provider;
- [x] retorno padronizado com Result;
- [x] testes automatizados;
- [x] nenhuma alteração no Kernel ou na CLI.
