# Blueprint — Genesis AI Providers

**Versão:** 1.0

## Objetivo

Definir uma base independente de fornecedor para integrar provedores de
inteligência ao Gênesis sem acoplar o Kernel, os Agents ou os consumidores a
SDKs e APIs específicas.

## Localização arquitetural

Os contratos e adapters de provedores pertencem a `Engines/AI/`. O Core não
depende dessa camada. Implementações concretas dependem dos contratos do Engine
e podem usar componentes estáveis do Core, como `Result` e `Registry`.

```text
Consumidor → AIProvider → implementação concreta
                         ↓
                       Result
```

## Estruturas de dados

### AIRequest

Estrutura imutável com:

- `prompt`: entrada textual;
- `capability`: capacidade solicitada.

### AIResponse

Estrutura imutável com:

- `provider_id`: provedor que produziu a resposta;
- `content`: conteúdo gerado;
- `capability`: capacidade utilizada.

## Contrato AIProvider

Todo provedor deve implementar:

```python
provider.provider_id
provider.capabilities
provider.generate(request)
```

- `provider_id` identifica unicamente o provedor;
- `capabilities` retorna uma tupla imutável de capacidades;
- `generate()` recebe `AIRequest` e retorna `Result`;
- sucesso usa `Result.success` com `AIResponse` em `data`;
- falhas esperadas usam `Result.error`, sem lançar exceções para o consumidor.

## Registry

O `Core.registry.Registry` será reutilizado:

```python
registry.register(provider.provider_id, provider)
provider = registry.get(provider_id)
```

Não será criado um Provider Registry nesta versão. O Registry atual já possui
responsabilidade genérica de registro e descoberta, além de contratos para
duplicidade e ausência. Um registro específico duplicaria comportamento e
criaria outra fonte de verdade sem necessidade atual.

Se requisitos futuros exigirem validação de tipo, aliases, prioridade, seleção
por capacidade ou descoberta dinâmica, a decisão deverá ser revisada antes da
implementação.

## FakeProvider

O `FakeProvider` é determinístico, não usa rede, credenciais ou SDK externo e
existe apenas para testes e desenvolvimento. Deve suportar sucesso e falha
controlada por configuração.

## Fora do escopo

- integrações com OpenAI, Anthropic, Gemini ou outros fornecedores;
- chamadas de rede;
- credenciais e configuração de APIs;
- seleção automática, fallback ou balanceamento entre provedores;
- alterações na CLI, no Orchestrator ou em outros componentes do Kernel.

## Critérios de conclusão

- [x] `AIRequest` e `AIResponse` imutáveis;
- [x] contrato abstrato `AIProvider`;
- [x] identificação e capacidades do provedor;
- [x] retorno padronizado com `Result`;
- [x] reutilização documentada do Registry;
- [x] FakeProvider sem rede;
- [x] testes automatizados.
