# Blueprint — Genesis Proposal Engine v1

**Versão:** 1.0  
**Status:** proposta de contrato; requer review arquitetural antes da implementação

## Objetivo

Definir o contrato comum para Proposals do Genesis: sugestões estruturadas,
provisórias, revisáveis e rastreáveis que podem orientar uma Decision, sem
produzir consequências antes de `Approve` e `Apply` explícitos.

O Engine deve ser reutilizável por Copilots verticais (incluindo Remodeling) e
manter uma única fonte de verdade para a autoridade, o ciclo de vida e a
prévia das mudanças de uma Proposal.

## Autoridade do agregado e relação com Document

`Proposal` é o agregado comercial oficial. Ele é a única fonte de verdade para
`ProposalStatus`, `Proposal.version`, `ProposalChange`, `ProposalReview`,
`Approve`, `Reject`, `Apply`, idempotência, `ProposalApplyPlan` e
`ProposalApplyReport`.

`Document` é o agregado editorial oficial, definido em
`Blueprints/GenesisDocumentEngine.md`. Ele é a única fonte de verdade para
estrutura documental, seções, templates, branding, metadados documentais,
status editorial, snapshots, `DocumentVersion`, preview estruturado e futura
renderização.

Proposal não herda de Document. Uma Proposal pode conter um `document_id`
opcional e retrocompatível, sem alterar o significado dos campos comerciais.
A integração futura é unidirecional e explícita:

```text
Proposal → ProposalDocumentAdapter → Document
```

O adapter não sincroniza estados ou versões automaticamente de volta para
Proposal. Template e branding pertencem ao Document Engine; Proposal não
absorve lógica visual.

## Decisão arquitetural necessária

Hoje `GenesisRemodelingCopilot.md` descreve transições e modelos de Proposal
dentro do Remodeling Engine. Este Blueprint propõe extrair o contrato comum
para `Engines/Proposal/`. Nenhuma implementação deve começar antes de review
que confirme a migração. Até essa decisão:

- o contrato existente do Remodeling permanece compatível;
- não se cria uma segunda implementação paralela de estados ou aplicação;
- a migração deve ser aditiva, com adapters e testes de regressão;
- o Core, a CLI e os contratos de `Mission`, `Project` e `Memory` permanecem
  inalterados.

## Localização arquitetural

As regras de Proposal pertencem a `Engines/Proposal/`. A coordenação com
Intelligence, Mission, Project e Memory pertence à Application Layer. Interfaces
apenas traduzem entradas e apresentam resultados.

```text
Interface → ProposalApplicationService → ProposalEngine
                                      ├→ Intelligence (contexto/origem)
                                      ├→ MissionApplicationService (prévia)
                                      ├→ ProjectService (prévia)
                                      └→ MemoryService (prévia)
```

O Engine não acessa repositories, HTTP, rede, providers, SDKs ou outros
Engines. Ele recebe dados já reunidos pela Application e devolve modelos
imutáveis ou `Core.result.Result`.

## Vocabulário e autoridade

- **Proposal:** sugestão editável, sem autoridade para alterar dados.
- **Review:** compreensão, comparação e edição antes da decisão.
- **Approve:** decisão explícita que autoriza a Proposal; não aplica efeitos.
- **Apply:** execução de uma mudança já aprovada, com prévia e relatório.
- **Recommendation:** direção preferida com razão, Confidence, concessões e
  alternativas.
- **Assumption:** premissa provisória, sempre visível e revisável.
- **Risk:** consequência possível, com impacto e mitigação quando conhecida.
- **Source:** origem do contexto, da evidência ou da resposta utilizada.

Uma Proposal nunca é tratada como Decision, Knowledge, Memory ou fato do
domínio antes de `Apply` concluído.

## Ciclo de vida

```text
DRAFT → GENERATED → REVIEWED → APPROVED → APPLIED
                         └──────────────→ REJECTED
APPROVED ───────────────→ APPLY_FAILED (relatório preservado)
```

### Estados

- `DRAFT`: estrutura criada, ainda editável e sem conteúdo gerado obrigatório;
- `GENERATED`: conteúdo estruturado produzido a partir de contexto e origem;
- `REVIEWED`: uma pessoa examinou ou alterou a Proposal;
- `APPROVED`: decisão explícita registrada com versão aprovada;
- `REJECTED`: rejeitada antes de Apply, com motivo opcional;
- `APPLIED`: todas as mudanças autorizadas foram efetivadas;
- `APPLY_FAILED`: Apply falhou parcial ou totalmente; o relatório identifica
  cada item e a Proposal não volta automaticamente a `APPROVED`.

Somente `DRAFT`, `GENERATED` e `REVIEWED` aceitam edição de conteúdo. Uma
Proposal `APPROVED` é imutável; correções exigem uma nova revisão ou uma nova
versão derivada. `APPLIED` é terminal. `APPLY_FAILED` permite recuperação
explícita e idempotente, nunca uma nova aplicação implícita.

## Modelos públicos imutáveis

Todos os modelos usam UUID textual, datas UTC com fuso horário e coleções em
tuplas ou mapas imutáveis. Textos são normalizados sem alterar o significado.

### `Proposal`

Agregado principal com:

- `id`, `version` e `created_at`;
- `document_id` opcional, aditivo e retrocompatível, quando existir uma
  representação editorial associada;
- `workspace_id` obrigatório e `project_id` opcional;
- `mission_id` opcional quando a Proposal nasce de uma Mission;
- `title`, `objective` e `summary` obrigatórios após geração;
- `status` (`ProposalStatus`);
- `recommendation` (`Recommendation` opcional);
- `changes` (`ProposalChange` ordenadas e identificadas);
- `assumptions`, `risks`, `missing_information` e `sources`;
- `confidence` em escala controlada (`LOW`, `MEDIUM`, `HIGH`) com justificativa;
- `created_by` (`USER`, `GENESIS`, `MANUAL_HANDOFF`);
- `approved_at`, `approved_by`, `applied_at` e `rejection_reason` opcionais.

`document_id` é apenas um vínculo. `workspace_id`, `project_id`, `mission_id` e
as demais relações comerciais continuam oficiais no agregado Proposal;
`DocumentMetadata` pode referenciá-las para rastreabilidade, mas não as
substitui. A Sprint 1 pode permanecer sem esse campo; sua inclusão futura deve
ser opcional, aditiva e compatível com os construtores e consumidores existentes.

### `ProposalChange`

Prévia declarativa de uma mudança, sem efeito por si só:

- `id` e `order` únicos dentro da Proposal;
- `target_type` controlado pelo consumidor do domínio;
- `target_id` opcional para criação ou obrigatório para atualização;
- `action` (`CREATE`, `UPDATE`, `ASSOCIATE`, `ARCHIVE`);
- `summary` legível, `before` opcional, `after` opcional e `reversible`;
- `dependencies`, referindo somente mudanças existentes na mesma Proposal.

`before` e `after` são dados de prévia, não comandos. O Engine rejeita
dependências inválidas, ciclos, IDs duplicados e combinações sem alvo ou sem
conteúdo suficiente.

### `ProposalSource`

Registra `kind`, `label`, `reference`, `captured_at` e `workspace_id`. A
referência não pode conter credenciais, cookies, tokens ou conteúdo secreto.
Fontes de outro Workspace são rejeitadas.

### `ProposalReview`

Registra `id`, `proposal_id`, `proposal_version`, `reviewer`, `decision`,
`notes`, `changed_change_ids` e `created_at`. `decision` pode ser `COMMENTED`,
`ACCEPTED`, `REQUESTED_CHANGES` ou `REJECTED`.

### `ProposalApplyPlan` e `ProposalApplyReport`

`ProposalApplyPlan` é uma prévia imutável gerada somente para Proposal aprovada,
com mudanças ordenadas e dependências resolvidas. `ProposalApplyReport`
registra `APPLIED`, `SKIPPED`, `FAILED` ou `ROLLED_BACK` por mudança, além do
estado final, motivo seguro e timestamp. O relatório nunca inclui mensagens
brutas de exceções ou segredos.

## Contrato do Engine

```python
engine.create_draft(
    workspace_id=workspace_id,
    title=title,
    objective=objective,
    project_id=project_id,
    mission_id=mission_id,
) -> Result[Proposal]

engine.record_generation(
    proposal=proposal,
    summary=summary,
    recommendation=recommendation,
    changes=changes,
    assumptions=assumptions,
    risks=risks,
    missing_information=missing_information,
    sources=sources,
    confidence=confidence,
) -> Result[Proposal]

engine.review(proposal, review) -> Result[Proposal]
engine.approve(proposal, reviewer, notes="") -> Result[Proposal]
engine.reject(proposal, reviewer, reason) -> Result[Proposal]
engine.build_apply_plan(proposal) -> Result[ProposalApplyPlan]
engine.validate_apply_report(proposal, report) -> Result[Proposal]
```

O Engine não executa `ProposalApplyPlan`. A Application Service passa cada
mudança a um adapter explícito do domínio, preservando o controle e a
idempotência. Todas as falhas de validação retornam `Result.error`; exceções de
adapters são convertidas em `ProposalApplyReport` seguro.

## Versionamento e status separados

`Proposal.version` e `DocumentVersion.version` são contadores independentes:

- `Proposal.version` representa evolução comercial e decisória;
- `DocumentVersion.version` representa evolução editorial e visual.

Todo `DocumentVersion` derivado de uma Proposal deve registrar
`source_proposal_id`, `source_proposal_version`, `template_id`,
`template_version`, `brand_profile_id` e `brand_profile_version` ou snapshot
equivalente. Uma versão documental não altera a versão da Proposal.

`DocumentStatus` nunca substitui `ProposalStatus`. Um eventual
`DocumentStatus.APPROVED` significa somente aprovação editorial e nunca autoriza
Proposal Apply. O domínio Document não possui estado `APPLIED`.

`ProposalReview` permanece a revisão comercial oficial. Revisões editoriais
ocorrem por nova `DocumentVersion` ou eventos editoriais, sem criar uma segunda
`ProposalReview`.

## Regras e invariantes

1. `workspace_id` é obrigatório em toda Proposal e em toda Source.
2. IDs, ordens, títulos e objetivos não podem ser vazios ou duplicados.
3. Uma Proposal gerada deve declarar contexto, fontes e lacunas conhecidas.
4. `HIGH` Confidence exige justificativa não vazia; Confidence nunca é certeza.
5. A existência de `Recommendation` não obriga o usuário a segui-la.
6. `Approve` exige estado `REVIEWED` e identidade explícita do aprovador.
7. `Apply` exige estado `APPROVED`, versão aprovada e plano confirmado.
8. Nenhuma mudança é aplicada automaticamente ao gerar, revisar ou aprovar.
9. Uma mudança só pode ser aplicada uma vez; retries seguros usam seu `id`.
10. Apply parcial preserva o que ocorreu, separa concluído e não concluído e
    nunca declara `APPLIED` sem todas as mudanças concluídas.
11. Dados de outro Workspace, dependências cíclicas e payloads incompatíveis
    são rejeitados antes de qualquer efeito.
12. Uma Proposal rejeitada não pode ser aprovada ou aplicada; deve ser derivada
    para nova versão.

## Application Service

`ProposalApplicationService` coordena:

- criação e consulta volátil de Proposals da instância;
- montagem do contexto por contratos públicos existentes;
- geração via Intelligence `FREE_ONLY` ou `ManualHandoff`, quando aplicável;
- registro de Review e aprovação explícita;
- construção da prévia de Apply;
- execução através de adapters de `Mission`, `Project` e `Memory`;
- relatório de Apply e recuperação explícita após falha.

O serviço não duplica validações do Engine, não acessa repositories diretamente
e não transforma sugestões em Memory, Mission ou Project antes de Apply.

## Eventos opcionais

Quando houver semântica aprovada, a Application pode publicar eventos
`ProposalCreated`, `ProposalReviewed`, `ProposalApproved`, `ProposalApplied` ou
`ProposalApplyFailed` pelo EventBus. Eventos são informativos; a consistência
do contrato síncrono não depende deles e a falha de um listener não interrompe
o fluxo principal.

## Integração com Remodeling

O Remodeling Copilot deve continuar expondo seu fluxo e rotas públicas. Após o
review arquitetural, `RemodelingApplicationService` usará o Proposal Engine
para lifecycle, mudanças, revisão e Apply, mantendo no Remodeling somente as
regras específicas de brief, orçamento e parser. A migração deve preservar:

- `DRAFT → GENERATED → REVIEWED → APPROVED → APPLIED`;
- orçamento como estimativa preliminar, recalculada deterministicamente;
- aprovação separada de Apply;
- aplicação idempotente em Mission, Project e Memory;
- respostas e relatórios voláteis na v1.

## Segurança, privacidade e acessibilidade

- nenhuma rede, scraping, browser automation, SDK de provider ou credencial;
- respostas manuais e payloads são tratados como dados, nunca executados;
- logs registram tipos de falha e IDs, não conteúdo sensível;
- fronteiras de Workspace são verificadas em todas as relações;
- a Interface deve expor estado, origem, Confidence, Risk, consequência,
  reversibilidade e próxima ação em linguagem clara;
- Review, Pause, Stop e recuperação devem ser acessíveis por teclado e leitor
  de tela, com foco visível e movimento reduzido.

## Fora do escopo da v1

- persistência de Proposal, versionamento distribuído ou colaboração em tempo
  real;
- aplicação genérica por reflexão, plugins arbitrários ou execução de código;
- aprovação automática, execução autônoma, providers reais ou rede;
- cálculo financeiro, impostos, contratos comerciais ou garantia de resultado;
- replanejamento automático, undo universal ou transações distribuídas;
- alterações em Core, CLI, Registry, AIOrchestrator ou contratos de domínio.
- lógica de template, branding ou renderização no Proposal Engine;
- renderers de PDF, DOCX, HTML, impressão, e-mail ou portal do cliente.

## Testes obrigatórios

- modelos imutáveis, normalização e isolamento por Workspace;
- transições válidas e rejeição de transições inválidas;
- edição bloqueada após Approve e estados terminais;
- validação de IDs, ordens, dependências e ciclos;
- preservação de Source, Confidence, Risk, Assumption e versão aprovada;
- Apply plan determinístico e relatório de sucesso, falha e parcialidade;
- idempotência por `change_id` e ausência de efeitos antes de Apply;
- payload malformado, dados cross-Workspace e exceções sem vazamento;
- integração do Remodeling e compatibilidade das rotas existentes;
- suíte completa e Genesis Doctor no review da implementação.

## Critérios de conclusão

- [ ] review arquitetural aprova a extração e a fonte única de Proposal;
- [ ] contratos e modelos imutáveis implementados em `Engines/Proposal/`;
- [ ] lifecycle Proposal → Review → Approve → Apply coberto por testes;
- [ ] prévia declarativa e relatório de Apply implementados;
- [ ] Application Service integra Intelligence e adapters de domínio;
- [ ] Remodeling migra sem quebra de contratos ou rotas;
- [ ] nenhuma ação ocorre antes de aprovação e confirmação de Apply;
- [ ] falhas parciais são seguras, explícitas e recuperáveis;
- [ ] documentação, suíte completa e Doctor revisados antes do commit.
