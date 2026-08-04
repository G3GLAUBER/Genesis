# Genesis UI Kit

**Sistema:** Genesis Continuum

**Versão:** 1.0

**Regra:** toda futura tela compõe estes elementos antes de propor um novo.

## Estrutura

```text
Foundations
├── color, type, spacing, grid, radius, elevation, motion
Primitives
├── icon, label, divider, avatar, progress line
Controls
├── button, field, textarea, select, checkbox, search, segmented control
Navigation
├── context rail, workspace switcher, context header, tabs, command surface
Content
├── attention card, project card, memory card, recommendation, context receipt
State
├── badge, confidence, health signal, risk notice, progress narrative
Journey
├── continuum line, journey rail, timeline event, review summary
Feedback
└── empty, loading, error, success, degraded, dialog, toast
```

## Regra de composição

Cada superfície possui um propósito, um título, uma ação dominante e uma saída
previsível. Cards não são containers universais. Um novo componente só é criado
quando semântica, comportamento e acessibilidade não cabem nos componentes
existentes.

## Shell

### Context Rail

Contém marca, Workspace, cinco destinos, Focus atual e Settings. Largura desktop
256 px. O item ativo combina indicador lateral, superfície e peso tipográfico.

### Context Header

Mostra relação atual, título, síntese e ações do contexto. Nunca repete métricas
da página nem expõe modo técnico no percurso diário.

### Focus Canvas

Região principal. Largura útil máxima de 1.440 px e medida editorial entre 55 e
75 caracteres. Recebe uma ação dominante por momento.

### Insight Rail

Contexto complementar, Recommendation ou Risk. Só aparece quando melhora a
decisão. Em tablet e mobile, torna-se painel sob demanda.

## Controles

### Button

Altura 40 px; touch 44 px. Variantes Primary, Secondary, Quiet e Danger. Label
sempre nomeia consequência. Loading preserva largura e descreve a ação.

### Field

Label visível, ajuda opcional, controle e mensagem. Erro fica ligado ao campo e
preserva valor. Placeholder nunca é label.

### Search

Busca conteúdo; Command Surface navega e inicia ações. Não misturar os dois
modelos numa entrada ambígua.

### Filter Chip

Mostra filtro ativo e remoção acessível. Filtros avançados permanecem
progressivos e a ação “Limpar filtros” só aparece quando necessária.

## Componentes de produto

### Continue Card

Resultado desejado, razão, último Progress Event, próximo movimento e ação
**Continuar**. É a expressão primária da continuidade.

### Attention Card

Decisão ou risco, “por que agora”, impacto, contexto e ação. Máximo de cinco no
Command Center.

### Project Card

Propósito, responsável, marco atual, narrativa de progresso, decisão aberta,
última mudança e próxima ação. Percentagem nunca aparece sozinha.

### Intelligence Session

Pedido, Context Receipt, plano, Recommendation, Confidence, alternativa,
resultado e Review. Fonte externa é metadado de confiança.

### Context Receipt

Lista compacta de Workspace, Project, Memories e restrições consideradas. Cada
item pode ser inspecionado e, quando permitido, removido antes de continuar.

### Memory Card

Síntese, origem, associação, relevância atual, última utilização e estado
Confirmada, Inferida, Desatualizada ou Em Review.

### Recommendation

Direção preferida, razão decisiva, Confidence, concessão e alternativa.
Oferece **Seguir recomendação**, **Ajustar** e **Agora não**.

### Journey Rail

Etapas completas, atual, futuras e bloqueadas. A Continuum Line liga a jornada;
somente a etapa atual recebe ênfase de ação.

### Timeline Event

Ator, verbo, objeto, razão e tempo. Eventos relacionados são agrupados por
Decision ou resultado; nunca formam feed infinito.

### Health Signal

Estado, impacto, capacidade restante e ação segura. Healthy é discreto.
Degraded e Unavailable explicam o que foi preservado.

## Estados do sistema

### Empty

Explica o valor do espaço, a razão do vazio e uma ação significativa. Não usa
ilustração como substituto de orientação.

### Loading

Preserva estrutura e diz “Compreendendo contexto”, “Preparando Proposal” ou o
estado humano equivalente. Esperas longas oferecem Pause ou saída segura.

### Error

Declara o que não aconteceu, o que foi preservado, a causa conhecida e a ação
segura. Nunca culpa a pessoa nem termina em “tente novamente” sem contexto.

### Success

Confirma mudança, destino e continuidade. Toast é reservado a ações pequenas e
reversíveis; marcos aparecem no próprio canvas.

### Degraded

Explica o que continua disponível, o que ficará pendente e como será retomado.

## Uso responsivo

- desktop: Context Rail fixa, Canvas flexível e Insight Rail condicional;
- tablet: rail compacta, contexto complementar em sheet;
- mobile: quatro destinos inferiores e More, conteúdo em uma coluna;
- nenhum componente depende de hover, drag ou gesto complexo;
- alvos preferenciais de 44 × 44 px;
- conteúdo funciona a 320 px e zoom de 400% quando aplicável.

## Acessibilidade

WCAG 2.2 AA é o mínimo. Contraste de texto 4.5:1, foco de 2 px com contraste
3:1, ordem de foco semântica, landmarks claros, estados não dependentes de cor,
movimento reduzido e mensagens anunciáveis. Todo ícone funcional recebe nome.

## Critério para novos componentes

Uma proposta deve responder: que significado novo representa, por que composição
não basta, qual ação suporta, como falha, como responde em mobile, como funciona
por teclado e o que substitui. Sem respostas claras, reutilizar o UI Kit.
