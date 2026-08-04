# Accessibility Guide

## Compromisso

Acessibilidade é parte da confiança Genesis. Informação, decisão e controle não
podem depender de uma capacidade sensorial, motora ou cognitiva específica.

Meta oficial: conformidade **WCAG 2.2 AA** em toda experiência principal.

## Contraste

- texto normal: mínimo 4.5:1;
- texto grande: mínimo 3:1;
- componentes, ícones essenciais e foco: mínimo 3:1;
- estados nunca dependem apenas de cor;
- placeholders não substituem labels.

## Teclado

Toda ação é alcançável por teclado. Ordem de foco segue leitura. Skip link leva
ao conteúdo principal. Menus usam padrões esperados; Escape fecha overlays sem
perder trabalho. Nenhuma keyboard trap.

## Foco

Indicador de foco com pelo menos 2 px, contraste mínimo 3:1 e offset visível.
Não remover outline sem substituição superior. Em ações destrutivas, o foco
inicial nunca cai automaticamente na confirmação.

## Semântica

Um único título principal por contexto, hierarquia de headings lógica, regiões
nomeadas e controles nativos sempre que possível. Ícones decorativos são
ignorados; ícones funcionais têm nome acessível.

## Leitores de tela

Mudanças importantes são anunciadas sem interromper leitura. Loading comunica
estado; sucesso e erro usam regiões apropriadas. Cards não escondem múltiplas
ações num único link ambíguo.

## Tamanho e gesto

Alvos mínimos de 24 × 24 px, preferencialmente 44 × 44 px em touch. Nenhuma ação
depende de gesto complexo, drag ou hover. Oferecer alternativa a reordenação por
arrasto.

## Movimento

Respeitar `prefers-reduced-motion`. Sem flashes acima do limite seguro. Parallax,
autoplay e animações contínuas não pertencem à experiência central.

## Cognição

- linguagem clara e consistente;
- uma ação principal por região;
- consequências explícitas;
- tempo ampliável ou inexistente para decisões;
- entradas preservadas após erro;
- revisão antes de ações de alto impacto;
- ajuda no contexto, não em documentação distante.

## Responsividade

### Desktop

Suporta zoom de 200% sem perda de conteúdo ou função. O canvas adapta densidade
e não prende largura mínima desnecessária.

### Tablet

Painéis laterais tornam-se overlays acessíveis, com foco contido e retorno ao
acionador. Touch e teclado permanecem equivalentes.

### Mobile

Sem rolagem horizontal no conteúdo principal a 320 px. A ação principal é
alcançável sem cobrir conteúdo. Navegação inferior respeita áreas seguras.

### Reflow

Conteúdo deve funcionar a 400% de zoom ou 320 CSS px, salvo visualizações cuja
natureza exija duas dimensões; nesses casos, o scroll fica contido.

## Formulários

Erros são descritos no topo e junto ao campo, com ligação programática. Instrução
vem antes da entrada. Campos obrigatórios são explicitados por texto. Não apagar
dados após validação.

## Conteúdo

Datas, estados, Health e Confidence usam texto compreensível. Evitar siglas sem
expansão. Idioma da página é declarado e mudanças de idioma são identificadas.

## Validação futura

Toda futura implementação deve incluir revisão por teclado, leitor de tela,
contraste, zoom, reflow, movimento reduzido e teste com pessoas com diferentes
necessidades. Conformidade automática é apoio, não prova final.
