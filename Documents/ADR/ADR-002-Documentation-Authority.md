# ADR-002 — Autoridade documental

Status: Aceito
Data: 2026-08-03

## Contexto

O repositório acumulou duas Constituições, dois ADRs com o identificador 001,
três roadmaps, mapas planejados apresentados como atuais e checklists que não
refletiam código e testes. Isso permitia interpretações conflitantes e violava a
regra de uma única fonte oficial de verdade.

## Decisão

A precedência normativa é:

1. Constituição;
2. ADRs aceitos e vigentes;
3. Architecture;
4. Roadmap;
5. Blueprints;
6. código;
7. testes.

Os caminhos canônicos são:

| Responsabilidade | Caminho |
|---|---|
| Constituição | `Documents/GenesisConstitution.md` |
| ADRs | `Documents/ADR/ADR-NNN-<Titulo>.md` |
| Arquitetura | `Documents/ARCHITECTURE.md` |
| Roadmap | `Documents/ROADMAP.md` |
| Blueprints | `Blueprints/Genesis<Componente>.md` |
| Regras para agentes | `AGENTS.md` |

Código e testes são evidência do estado real, não autoridade para contrariar um
documento superior. Um Blueprint descreve o contrato aprovado de um componente,
mas não pode alterar sozinho princípios ou camadas superiores.

Quando houver conflito:

1. identificar o documento vigente de maior autoridade;
2. não implementar a interpretação conflitante;
3. registrar o conflito no review;
4. atualizar ou marcar a fonte inferior como superseded;
5. exigir ADR para mudar decisão arquitetural e alteração constitucional para
   mudar a Constituição.

Documentos históricos são preservados com aviso de status e link para a fonte
canônica. Conteúdo `Superseded` ou `Archived` não é normativo.

## Documentos legados nesta decisão

- `Documents/Constitution.md`: superseded pela Constituição canônica;
- `Documents/Architecture/GenesisMap.md`: superseded pela Architecture canônica;
- `Documents/Architecture/SystemOverview.md`: archived; arquivo vazio legado;
- `Documents/Roadmap/MasterPlan.md`: superseded pelo Roadmap canônico;
- `Documents/Roadmap/ProductBacklog.md`: superseded pelo Roadmap canônico;
- `Documents/Roadmap/Roadmap.md`: archived; arquivo vazio legado;
- `Documents/Decisions/DecisionLog.md`: archived; arquivo vazio, ADRs são o
  registro canônico de decisões arquiteturais;
- `Documents/Sprints/Sprint-001.md`: archived; arquivo vazio legado.

Os dois ADRs identificados como 001 permanecem registros históricos aceitos de
suas decisões, mas são marcados como identificadores legados. Novos ADRs usam
numeração única a partir deste ADR-002.

Este ADR substitui parcialmente o `ADR-001-Event-Driven-Architecture.md` somente
na exigência de que toda comunicação interna use EventBus. A orientação a
eventos continua aceita; chamadas síncronas entre contratos públicos continuam
válidas quando previstas pela Architecture e por Blueprint específico.

## Consequências

- agentes passam a ter uma ordem inequívoca de leitura e precedência;
- documentos planejados deixam de representar falsamente o estado implementado;
- legados permanecem disponíveis sem competir com fontes canônicas;
- futuras mudanças documentais precisam atualizar apenas a fonte responsável.
