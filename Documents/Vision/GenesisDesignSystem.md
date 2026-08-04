# Genesis Design System

**Versão:** 2.0 — Phase II Product Experience

**UI Kit oficial:** `UIKit.md`

## Nome

**Genesis Continuum** é o sistema visual do produto. Sua ideia central é uma
linha contínua entre intenção, decisão, ação e memória.

## Princípios visuais

- Quiet confidence: base calma, contraste preciso e ênfase rara.
- Context in layers: detalhe progressivo, sem paredes de informação.
- Meaning before metrics: texto e consequência antes de números.
- Control is visible: ações, estado e reversibilidade são legíveis.
- Motion with purpose: movimento explica mudança, nunca entretém.

## Cores

### Neutros

| Token | Valor | Uso |
|---|---:|---|
| Ink 950 | `#101318` | texto principal, fundos profundos |
| Ink 800 | `#252A33` | texto secundário forte |
| Slate 600 | `#5F6877` | metadados |
| Slate 400 | `#98A1AF` | elementos passivos |
| Mist 200 | `#DDE2E9` | bordas |
| Mist 100 | `#EEF1F5` | superfícies secundárias |
| Canvas | `#F7F8FA` | fundo principal |
| White | `#FFFFFF` | superfície elevada |

### Identidade e semântica

| Token | Valor | Uso |
|---|---:|---|
| Genesis Violet | `#6757D9` | ação e Focus |
| Violet Soft | `#EFEDFC` | contexto selecionado |
| Intelligence Cyan | `#16859B` | Intelligence e insights |
| Success Green | `#267A55` | conclusão confirmada |
| Attention Amber | `#A96713` | decisão necessária |
| Risk Red | `#B64242` | risco alto e ação destrutiva |

Cor semântica sempre acompanha ícone, rótulo ou texto.

## Tipografia

Família principal: **Inter**, com fallback para fontes de sistema. Para leitura
editorial longa, **Newsreader** pode ser usada com parcimônia em títulos de
manifesto e sínteses, nunca em controles.

Escala: 12, 14, 16, 20, 24, 32 e 44 px. Corpo padrão 16 px, altura de linha
1.5. Texto operacional compacto nunca menor que 13 px.

## Grid e espaço

Base de 4 px; escala principal 8, 12, 16, 24, 32, 48 e 64 px. Canvas desktop em
12 colunas, tablet em 8 e mobile em 4. Comprimento ideal de leitura entre 55 e
75 caracteres.

## Forma

Raios: 8 px em controles, 12 px em cards e 16 px em superfícies de foco. Sombras
são raras; hierarquia prefere cor de superfície, borda e espaço. Bordas de 1 px
com contraste suficiente.

## Ícones

Ícones lineares de 1.75 px, cantos levemente arredondados e metáforas universais.
Tamanhos 16, 20 e 24 px. Usar rótulo em ações não universais. Evitar robôs,
cérebro, estrelas mágicas e logos de fontes de inteligência como identidade.

## Motion

Duração 120–220 ms para feedback e 240–320 ms para mudança de contexto. Curva
suave, sem overshoot. Respeitar preferência por movimento reduzido.

## Responsive behavior

Design parte de prioridade, não de compressão. Colunas secundárias tornam-se
painéis sob demanda; cards empilham; tabelas auxiliares podem rolar dentro do
próprio contexto. A ação principal permanece alcançável.

## Tema escuro

Preserva relações de contraste, reduz superfícies puramente pretas e não usa
cores saturadas em grandes áreas. Tema nunca muda significado semântico.

## Assinatura visual

Uma linha contínua ou pulso discreto pode conectar etapas, Timeline e estados de
Intelligence. É o gesto próprio Genesis: progresso como continuidade, não como
velocidade.

## Shell oficial

- **Context Rail:** 256 px no desktop; Workspace, cinco destinos, Focus e
  Settings;
- **Context Header:** relação atual, título, síntese e ações do contexto;
- **Focus Canvas:** região principal com largura máxima de 1.440 px;
- **Insight Rail:** Recommendation, contexto ou Risk somente quando relevante;
- **mobile:** quatro destinos inferiores e More, sem reproduzir a Sidebar.

O header não apresenta versão, armazenamento ou disponibilidade técnica durante
o trabalho cotidiano. Essas informações pertencem a Settings e Health quando
alterarem uma decisão.

## Hierarquia de superfície

1. Canvas para continuidade do trabalho;
2. Focus Surface para a decisão dominante;
3. Content Surface para entidades e contexto;
4. Inset Surface para detalhes relacionados;
5. Overlay apenas para decisão curta e focada.

Bordas não delimitam automaticamente toda região. Espaço e alinhamento criam a
primeira hierarquia; cor de superfície e borda entram quando existe uma relação
semântica real.

## Estados semânticos

| Estado | Cor | Linguagem | Intensidade |
|---|---|---|---|
| Neutral | Slate | informação estável | baixa |
| Intelligence | Cyan | contexto e Insight | média |
| Focus | Violet | ação e seleção | alta e rara |
| Success | Green | resultado confirmado | proporcional |
| Attention | Amber | decisão necessária | contextual |
| Risk | Red | dano material possível | reservada |

Todo estado combina texto, forma e, quando útil, ícone. Cor isolada nunca
comunica significado.

## Densidade

Genesis oferece densidade confortável por padrão. Superfícies de decisão usam
mais espaço; comparação e pesquisa podem ser compactas. A pessoa pode aprofundar
detalhes sem que a visão inicial se torne uma parede de informação.

## Qualidade de componentes

Cada componente precisa definir conteúdo, prioridade, ação, estado vazio,
loading, erro, responsividade, teclado e foco. O UI Kit é fechado por padrão:
composição precede criação de novos componentes.
