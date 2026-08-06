# Plano de implementação — Genesis Proposal Engine v1

**Blueprint de origem:** `Blueprints/GenesisProposalEngine.md`  
**Versão do plano:** 1.0  
**Status:** plano executável condicionado a review arquitetural  
**Escopo:** implementação incremental do contrato de Proposal, sem alterações
no Core, CLI ou contratos públicos existentes.

## Como usar este plano

Os Sprints são sequenciais. Um Sprint só começa quando o anterior estiver
aceito e a definição de pronto estiver satisfeita. O desenvolvedor deve seguir
os nomes, assinaturas, estados e limites deste documento; qualquer divergência
exige review arquitetural e atualização do Blueprint de origem antes de código.

Não implementar nada enquanto o Sprint 0 não receber aprovação explícita do
review arquitetural. Cada mudança deve permanecer restrita aos arquivos
permitidos no Sprint corrente. Não criar arquivos de compatibilidade, APIs ou
abstrações não listadas aqui.

## Contrato congelado para a implementação

### Localização e direção de dependências

```text
Interface → Application.services.ProposalApplicationService →
Engines.Proposal.ProposalEngine → Core.result.Result
```

`Engines/Proposal/` é domínio puro. Não importa Application, Interfaces,
Companion, HTTP, repositories, providers, SDKs ou rede. A Application compõe
contexto e chama adapters oficiais de Mission, Project e Memory sem duplicar
suas regras.

`Proposal` é o agregado comercial oficial. A relação editorial é opcional e
unidirecional, por adapter futuro:

```text
Proposal → ProposalDocumentAdapter → Document
```

`document_id`, quando adicionado, será opcional e retrocompatível. Não haverá
herança Proposal–Document, sincronização bidirecional automática ou substituição
de `Proposal.version` por `DocumentVersion.version`. Template, branding,
seções e status editorial pertencem exclusivamente ao Document Engine.

### Estados e transições

```text
DRAFT → GENERATED → REVIEWED → APPROVED → APPLIED
                         └──────────────→ REJECTED
APPROVED ───────────────→ APPLY_FAILED
```

Transições válidas:

| Origem | Operação | Destino |
|---|---|---|
| nenhuma | `create_draft` | `DRAFT` |
| `DRAFT` | `record_generation` | `GENERATED` |
| `GENERATED` ou `REVIEWED` | edição/review | `REVIEWED` |
| `REVIEWED` | `approve` | `APPROVED` |
| `DRAFT`, `GENERATED` ou `REVIEWED` | `reject` | `REJECTED` |
| `APPROVED` | Apply completo | `APPLIED` |
| `APPROVED` | Apply parcial/falho | `APPLY_FAILED` |

`APPROVED` é snapshot imutável. `APPLIED` é terminal. `REJECTED` não pode ser
aprovado nem aplicado. Recuperação de `APPLY_FAILED` é explícita e usa os
`change_id` já concluídos; não há retry automático.

### APIs públicas congeladas

```python
ProposalEngine.create_draft(
    workspace_id: str,
    title: str,
    objective: str,
    project_id: str | None = None,
    mission_id: str | None = None,
) -> Result[Proposal]

ProposalEngine.record_generation(
    proposal: Proposal,
    summary: str,
    recommendation: Recommendation | None,
    changes: Sequence[ProposalChange],
    assumptions: Sequence[str],
    risks: Sequence[str],
    missing_information: Sequence[str],
    sources: Sequence[ProposalSource],
    confidence: Confidence,
) -> Result[Proposal]

ProposalEngine.review(proposal: Proposal, review: ProposalReview) -> Result[Proposal]
ProposalEngine.approve(proposal: Proposal, reviewer: str, notes: str = "") -> Result[Proposal]
ProposalEngine.reject(proposal: Proposal, reviewer: str, reason: str) -> Result[Proposal]
ProposalEngine.build_apply_plan(proposal: Proposal) -> Result[ProposalApplyPlan]
ProposalEngine.validate_apply_report(
    proposal: Proposal, report: ProposalApplyReport
) -> Result[Proposal]
```

O Engine nunca executa o plano. A execução pertence ao
`ProposalApplicationService` e a adapters explícitos.

### Modelos públicos

Todos devem ser `dataclass(frozen=True)`, com UUID textual, `datetime` UTC com
fuso horário e coleções convertidas para tuplas/mapas imutáveis:

- `ProposalStatus`: `DRAFT`, `GENERATED`, `REVIEWED`, `APPROVED`, `REJECTED`,
  `APPLIED`, `APPLY_FAILED`;
- `Confidence`: `LOW`, `MEDIUM`, `HIGH`, sempre com justificativa quando `HIGH`;
- `ProposalAction`: `CREATE`, `UPDATE`, `ASSOCIATE`, `ARCHIVE`;
- `ProposalChange`: `id`, `order`, `target_type`, `target_id`, `action`,
  `summary`, `before`, `after`, `reversible`, `dependencies`;
- `ProposalSource`: `kind`, `label`, `reference`, `captured_at`,
  `workspace_id`;
- `Recommendation`: direção, razão, benefícios, concessões, alternativas e
  Confidence;
- `ProposalReview`: `id`, `proposal_id`, `proposal_version`, `reviewer`,
  `decision`, `notes`, `changed_change_ids`, `created_at`;
- `Proposal`: agregado e campos definidos no Blueprint de origem;
- `ProposalApplyPlan`: snapshot aprovado, mudanças ordenadas e dependências
  resolvidas;
- `ProposalApplyReport`: resultado por mudança (`APPLIED`, `SKIPPED`, `FAILED`,
  `ROLLED_BACK`), estado final, motivo seguro e timestamp.

Falhas de contrato usam `Result.error`; mensagens não incluem exceções brutas,
payloads sensíveis ou credenciais.

O campo `document_id` poderá ser acrescentado ao agregado Proposal somente como
referência opcional. Nenhuma assinatura pública existente, incluindo
`create_draft`, pode ser removida ou ter sua semântica alterada.

## Ordem inter-Blueprint congelada

Após a Sprint 1 já implementada, a ordem segura de evolução é:

1. congelamento documental da relação Proposal–Document;
2. lifecycle comercial e Apply do Proposal;
3. fundação pura do Document Engine;
4. adapter unidirecional Proposal → Document;
5. `DocumentApplicationService` e composição pela Application;
6. integração de contexto com Projects, Workflow, Mission Copilot e Memory;
7. migração controlada do Remodeling;
8. integração de apresentação no Companion;
9. renderers futuros, fora do domínio.

O Document Engine não deve antecipar o adapter nem alterar a Sprint 1 do
Proposal. O adapter só pode ser implementado depois de ambos os contratos
estarem congelados.

---

## Sprint 0 — Gate arquitetural e contrato executável

### Objetivo

Confirmar que a extração de Proposal não cria duas fontes de verdade e congelar
o contrato que os Sprints seguintes implementarão.

Este gate também congela que Proposal possui o lifecycle comercial e Document
possui o lifecycle editorial, com versões independentes e vínculo opcional por
`document_id`.

### Escopo permitido

- revisar o Blueprint de origem contra Architecture, ADRs e Remodeling;
- registrar a decisão de extração e a estratégia de adapter em review;
- transformar as tabelas e assinaturas deste plano em checklist de implementação;
- identificar consumidores atuais do Remodeling sem alterar seus contratos.

### Escopo proibido

- qualquer código de `Engines/Proposal/`;
- qualquer migração do Remodeling;
- alterar Blueprint, Architecture, ADR, código ou testes existentes;
- introduzir persistência, eventos obrigatórios ou novas rotas.

### Arquivos permitidos

- Nenhum arquivo do repositório deve ser alterado neste Sprint.
- Artefatos de review devem ser externos ao repositório ou aprovados pelo
  processo de governança vigente.

### APIs públicas

Nenhuma API nova. As assinaturas congeladas neste plano são apenas referência
para o review.

### Modelos

Nenhum modelo implementado. Confirmar nomes, campos, estados e imutabilidade.

### Serviços

Nenhum serviço implementado. Confirmar que Application será a única composição.

### Companion

Nenhuma rota ou template alterado. Confirmar que rotas existentes do Remodeling
continuarão funcionando durante a migração.

### Testes

Nenhum teste alterado. O review deve listar testes existentes de Remodeling e
consumidores que exigirão regressão.

### Critérios de aceite

- decisão explícita aprova a fonte única `Engines/Proposal/` ou rejeita a
  extração;
- compatibilidade do Remodeling, Application e Companion está mapeada;
- não há contrato conflitante entre este plano e o Blueprint de origem;
- Sprints 1–5 estão autorizados sem interpretação adicional.

### Riscos

- duplicação do lifecycle entre Proposal e Remodeling;
- migração que quebre rotas ou modelos públicos existentes;
- escopo indevido em Core ou persistência.

### Validações

- revisão documental na ordem constitucional definida por ADR-002;
- inspeção dos consumidores e testes de Remodeling;
- confirmação de que a mudança é compatível com a fase atual do Roadmap.

### Definição de pronto

Review arquitetural aprovado, decisão registrada pelo mecanismo oficial e
nenhuma alteração de arquivo no repositório.

---

## Sprint 1 — Modelos, enums e validação pura

### Objetivo

Implementar os modelos imutáveis e todas as validações estruturais sem efeitos
colaterais.

### Escopo permitido

- criar `Engines/Proposal/` e seus módulos de modelos/validação;
- implementar enums, dataclasses congeladas, normalização e validação;
- implementar `ProposalEngine.create_draft`;
- reutilizar somente `Core.result.Result` e biblioteca padrão.

### Escopo proibido

- lifecycle além de `DRAFT`;
- Application, Companion, HTTP, repositories, SQLite ou EventBus;
- IA, providers, parsing de resposta externa ou execução de mudanças;
- alterar Remodeling ou qualquer contrato existente.

### Arquivos permitidos

- `Engines/Proposal/__init__.py`;
- `Engines/Proposal/models.py`;
- `Engines/Proposal/validation.py`;
- `Engines/Proposal/engine.py`;
- `Tests/test_proposal_models.py`;
- `Tests/test_proposal_validation.py`.

### APIs públicas

- exportar os modelos listados no contrato congelado;
- `ProposalEngine.create_draft(...)`;
- nenhuma API de aplicação ou rota.

### Modelos

Implementar `Proposal`, `ProposalChange`, `ProposalSource`, `Recommendation`,
`ProposalReview`, `ProposalApplyPlan`, `ProposalApplyReport`, `ProposalStatus`,
`Confidence` e `ProposalAction`. `create_draft` cria UUID, timestamp UTC,
versão inicial `1` e estado `DRAFT`.

### Serviços

Nenhum Application Service. O Engine deve ser instanciável sem dependências ou
com dependências somente de `Result`.

### Companion

Sem alteração de rotas, views, estilos ou bootstrap.

### Testes

- imutabilidade e normalização;
- UUID e timestamp com timezone;
- campos obrigatórios, Workspace obrigatório e IDs válidos;
- enumerações e coleções imutáveis;
- tentativa de importar Core, Application ou Interfaces pelo Engine deve ser
  ausente (verificação estática ou teste de arquitetura apropriado).

### Critérios de aceite

- objetos não podem ser mutados após criação;
- `workspace_id`, título e objetivo inválidos retornam erro controlado;
- nenhum import produz efeito colateral;
- todos os modelos são construíveis com os campos documentados;
- testes do Sprint passam isoladamente e com a suíte existente.

### Riscos

- mapas `before`/`after` mutáveis escaparem do modelo;
- normalização alterar conteúdo significativo;
- campos divergirem dos consumidores do Remodeling.

### Validações

Executar testes do Sprint, `pytest Tests` e `git diff --check`. Comparar API
exportada com a tabela deste plano antes de avançar.

### Definição de pronto

Modelos e `create_draft` implementados, testes determinísticos aprovados e
nenhuma alteração fora dos arquivos permitidos.

---

## Sprint 2 — Geração, Review, Approve, Reject e Apply Plan

### Objetivo

Implementar o lifecycle completo de decisão e construir uma prévia de Apply
determinística, sem executar mudanças de domínio.

### Escopo permitido

- completar `ProposalEngine.record_generation`, `review`, `approve`, `reject`;
- implementar `build_apply_plan` e `validate_apply_report`;
- validar dependências, ciclos, versões, Confidence, Source e transições;
- adicionar testes unitários de estado e contrato.

### Escopo proibido

- executar `ProposalApplyPlan`;
- chamar Mission, Project, Memory, Intelligence ou AIOrchestrator;
- persistência, eventos obrigatórios, Application ou Companion;
- alterar o contrato do Remodeling.

### Arquivos permitidos

- `Engines/Proposal/engine.py`;
- `Engines/Proposal/validation.py`;
- `Engines/Proposal/models.py` somente se necessário para o contrato congelado;
- `Tests/test_proposal_engine.py`;
- `Tests/test_proposal_lifecycle.py`.

### APIs públicas

Implementar exatamente `record_generation`, `review`, `approve`, `reject`,
`build_apply_plan` e `validate_apply_report` com os tipos definidos.

### Modelos

`record_generation` produz versão imutável em `GENERATED`; Review sempre produz
novo snapshot em `REVIEWED`; Approve registra aprovador, timestamp e versão;
Apply Plan ordena por `order` após validar dependências.

### Serviços

Nenhum serviço de Application. O Engine deve permanecer puro e síncrono.

### Companion

Sem alteração. Nenhuma tela pode sugerir que uma Proposal foi aplicada.

### Testes

- todas as transições válidas e inválidas;
- edição bloqueada em `APPROVED`, `APPLIED` e `APPLY_FAILED` conforme contrato;
- rejeição, versão aprovada e identidade do aprovador;
- dependências ausentes, duplicadas e cíclicas;
- ordenação determinística do Apply Plan;
- Confidence alta sem justificativa, Source cross-Workspace e payload inválido;
- nenhum efeito colateral durante geração, Review ou Approve.

### Critérios de aceite

- só `REVIEWED` pode ser aprovado;
- Approve nunca muda dados externos;
- Proposal rejeitada nunca pode ser aprovada ou aplicada;
- Apply Plan só é produzido para `APPROVED`;
- relatório inválido retorna `Result.error` sem alterar a Proposal;
- mensagens de erro são seguras e estáveis para consumidores.

### Riscos

- transições permissivas que permitem Apply prematuro;
- snapshot aprovado compartilhando coleções mutáveis;
- ordenação que não respeite dependências.

### Validações

Executar testes dos Sprints 1 e 2, suíte completa, `git diff --check` e revisão
manual das transições contra o diagrama do Blueprint.

### Definição de pronto

Lifecycle e Apply Plan implementados sem efeitos externos, com cobertura dos
casos positivos, negativos e de segurança.

---

## Sprint 3 — ProposalApplicationService e adapters de Apply

### Objetivo

Compor contexto real e executar mudanças aprovadas exclusivamente por adapters
explícitos, mantendo isolamento de Workspace, idempotência e falha parcial
segura.

### Escopo permitido

- criar `ProposalApplicationService` volátil;
- criar contratos internos de adapters para Mission, Project e Memory;
- integrar `IntelligenceApplicationService` apenas para `FREE_ONLY` ou
  `ManualHandoff` quando o caso de uso exigir geração;
- executar Apply em ordem e produzir `ProposalApplyReport`;
- manter registros somente na instância da Application.

### Escopo proibido

- acesso direto a repositories ou SQL pelo serviço;
- provider real, rede, scraping ou execução de payload;
- persistência de Proposal, Plan ou Report;
- alterações nos contratos dos Engines existentes;
- automação, retry implícito, transação distribuída ou Undo universal.

### Arquivos permitidos

- `Application/services/proposal_service.py`;
- `Application/services/__init__.py` apenas para exportação;
- `Application/bootstrap.py` apenas para composição aditiva;
- `Application/__init__.py` apenas para exportação aditiva;
- `Tests/test_proposal_application_service.py`;
- `Tests/test_proposal_apply.py`.

### APIs públicas

O serviço deve expor, no mínimo:

- `create_draft(...)`;
- `get(proposal_id)` e `list(workspace_id)`;
- `record_generation(...)`;
- `review(...)`, `approve(...)`, `reject(...)`;
- `build_apply_plan(proposal_id)`;
- `apply(proposal_id, plan, confirmation)`;
- `get_apply_report(proposal_id)`.

`confirmation` deve ser uma confirmação explícita da versão e do alcance; não
é um booleano implícito obtido da geração ou Approve.

### Modelos

Usar os modelos do Engine sem duplicá-los. Contexto de Workspace, Project,
Mission e Memory deve ser somente leitura e conter apenas dados disponíveis.

### Serviços

O serviço coordena, mas não valida regras de domínio novamente. Cada adapter
deve receber `ProposalChange` tipada, devolver resultado controlado e aceitar
`change_id` para idempotência.

### Companion

Nenhuma rota é adicionada neste Sprint. O bootstrap deve permitir construir o
serviço sem alterar o comportamento das rotas existentes.

### Testes

- isolamento por Workspace e rejeição de contexto cruzado;
- listagem volátil e consulta de Proposal;
- geração via handoff sem rede;
- Apply exige `APPROVED`, plano e confirmação da mesma versão;
- idempotência por `change_id`;
- sucesso total, falha, skip por dependência e falha parcial;
- exceções do adapter convertidas em relatório seguro;
- ausência de efeitos antes de Apply.

### Critérios de aceite

- nenhum adapter é chamado em DRAFT, GENERATED, REVIEWED ou REJECTED;
- Apply parcial termina em `APPLY_FAILED` e preserva o relatório;
- mudanças já `APPLIED` não são repetidas;
- Mission, Project e Memory só recebem efeitos autorizados e explícitos;
- Application não importa APIs de provider nem acessa SQL.

### Riscos

- efeitos parciais difíceis de recuperar;
- composição duplicar validações ou quebrar isolamento;
- confirmação aceitar versão diferente da aprovada.

### Validações

Executar testes dos Sprints 1–3, suíte completa, verificação de imports e
Genesis Doctor. Inspecionar o diff para confirmar composição aditiva.

### Definição de pronto

Application Service executa somente Proposals aprovadas, relata cada mudança e
mantém comportamento existente intacto.

---

## Sprint 4 — Migração do Remodeling e integração de apresentação

### Objetivo

Migrar o Remodeling para a fonte comum de Proposal e expor a revisão e Apply
sem quebrar rotas, modelos ou orçamento existentes.

### Escopo permitido

- substituir lifecycle duplicado do Remodeling por delegação ao Proposal Engine;
- preservar regras específicas de brief, parser JSON e orçamento preliminar;
- adicionar somente endpoints/views necessários para Review, Approve, prévia e
  Apply se já previstos pelos contratos públicos existentes;
- manter estados, mensagens e compatibilidade documentados no Blueprint de
  Remodeling.

### Escopo proibido

- criar segundo modelo de Proposal ou segundo enum de estados;
- alterar rotas públicas existentes ou remover campos compatíveis;
- adicionar IA, provider, persistência, uploads, pagamentos ou cálculo fiscal;
- alterar Core, CLI, AIOrchestrator ou contratos de Mission/Project/Memory;
- Apply automático após geração ou Approve.

### Arquivos permitidos

- `Application/services/remodeling_service.py`;
- `Application/services/proposal_service.py`;
- `Interfaces/Companion/application.py` somente delegação aditiva;
- `Interfaces/Companion/server.py` somente rotas já aprovadas;
- `Interfaces/Companion/views.py` somente apresentação do fluxo;
- `Tests/test_remodeling_copilot.py`;
- `Tests/test_proposal_companion.py`.

Qualquer arquivo adicional exige justificativa e review antes da alteração.

### APIs públicas

Preservar integralmente as APIs do Remodeling. Novas operações, se aprovadas,
devem ser explícitas e separadas:

- `review_proposal`;
- `approve_proposal`;
- `build_proposal_apply_preview`;
- `apply_proposal` com confirmação de versão;
- `get_proposal_apply_report`.

### Modelos

Remodeling usa `Proposal` e `ProposalChange` comuns. O orçamento preliminar
continua específico e é representado em `after`/metadata apenas como prévia,
sem torná-lo preço final.

### Serviços

`RemodelingApplicationService` mantém brief, lacunas, parser seguro e orçamento;
`ProposalApplicationService` mantém lifecycle e Apply. Nenhum serviço chama
Engine diretamente a partir da Interface.

### Companion

Apresentar sempre etapa atual, origem, Confidence, Risks, Assumptions,
consequência, reversibilidade e próxima ação. Separar visual e semanticamente
Review, Approve e Apply; manter acessibilidade, foco e estados de erro.

### Testes

- regressão de todas as rotas e APIs anteriores;
- fluxo HTTP completo Brief → Proposal → Review → Approve → Apply;
- Approve não aplica mudanças;
- orçamento continua determinístico e preliminar;
- rejeição, falha parcial e recuperação explícita;
- HTML escapa entrada e não expõe segredos;
- navegação por teclado e estados de erro/sucesso relevantes.

### Critérios de aceite

- Remodeling possui uma única implementação do lifecycle;
- rotas anteriores continuam compatíveis;
- nenhuma mudança é efetivada antes de Apply confirmado;
- Proposal aplicada é idempotente;
- falha informa o que ocorreu, o que não ocorreu e como continuar;
- Companion não compõe Engines diretamente.

### Riscos

- regressão de contratos HTTP existentes;
- divergência entre orçamento específico e mudanças genéricas;
- confusão de Approve com Apply na Interface.

### Validações

Executar testes de Remodeling, Companion e suíte completa; executar Doctor;
fazer revisão manual da jornada e de todos os caminhos de falha.

### Definição de pronto

Remodeling delega lifecycle e Apply ao contrato comum, Companion mantém
compatibilidade e todos os testes de integração passam.

---

## Sprint 5 — Hardening, documentação de implementação e encerramento

### Objetivo

Validar a implementação completa contra o Blueprint, contratos, segurança,
compatibilidade e critérios operacionais do Genesis.

### Escopo permitido

- corrigir defeitos encontrados nos arquivos já autorizados nos Sprints 1–4;
- completar testes de regressão, arquitetura, segurança e acessibilidade;
- revisar exports, type hints, imutabilidade e mensagens de erro;
- executar suíte completa e Doctor.

### Escopo proibido

- novas capacidades, persistência, provider real ou mudança arquitetural;
- alterar o Blueprint de origem para acomodar implementação divergente;
- refatoração não necessária ao contrato Proposal;
- commit ou push sem autorização explícita.

### Arquivos permitidos

- somente arquivos permitidos nos Sprints 1–4;
- novos arquivos de teste exclusivamente se forem indispensáveis para um
  critério de aceite já definido e aprovados no review.

### APIs públicas

Nenhuma API nova. Confirmar assinaturas, exports e compatibilidade.

### Modelos

Auditar todos os modelos contra os campos, enums, snapshots e estados do
Blueprint. Confirmar que nenhum mapa ou lista interna é mutável.

### Serviços

Auditar fronteiras: Engine puro, Application como composição, adapters
explícitos e nenhuma dependência inversa do Core.

### Companion

Auditar semântica de Proposal → Review → Approve → Apply, acessibilidade,
mensagens de falha parcial, confirmação proporcional e ausência de ação
automática.

### Testes

- `.venv/bin/python -m pytest Tests`;
- testes focados do Proposal, Application, Remodeling e Companion;
- verificações de imports e imutabilidade;
- `.venv/bin/python -m CLI.main doctor`;
- `git diff --check`.

### Critérios de aceite

- todos os critérios do Blueprint de origem marcados como satisfeitos;
- suíte completa sem falhas atribuíveis à implementação;
- Doctor executado e resultado reportado;
- nenhuma alteração fora do escopo aprovado;
- review confirma segurança, simplicidade, compatibilidade e ausência de
  dependência de fornecedor.

### Riscos

- testes verdes sem cobertura de falha parcial;
- alterações preexistentes confundirem o diagnóstico;
- documentação e contrato divergirem do código final.

### Validações

Comparar diff com este plano arquivo por arquivo; repetir testes após qualquer
correção; registrar falhas ambientais separadamente de falhas do produto.

### Definição de pronto

Blueprint implementado integralmente, review concluído, suíte e Doctor
executados, riscos conhecidos registrados e implementação pronta para commit
somente mediante autorização do usuário.

## Matriz final de não regressão

| Área | Deve permanecer inalterada |
|---|---|
| Core | Configuration, Context, Result, Registry, Orchestrator, EventBus, Logger e Lifecycle |
| CLI | comandos, códigos de saída e Doctor |
| AI | independência de provider, `AIOrchestrator` e `FREE_ONLY` |
| Domínios | contratos públicos de Mission, Project e Memory |
| Remodeling | brief, parser JSON, orçamento preliminar, rotas e compatibilidade |
| Persistência | Proposal, Plan e Report voláteis na v1 |

## Regra de escalonamento

Se surgir necessidade de persistência, novo estado, novo adapter, alteração de
rota, dependência externa, mudança de contrato ou nova responsabilidade, parar o
Sprint, registrar o conflito e solicitar review arquitetural. Não resolver por
interpretação local nem ampliar a lista de arquivos permitidos.
