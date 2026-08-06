# Plano de implementação — Genesis Document Engine v1

**Blueprint de origem:** `Blueprints/GenesisDocumentEngine.md`
**Versão:** 1.0
**Status:** plano executável condicionado a review arquitetural

## Regras de execução

Este plano não autoriza código antes do review. A implementação deve ser
incremental, aditiva e restrita aos arquivos do Sprint corrente. Qualquer
necessidade de persistência, renderer, novo estado, alteração de contrato ou
mudança em Core/CLI/Infrastructure interrompe o Sprint e exige review.

## Contrato de integração congelado

`Proposal` é o agregado comercial e `Document` é o agregado editorial. Proposal
não herda de Document. A integração futura usa somente o adapter unidirecional
`Proposal → ProposalDocumentAdapter → Document`, com `document_id` opcional e
retrocompatível.

`Proposal.version` e `DocumentVersion.version` permanecem independentes. Todo
snapshot documental originado de Proposal registra
`source_proposal_id`, `source_proposal_version`, `template_id`,
`template_version`, `brand_profile_id` e `brand_profile_version` ou snapshot
equivalente. `DocumentStatus.APPROVED` nunca autoriza Proposal Apply e Document
não possui `APPLIED`.

`ProposalReview` é a revisão comercial oficial. Revisão editorial produz nova
`DocumentVersion` ou evento editorial. Template e branding não entram no
Proposal Engine, e `DocumentMetadata` não substitui relações comerciais de
Proposal.

## Ordem inter-Blueprint congelada

1. congelamento documental;
2. lifecycle e Apply do Proposal;
3. fundação pura do Document Engine;
4. adapter Proposal → Document;
5. Application Service;
6. integração com Projects, Workflow, Mission Copilot e Memory;
7. migração controlada do Remodeling;
8. Companion;
9. renderers futuros fora do domínio.

## Sprint 0 — review e congelamento do contrato

Confirmar a fonte única entre Document e Proposal, a separação entre lifecycle
genérico e Apply específico, os schemas de template, o isolamento por Workspace
e a ausência de formatos no domínio. Mapear consumidores do Remodeling,
Mission Copilot, Workflow, Projects, Memory e Companion.

Nenhum arquivo de código ou teste é alterado. O review deve aprovar este
Blueprint e registrar riscos de migração antes do Sprint 1.

## Sprint 1 — domínio puro e validação

### Arquivos permitidos

- `Engines/Document/__init__.py`
- `Engines/Document/models.py`
- `Engines/Document/validation.py`
- `Engines/Document/engine.py`
- `Tests/test_document_models.py`
- `Tests/test_document_validation.py`

### Entrega

Implementar os sete modelos do Blueprint, enums auxiliares necessários,
normalização segura, snapshots imutáveis e operações de criação/validação sem
efeitos externos. O engine pode depender somente de `Core.result.Result` e da
biblioteca padrão.

### Aceite

Imutabilidade profunda, UUID/timestamp corretos, schema inválido, seção
duplicada, referência cross-Workspace, template incompatível e transição
inválida retornam erro controlado. Nenhum import de Application, Interfaces,
Infrastructure, provider ou formato aparece no domínio.

## Sprint 2 — lifecycle, templates e versionamento

### Arquivos permitidos

- `Engines/Document/engine.py`
- `Engines/Document/models.py`
- `Engines/Document/validation.py`
- `Tests/test_document_engine.py`
- `Tests/test_document_lifecycle.py`
- `Tests/test_document_templates.py`

### Entrega

Implementar `generate`, revisão, aprovação, rejeição, derivação de versão,
hash determinístico e validação de `DocumentTemplate`/`BrandProfile`. Templates
e marcas continuam objetos em memória; nenhuma persistência ou renderer é
criado.

Este Sprint trata exclusivamente lifecycle editorial. Não implementa
`ProposalReview`, `ProposalStatus`, `Proposal Apply` ou qualquer sincronização
de estado com Proposal.

### Aceite

Snapshots aprovados não podem ser mutados; nova versão não sobrescreve a
anterior; transições seguem o diagrama; o mesmo conteúdo produz hash estável;
template e marca ficam registrados na versão; `APPLIED` não existe no domínio
genérico.

## Sprint 3 — Application e integrações de contexto

### Arquivos permitidos

- `Application/services/document_service.py`
- `Application/services/__init__.py` somente para exportação
- `Application/bootstrap.py` somente composição aditiva
- `Tests/test_document_application_service.py`

### Entrega

Criar serviço volátil que reúna Project, Workflow, Mission Copilot e Memory por
contratos públicos, crie documentos e liste/consulte por Workspace. O serviço
não acessa repositories diretamente nem duplica validações. Salvamento em
Memory é explícito e opcional.

### Aceite

Isolamento por Workspace, contexto somente leitura, nenhuma execução automática,
nenhuma rede e compatibilidade das rotas existentes. Workflow apenas observa;
não há transição automática por criar ou aprovar documento.

## Sprint 4 — adapter do Proposal e regressão do Remodeling

### Arquivos permitidos

- `Application/services/proposal_service.py`
- `Application/services/remodeling_service.py`
- `Tests/test_proposal_document_adapter.py`
- `Tests/test_remodeling_copilot.py`

### Entrega

Mapear Proposal para `Document(document_type=PROPOSAL)` e suas seções sem criar
segundo lifecycle. Preservar `ProposalStatus`, `ProposalChange`, orçamento
preliminar, Apply Plan/Report, APIs e rotas do Remodeling. Document aprovado não
aplica mudanças; somente a confirmação do fluxo Proposal o faz.

O adapter é unidirecional, usa `Proposal.document_id` quando disponível e
registra em cada `DocumentVersion` a Proposal de origem, suas versões, template
e BrandProfile. Alterações editoriais nunca atualizam automaticamente Proposal.

### Aceite

Fluxo legado continua compatível, nenhuma ação ocorre antes de Apply, versões
documentais e versões Proposal permanecem rastreáveis e dados de outro
Workspace são rejeitados.

## Sprint 5 — hardening e review de encerramento

Executar testes focados, suíte completa, Doctor, `git diff --check`, auditoria de
imports e inspeção de segurança. Confirmar que nenhum arquivo fora dos Sprints
foi alterado e que formatos/renderers não entraram no domínio. Commit e push
continuam condicionados à autorização explícita.

## Matriz de não regressão

| Área | Garantia |
|---|---|
| Core/CLI/Infrastructure | inalterados |
| Proposal/Remodeling | lifecycle, Apply, APIs e rotas preservados |
| Projects/Workflow/Mission Copilot/Memory | contratos e isolamento preservados |
| Persistência | nenhum Document persistido na v1 |
| Formatos | nenhum PDF, DOCX, HTML, impressão ou exportação no domínio |
| Renderers | PDF, DOCX, HTML, impressão, e-mail e portal do cliente ficam fora do domínio |
