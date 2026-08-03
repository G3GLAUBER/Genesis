# Blueprint — Genesis Intelligence Engine v0.1

## Objetivo

Selecionar de forma determinística e explicável o melhor provider configurado,
priorizando recursos locais, gratuitos ou já disponíveis antes de recursos
pagos. A versão v0.1 não usa IA para escolher IA e não verifica serviços pela
rede.

## Arquitetura

```text
Interface → IntelligenceApplicationService → IntelligenceRouter
                                      ├→ ProviderCatalog
                                      ├→ ManualHandoffManager
                                      └→ AIOrchestrator → AIProvider
```

`ProviderCatalog` mantém somente perfis de configuração. Ele não reutiliza o
`Core.registry.Registry`, pois o Registry contém implementações executáveis e o
catálogo também descreve providers manuais ou desabilitados. O
`AIOrchestrator` continua sendo o único executor de providers automáticos.

## Modelos

- `ProviderProfile`: identidade, capabilities, acesso, custo, disponibilidade
  configurada, prioridade e notas;
- `RoutingDecision`: provider selecionado, modo, justificativa, alternativas e
  necessidade de handoff manual;
- `ManualHandoff`: prompt e resposta manual imutáveis, com relações opcionais
  para Workspace, Project e Mission;
- `IntelligenceMetricsSnapshot`: contadores locais imutáveis.

## Política Free First

Somente profiles habilitados e compatíveis participam. `FREE_ONLY` exclui
sempre `PAID`; `LOCAL_FIRST` posiciona acesso `LOCAL` antes dos demais;
`ECONOMY` ordena por faixa de custo. Empates usam prioridade e `provider_id`,
garantindo decisão determinística. `BALANCED` e `MAX_QUALITY` usam a prioridade
configurada nesta versão, pois ainda não existem métricas reais de qualidade.

## Manual Handoff

Providers `MANUAL` geram um fluxo para o usuário copiar o prompt, utilizar a
conta por iniciativa própria e colar a resposta. O Genesis não abre sites, não
usa clipboard, cookies, sessões, scraping, login ou endpoints não oficiais. A
resposta concluída pode ser armazenada como Memory quando houver Workspace.

## Perfis iniciais

Perfis demonstrativos usam identificadores genéricos. Perfis de API, pago e
local sem executor começam desabilitados e não representam disponibilidade
real. O `FakeProvider` local permanece habilitado apenas para desenvolvimento.
Nenhuma credencial ou limite diário é armazenado.

## Limites

- sem rede, providers reais, cobrança, embeddings ou aprendizado;
- handoffs e métricas são voláteis e locais à composição;
- sem persistência de preferências de roteamento;
- sem paralelismo ou benchmark real.
