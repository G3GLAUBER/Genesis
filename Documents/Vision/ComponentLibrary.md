# Component Library

## App Shell

Context Rail, Context Header, Focus Canvas e Insight Rail. Mantém orientação e
separa trabalho principal de contexto complementar.

## Cards

### Attention Card

Título orientado por ação, razão temporal, impacto, contexto e uma ação
principal. Variações: decision, risk, blocked e recommendation.

### Project Card

Propósito, marco, Missions, Memory, responsável, última atividade, próxima ação
e Health. Nunca é apenas título com contadores.

### Memory Card

Síntese, origem, associações, relevância e estado de confiança.

### Intelligence Card

Pedido, estado, contexto utilizado, Confidence e próximo Handoff humano.

### Recommendation Card

Direção recomendada, razão, Confidence, concessão e ações aceitar, ajustar ou
adiar.

## Navigation

### Context Rail

Brand, Workspace switcher, destinos, Focus atual e Settings. Item ativo combina
forma, contraste e indicador lateral.

### Context Header

Breadcrumb, título, subtitle contextual, presença de colaboradores quando
aplicável e ações da entidade atual.

### Command Surface

Busca universal, ações recentes e resultados agrupados. Totalmente operável por
teclado.

## Status

### Badge

Rótulo curto e semântico. Nunca depende apenas de cor.

### Health Signal

Estado, impacto e recomendação. “Healthy” é discreto; problemas explicam a
consequência.

### Progress Narrative

Linha de progresso acompanhada por marco atual e bloqueio, não percentagem nua.

### Journey Rail

Etapas concluídas, atual, próximas e bloqueadas. Usada em Remodeling e
Automation.

## Timeline

Agrupa mudanças por decisão ou resultado. Cada item tem ator, verbo, objeto,
tempo e, quando relevante, razão. Permite aprofundar sem expor ruído.

## Inputs

Rótulo sempre visível, ajuda contextual, exemplo somente quando útil e erro
junto ao campo. Textarea cresce até limite confortável. Search é distinto de
Command Surface.

## Buttons

- **Primary:** uma ação dominante por região.
- **Secondary:** alternativa segura.
- **Quiet:** ações de baixa ênfase.
- **Danger:** consequência destrutiva explícita.
- **Split action:** evitar; preferir escolha antes da ação.

Rótulos usam verbo + objeto: “Aprovar Proposal”, não “Confirmar”.

## Dialogs

Modais são reservados para decisões focadas, confirmação de alto impacto e
contexto curto. Trabalho longo, Review e criação pertencem ao canvas. Todo modal
tem título de consequência, foco contido e saída previsível.

## System states

### Empty State

Explica valor, por que está vazio e uma ação significativa. Sem ilustração
decorativa obrigatória.

### Loading

Mostra o que Genesis está fazendo e preserva layout. Para espera longa, oferece
Pause ou saída segura.

### Error

Efeito, preservação, causa conhecida e recuperação. Nunca culpa a pessoa.

### Success

Confirma mudança e continuidade. Toast apenas para ações pequenas e reversíveis.

### Offline / Degraded

Explica o que continua disponível e o que será retomado depois.

## Tooltips

Esclarecem, não carregam informação essencial. Devem funcionar por foco e hover
e nunca conter ação indispensável.
