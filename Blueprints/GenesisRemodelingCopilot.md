# Blueprint — Genesis Remodeling Copilot v0.1

## Objetivo

Oferecer o primeiro fluxo vertical especializado do Genesis para preparar,
revisar e aplicar propostas de remodelação sem transformar conteúdo de IA em
dados definitivos sem aprovação humana explícita.

## Arquitetura

```text
Companion → RemodelingApplicationService → RemodelingEngine
                         ├→ IntelligenceApplicationService → ManualHandoff
                         ├→ MissionApplicationService
                         ├→ ProjectService
                         └→ MemoryService
```

O Engine contém validação do brief, identificação de lacunas, parser JSON,
cálculo determinístico do orçamento e transições da proposta. Application
coordena os contratos existentes. A Interface apenas traduz HTTP e HTML.

## Fluxo de aprovação

```text
DRAFT → GENERATED → REVIEWED → APPROVED → APPLIED
                         └──────────────→ REJECTED
```

Somente propostas `APPROVED` podem ser aplicadas. A aplicação é idempotente:
uma proposta `APPLIED` não pode criar dados novamente. Conteúdo gerado nunca
cria Mission ou Memory antes da confirmação explícita.

## Resposta manual

O handoff solicita JSON com `phases`, `risks`, `missing_information`,
`suggested_missions`, `suggested_memories`, `preliminary_budget` e
`assumptions`. Dependências de fases referem ordens inteiras existentes. O
parser usa somente `json`, valida tipos, rejeita conteúdo incompatível e
preserva a resposta bruta. Não usa `eval`, pickle, rede ou automação.

## Orçamento preliminar

Valores são opcionais e sempre marcados como estimativas. O Genesis recalcula
linhas com quantidade e preço unitário, subtotal, contingência e total usando
aritmética decimal. Não calcula impostos nem apresenta o resultado como preço
final ou proposta comercial.

## Persistência e limites

Briefs, propostas, respostas e relatórios de aplicação são voláteis nesta
versão. Workspace, Project e Memory reutilizam seus repositories atuais;
Mission continua volátil. Não há provider real, scraping, navegador, preços
externos, upload, pagamentos, contrato, fiscalidade ou aprovação automática.

## Critérios de conclusão

- [x] modelos imutáveis e validação de brief;
- [x] lacunas não essenciais identificadas sem bloquear geração;
- [x] roteamento exclusivamente `FREE_ONLY` e ManualHandoff;
- [x] parser JSON seguro e resposta bruta preservada;
- [x] orçamento preliminar recalculado pelo Genesis;
- [x] lifecycle com revisão e aprovação explícitas;
- [x] aplicação idempotente em Mission, Project e Memory;
- [x] Companion e rotas integrados sem quebrar APIs anteriores;
- [x] nenhuma alteração em Core ou CLI.
