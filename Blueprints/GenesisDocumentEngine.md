# Blueprint — Genesis Document Engine v1

**Versão:** 1.0
**Status:** proposta arquitetural; requer review antes da implementação
**Escopo:** fundação de documentos profissionais estruturados, sem renderização
ou exportação.

## Objetivo

Extrair do Proposal Engine uma fundação reutilizável para qualquer documento
profissional produzido pelo Genesis. Proposal é o primeiro tipo suportado;
Contract, Budget, Inspection Report, Completion Report e Warranty são
especializações futuras do mesmo contrato.

O engine produz somente uma representação estruturada, validável, versionada e
independente de apresentação. PDF, DOCX, HTML, impressão, e-mail, exportação,
integrações externas e banco não pertencem a este domínio.

## Autoridade e compatibilidade

Este Blueprint complementa `Blueprints/GenesisProposalEngine.md`; não revoga
seus estados, APIs ou compatibilidade do Remodeling. A extração deve manter uma
única fonte de verdade para o lifecycle comum e usar adapters durante a
migração. Nenhuma implementação começa antes de review arquitetural.

## Relação oficial com Proposal

`Document` é o agregado editorial oficial. `Proposal` é o agregado comercial
oficial e não herda de Document. A relação é opcional, aditiva e
retrocompatível:

```text
Proposal (document_id opcional)
        → ProposalDocumentAdapter
        → Document
```

O adapter é unidirecional. Não existe sincronização bidirecional automática,
nem o Document Engine pode alterar lifecycle, mudanças ou Apply de uma Proposal.
O vínculo não transforma Document em fonte de verdade comercial nem Proposal em
fonte de verdade visual.

## Localização e direção de dependências

```text
Interface → Application DocumentApplicationService
          → DocumentEngine → Core.result.Result
                         ↘ contratos de Project, Workflow, Mission Copilot,
                           Memory e Branding reunidos pela Application
```

`Engines/Document/` contém apenas regras de domínio, modelos imutáveis,
validação e composição de uma árvore documental. Não importa Application,
Interfaces, Companion, Core além de `Result`, repositories, SQL, rede,
providers, SDKs ou renderizadores.

Application reúne contexto por contratos públicos existentes, escolhe template
e BrandProfile, chama o engine e mantém resultados voláteis na v1. Interfaces
apresentam a estrutura e nunca compõem engines diretamente.

## Limites do domínio

O domínio conhece tipos de documento, seções, conteúdo semântico, metadados,
identidade visual declarativa, versões e estados de revisão. Não conhece meios
de saída, paginação física, fontes instaladas, margens de papel, MIME type,
layout de tela, impressão, transporte ou armazenamento.

Renderizadores futuros recebem um contrato estruturado através de uma porta da
Application. A escolha de renderer e formato ocorre fora do domínio; adicionar
um renderer não altera `Document`, templates ou regras de conteúdo.

## Vocabulário

- **Document:** agregado imutável que identifica o documento, seu tipo, template,
  marca, conteúdo estruturado, versão corrente e estado.
- **DocumentSection:** unidade semântica ordenada e reutilizável; contém título,
  tipo, conteúdo estruturado, subseções e regras de visibilidade.
- **DocumentTemplate:** definição declarativa de estrutura, seções requeridas,
  ordem, placeholders, versão e tipos de documento compatíveis.
- **BrandProfile:** identidade visual nomeada e versionada (cores, tipografia,
  logotipo referenciado por identificador seguro, tom e dados de contato), sem
  instruções de renderização.
- **DocumentVersion:** snapshot imutável do conteúdo, template, marca e
  metadados em um instante; versões aprovadas nunca são editadas.
- **DocumentMetadata:** dados operacionais e de proveniência, sem segredo,
  incluindo workspace, projeto, missão, autor, fontes e campos livres seguros.

## Modelos públicos

Todos os modelos são `dataclass(frozen=True)`, usam UUID textual, timestamps UTC
com timezone e coleções imutáveis (tuplas ou mapas imutáveis). IDs e referências
de Workspace são validados nas fronteiras. Conteúdo é dado, nunca código.

### `Document`

Agregado raiz com:

- `id`, `document_type`, `title` e `workspace_id`;
- `template_id` e `template_version`;
- `brand_profile_id` e `brand_profile_version`;
- `sections` ordenadas, sem IDs duplicados;
- `metadata` (`DocumentMetadata`);
- `current_version` e histórico de `DocumentVersion`;
- `status` (`DocumentStatus`), `created_at`, `updated_at`;
- `source_document_id` opcional para derivação, nunca para compartilhar estado.

O agregado é um snapshot: cada operação de edição/revisão devolve um novo
`Document`, sem mutar o anterior.

### `DocumentSection`

Contém `id`, `key`, `section_type`, `title`, `order`, `content`, `children`,
`required`, `visible`, `reusable_section_id` opcional e `metadata` segura.
`content` é uma árvore limitada de valores JSON (texto, número, booleano,
listas e mapas), sem HTML confiável, macros, chamadas ou código executável.
Seções reutilizadas são copiadas como snapshot; alterar uma biblioteca não
altera documentos já criados.

### `DocumentTemplate`

Contém `id`, `name`, `version`, `document_types`, `section_schema`,
`required_sections`, `default_sections`, `placeholder_schema`, `locale` e
`metadata`. Template define estrutura e validação, não conteúdo de um caso
concreto nem regras de preço, contrato ou domínio de Project.

Templates são imutáveis por versão. Uma alteração estrutural cria nova versão;
documentos existentes permanecem vinculados à versão usada na criação.

### `BrandProfile`

Contém `id`, `name`, `version`, `colors`, `typography`, `logo_ref`, `tone`,
`contact_fields`, `locale` e `metadata`. Valores são tokens semânticos e
referências opacas; não contêm HTML, CSS, arquivos binários, segredos ou
dependência de ferramenta de renderização. Uma marca pode ser aplicada a vários
tipos de documento e versões são imutáveis.

### `DocumentVersion`

Contém `document_id`, `version`, `created_at`, `created_by`, `reason`,
`sections`, `template_id/version`, `brand_profile_id/version`, `metadata` e
`content_hash` determinístico. É um snapshot completo, não um diff implícito.
Versões derivadas mantêm `source_version` e não sobrescrevem histórico.

Quando a origem for uma Proposal, deve registrar também
`source_proposal_id` e `source_proposal_version`. `Proposal.version` e
`DocumentVersion.version` são independentes: a primeira representa evolução
comercial/decisória; a segunda representa evolução editorial/visual.

### `DocumentStatus`

Estados genéricos: `DRAFT`, `GENERATED`, `IN_REVIEW`, `REVIEWED`, `APPROVED`,
`REJECTED`, `SUPERSEDED` e `ARCHIVED`.

Transições válidas:

```text
DRAFT → GENERATED → IN_REVIEW → REVIEWED → APPROVED
  └──────────────────────────────→ REJECTED
APPROVED → SUPERSEDED → ARCHIVED
REJECTED → DRAFT (nova versão derivada, nunca mutação)
```

`APPROVED`, `SUPERSEDED` e `ARCHIVED` são snapshots imutáveis. O domínio
genérico não possui `APPLIED`: aplicação de mudanças é capacidade específica
de Proposal ou de outro domínio, coordenada pela Application.

`DocumentStatus.APPROVED`, quando usado, significa somente aprovação editorial.
Nunca autoriza `Proposal Apply`. `ProposalReview` permanece a revisão comercial
oficial; revisão editorial cria nova `DocumentVersion` ou evento editorial e
não duplica `ProposalReview`.

### `DocumentMetadata`

Contém `workspace_id`, `project_id`, `mission_id`, `author_id`, `created_by`,
`locale`, `source_refs`, `tags`, `custom_fields` e `trace_id` opcional. Campos
devem ser serializáveis como dados, não podem conter credenciais, cookies,
tokens ou exceções brutas. Relações entre Workspaces são rejeitadas.

## Contrato do Document Engine

Operações puras retornam `Result` e não persistem nem publicam eventos
obrigatórios:

- `create_draft(document_type, title, template, brand, metadata)`;
- `generate(document, sections, generated_by)`;
- `start_review(document, reviewer)`;
- `record_review(document, review)`;
- `approve(document, approver)`;
- `reject(document, reviewer, reason)`;
- `derive_version(document, reason)`;
- `validate(document, template)`.

Cada operação valida tipo, template, schema de seções, ordenação, campos
obrigatórios, referências de Workspace e transição de estado. Não há API de
renderização, exportação ou execução de efeitos.

## Proposal como primeiro documento

Proposal permanece o contrato vertical definido em
`GenesisProposalEngine.md`, com `ProposalStatus` e `ProposalChange`. Sua
representação documental deve ser um adapter/mapper explícito:

- `document_type = PROPOSAL`;
- `Proposal.document_id` é a referência opcional ao agregado editorial;
- template controla a ordem das seções Proposal;
- conteúdo das seções deriva de `summary`, `recommendation`, `changes`,
  `assumptions`, `risks`, `missing_information` e `sources`;
- `DocumentVersion` acompanha a versão visual/estrutural, enquanto a versão e
  lifecycle da Proposal continuam autoridade para Review, Approve e Apply;
- `APPROVED` de Document não executa Apply; somente o fluxo Proposal aprovado e
  confirmado pode produzir `ProposalApplyPlan`.

O adapter é unidirecional e não gera mutações comerciais a partir de alterações
editoriais. `workspace_id`, `project_id`, `mission_id` e outras relações
comerciais continuam oficiais em Proposal; `DocumentMetadata` apenas as
referencia para rastreabilidade.

Contract, Budget, Inspection Report, Completion Report e Warranty serão tipos
adicionais, com schemas e regras específicas, sem copiar o agregado ou criar
novos renderizadores por tipo.

## Reutilização

Uma seção pode ser reutilizada por `reusable_section_id` e incorporada como
snapshot. Um template pode declarar compatibilidade com vários tipos de
documento e placeholders tipados; o conteúdo fornecido pela Application é o
que muda por caso. Assim, o mesmo template pode gerar Proposal, Budget ou
Contract alterando apenas `document_type`, BrandProfile e conteúdo validado.

Templates e BrandProfiles são separados: estrutura não contém identidade visual
e marca não contém conteúdo. Uma combinação concreta é registrada no
`DocumentVersion`, garantindo reprodutibilidade.

## Integrações previstas

- **Projects:** Application fornece dados somente leitura do Project e grava a
  relação em `DocumentMetadata`; Document Engine não altera Project.
- **Workflow:** Workflow pode observar a existência, status e próxima ação de
  documentos por uma observação futura; não cria, aprova ou aplica documentos.
- **Mission Copilot:** produz contexto, premissas, riscos e resultados
  estruturados que a Application converte em conteúdo; respostas continuam
  manuais e não executáveis.
- **Memory:** fontes e resultado de documento podem ser salvos como Memory
  somente por ação explícita, com isolamento por Workspace; o Engine não acessa
  Memory diretamente.
- **Companion:** apresenta estrutura, estado, origem, versão, marca e próxima
  ação por serviços da Application; não chama renderizadores nem Engines.

Integrações são aditivas e não introduzem dependência no Core, CLI ou
Infrastructure.

## Renderização futura e múltiplos formatos

O domínio expõe uma árvore documental semântica e um contrato de renderer fora
do Engine, por exemplo `render(document_version, RenderOptions) → RenderedArtifact`.
`RenderOptions` e `RenderedArtifact` pertencem à futura Application/Infrastructure
e são portas, não modelos do domínio. Adapters independentes poderão produzir
HTML, PDF, DOCX ou outros formatos; cada um declara capabilities, versão e
falhas controladas. O domínio nunca importa esses nomes ou bibliotecas.

Renderização é somente leitura sobre um snapshot. O artefato não altera status,
versão, conteúdo ou relações. Exportação, impressão e envio permanecem casos de
uso posteriores, sujeitos a Blueprints próprios.

Renderers futuros permanecem fora do domínio Document, incluindo adapters para
PDF, DOCX, HTML, impressão, e-mail e portal do cliente. Nenhum desses formatos
ou meios de distribuição pode aparecer em `Document`, `DocumentSection`,
`DocumentTemplate`, `BrandProfile` ou `DocumentVersion`.

## Segurança, privacidade e acessibilidade

- nenhum provider, rede, scraping, SDK ou segredo;
- conteúdo manual é tratado como dado e validado por schema;
- referências e metadata não vazam payloads sensíveis;
- isolamento por Workspace em toda relação;
- snapshots aprovados preservam proveniência e hash determinístico;
- Interfaces devem expor estado, versão, origem, marca, lacunas e próxima ação;
- futuras telas devem manter teclado, foco visível, leitor de tela e movimento
  reduzido.

## Fora do escopo

Persistência de Documents/Templates/Brands, colaboração em tempo real,
permissões multiusuário, assinatura digital, cálculo financeiro, contratos
jurídicos, geração automática irrestrita, exportação, impressão, e-mail,
uploads, banco, Core, CLI, Infrastructure e alterações em APIs existentes.

## Critérios de aceitação do Blueprint

- [ ] domínio estruturado e independente de formato;
- [ ] modelos imutáveis e versionamento por snapshot;
- [ ] templates e BrandProfiles versionados e separados;
- [ ] seções reutilizáveis por cópia semântica;
- [ ] lifecycle genérico sem `APPLIED`;
- [ ] Proposal mapeado sem duplicar lifecycle ou Apply;
- [ ] integrações definidas somente pela Application;
- [ ] renderers futuros substituíveis sem alterar o domínio;
- [ ] nenhuma alteração em Core, CLI, Infrastructure, banco, código ou testes
      nesta fase documental.
